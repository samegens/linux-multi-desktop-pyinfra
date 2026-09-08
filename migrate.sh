#!/bin/bash
# Migrates the paths listed in migration.md from this machine to dell_laptop. This machine
# stays authoritative until cutover - safe to run repeatedly (e.g. to test on dell_laptop while
# still daily-driving this one), only the last run before cutover needs --final.
#
# Also warns (never blocks) about any repo under ~/git with untracked/uncommitted/unpushed
# changes - those aren't synced by this script, so they'd otherwise be silently left behind.
#
# Usage:
#   ./migrate.sh            Interim sync - no --delete, warns (doesn't block) if
#                            Betterbird/Firefox are open.
#   ./migrate.sh --final    Exact-mirror pass (rsync --delete) - refuses to run unless
#                            Betterbird/Firefox are closed on BOTH machines, asks for
#                            confirmation, and verifies the result afterwards.
#   ./migrate.sh --only NAME   Only sync one item: betterbird, firefox, darktable, fotos,
#                              fotos-uitzoeken, pictures, prusaslicer-printer,
#                              prusaslicer-filament, prusaslicer-print,
#                              prusaslicer-physical-printer. For testing the script itself.
#
# Not reusing pyinfra's vault-based SSH password: this is a manual, occasionally-run personal
# script, not part of the deploy. Requires passwordless (key-based) SSH to dell_laptop instead -
# the script makes many SSH/rsync calls per run, and password auth would mean typing it in
# repeatedly; check_passwordless_ssh() below fails fast with setup instructions if it's missing,
# rather than silently blocking on a hidden password prompt partway through.

set -euo pipefail

DEST_HOST=dwerglijster     # dell_laptop - see pyinfra/inventory.py if this ever changes
DEST_USER=sebastiaan
SRC_USER=sebastiaan
SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o BatchMode=yes)

FINAL=false
ONLY=""
while [ $# -gt 0 ]; do
    case "$1" in
        --final) FINAL=true ;;
        --only) ONLY="$2"; shift ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
    shift
done

ALL_ITEMS=(betterbird firefox darktable fotos fotos-uitzoeken pictures prusaslicer-printer
    prusaslicer-filament prusaslicer-print prusaslicer-physical-printer)

ssh_dest() { ssh "${SSH_OPTS[@]}" "$DEST_USER@$DEST_HOST" "$@"; }

want() { [ -z "$ONLY" ] || [ "$ONLY" = "$1" ]; }

check_passwordless_ssh() {
    echo "==> Checking passwordless SSH to dell_laptop..."
    if ! ssh_dest true 2>/dev/null; then
        echo "ERROR: passwordless SSH to dell_laptop isn't setup." >&2
        exit 1
    fi
}

# True if version $1 sorts before version $2 (i.e. $1 is older).
version_lt() {
    [ "$1" != "$2" ] && [ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | head -n1)" = "$1" ]
}

# Target must be same-or-newer than source for both apps - official guidance for both
# Firefox and Thunderbird/Betterbird profiles is to never open a profile in an OLDER version
# than last wrote it. Coarse major.minor.patch comparison only (ignores e.g. Betterbird's
# "esr-bbNN" build suffix) - good enough to catch an actual downgrade.
check_app_versions() {
    echo "==> Checking Betterbird/Firefox versions (dell_laptop must be >= this machine)..."
    local bb_src bb_dst ff_src ff_dst
    bb_src=$(flatpak run eu.betterbird.Betterbird --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1 || true)
    bb_dst=$(ssh_dest "flatpak run eu.betterbird.Betterbird --version 2>/dev/null" | grep -oP '\d+\.\d+\.\d+' | head -1 || true)
    ff_src=$(rpm -q --qf '%{VERSION}' firefox 2>/dev/null || true)
    ff_dst=$(ssh_dest "dpkg-query -W -f='\${Version}' firefox 2>/dev/null" | grep -oP '^\d+\.\d+' || true)

    echo "    Betterbird: source=${bb_src:-?} dest=${bb_dst:-?} | Firefox: source=${ff_src:-?} dest=${ff_dst:-?}"

    if [ -n "$bb_src" ] && [ -n "$bb_dst" ] && version_lt "$bb_dst" "$bb_src"; then
        echo "ERROR: target's Betterbird ($bb_dst) is older than this machine's ($bb_src) - update it first." >&2
        exit 1
    fi
    if [ -n "$ff_src" ] && [ -n "$ff_dst" ] && version_lt "$ff_dst" "$ff_src"; then
        echo "ERROR: target's Firefox ($ff_dst) is older than this machine's ($ff_src) - update it first." >&2
        exit 1
    fi
}

# Warn-only (never blocks): dirty/unpushed repos aren't part of what this script syncs, but
# leaving them behind on this machine before a --final cutover is an easy way to lose work.
check_git_repos_clean() {
    echo "==> Checking ~/git repos for untracked/uncommitted/unpushed changes..."
    local dir found=false
    for dir in "/home/$SRC_USER/git/"*/; do
        [ -d "$dir/.git" ] || continue
        local status unpushed
        status=$(git -C "$dir" status --porcelain)
        unpushed=$(git -C "$dir" log --branches --not --remotes --oneline 2>/dev/null)
        if [ -n "$status" ] || [ -n "$unpushed" ]; then
            found=true
            echo "WARNING: $dir has uncommitted/untracked or unpushed changes:" >&2
            [ -n "$status" ] && echo "$status" | sed 's/^/    /' >&2
            [ -n "$unpushed" ] && echo "$unpushed" | sed 's/^/    unpushed: /' >&2
        fi
    done
    $found || echo "    All clean."
}

apps_running_locally() { pgrep -f -i betterbird >/dev/null || pgrep -f firefox >/dev/null; }
apps_running_remotely() { ssh_dest "pgrep -f -i betterbird || pgrep -f firefox" >/dev/null; }

check_apps_closed() {
    echo "==> Checking Betterbird/Firefox are closed on both machines (required for --final)..."
    if apps_running_locally; then
        echo "ERROR: Betterbird or Firefox is still running on this machine - close it first." >&2
        exit 1
    fi
    if apps_running_remotely; then
        echo "ERROR: Betterbird or Firefox is still running on dell_laptop - close it first." >&2
        exit 1
    fi
}

warn_if_apps_running() {
    if apps_running_locally; then
        echo "WARNING: Betterbird/Firefox are running here - this interim sync may copy an" >&2
        echo "         inconsistent snapshot (uncommitted WAL). Fine for testing, not for --final." >&2
    fi
}

# Checked once for the combined total, not per item - most items share the same destination
# filesystem, so per-item checks could each individually pass while the combined total doesn't
# actually fit.
check_disk_space() {
    local -n paths_ref=$1
    local needed_kb=0 avail_kb
    for path in "${paths_ref[@]}"; do
        [ -d "$path" ] || continue
        needed_kb=$((needed_kb + $(du -sk "$path" | cut -f1)))
    done
    avail_kb=$(ssh_dest "df -Pk \"/home/$DEST_USER\"" | tail -1 | awk '{print $4}')
    echo "==> Disk space: need ~$((needed_kb / 1024))M, dell_laptop has $((avail_kb / 1024))M free."
    # 20% headroom
    if [ "$avail_kb" -lt "$((needed_kb * 12 / 10))" ]; then
        echo "ERROR: not enough free space on dell_laptop." >&2
        exit 1
    fi
}

# The real Betterbird profile is whichever one actually has a Mail directory - folder names are
# random-salted per install (see modules/betterbird.py's docstring), and an empty decoy profile
# can exist alongside the real one (confirmed live: exactly this on this machine).
discover_betterbird_profile() {
    local base="/home/$SRC_USER/.var/app/eu.betterbird.Betterbird/.thunderbird"
    find "$base" -mindepth 1 -maxdepth 1 -type d -exec test -d '{}/Mail' \; -print 2>/dev/null | head -1
}

# The profile that actually launches is named by profiles.ini's [InstallXXXX] Default= line -
# not any [ProfileN] Default=1 marker, which can point at an unrelated/older profile (confirmed
# live: this machine's profiles.ini has both, pointing at different profiles). Both Firefox's and
# Betterbird's profiles.ini share this same format, so this works for either.
mozilla_default_profile_name() {
    awk '/^\[Install/{f=1} f && /^Default=/{print; exit}' "$1" | cut -d= -f2
}

sync_dir() {
    local name="$1" src="$2" dest="$3"
    if [ ! -d "$src" ]; then
        echo "==> Skipping $name - $src does not exist locally."
        return
    fi
    echo "==> Syncing $name ($src -> dell_laptop:$dest)"
    ssh_dest "mkdir -p \"$dest\""
    local delete_opt=()
    $FINAL && delete_opt=(--delete)
    rsync -az --info=progress2 "${delete_opt[@]}" \
        --exclude=lock --exclude=.parentlock \
        -e "ssh ${SSH_OPTS[*]}" \
        "$src"/ "$DEST_USER@$DEST_HOST:$dest"/
}

verify_dir() {
    local name="$1" src="$2" dest="$3"
    [ -d "$src" ] || return
    local diff_out
    diff_out=$(rsync -aiun --delete --exclude=lock --exclude=.parentlock \
        -e "ssh ${SSH_OPTS[*]}" \
        "$src"/ "$DEST_USER@$DEST_HOST:$dest"/ 2>&1)
    if [ -n "$diff_out" ]; then
        echo "WARNING: $name still shows differences after sync:"
        echo "$diff_out"
    else
        echo "    $name: verified clean."
    fi
}

confirm_final() {
    echo
    echo "This is a --final mirror pass: it will DELETE anything on dell_laptop under the"
    echo "synced paths that no longer exists here."
    read -rp "Type 'yes' to continue: " reply
    [ "$reply" = "yes" ] || { echo "Aborted."; exit 1; }
}

main() {
    check_passwordless_ssh
    check_app_versions
    check_git_repos_clean

    if $FINAL; then
        check_apps_closed
        confirm_final
    else
        warn_if_apps_running
    fi

    local bb_profile bb_name bb_dest_profile ff_profile ff_dest_profile
    bb_profile=$(discover_betterbird_profile)
    bb_dest_profile=$(ssh_dest "cat /home/$DEST_USER/.var/app/eu.betterbird.Betterbird/.thunderbird/profiles.ini 2>/dev/null" | mozilla_default_profile_name /dev/stdin)
    ff_profile=$(mozilla_default_profile_name "/home/$SRC_USER/.config/mozilla/firefox/profiles.ini")
    ff_dest_profile=$(ssh_dest "cat /home/$DEST_USER/.config/mozilla/firefox/profiles.ini" | mozilla_default_profile_name /dev/stdin)

    want betterbird && [ -z "$bb_profile" ] && { echo "ERROR: no real Betterbird profile found locally (no Mail dir)." >&2; exit 1; }
    want betterbird && [ -z "$bb_dest_profile" ] && { echo "ERROR: could not discover dell_laptop's Betterbird default profile - launch Betterbird there once first." >&2; exit 1; }
    want firefox && [ -z "$ff_profile" ] && { echo "ERROR: could not discover local Firefox default-release profile." >&2; exit 1; }
    want firefox && [ -z "$ff_dest_profile" ] && { echo "ERROR: could not discover dell_laptop's Firefox default-release profile - launch Firefox there once first." >&2; exit 1; }

    bb_name=$(basename "${bb_profile:-unknown}")

    declare -A SRC=(
        [betterbird]="/home/$SRC_USER/.var/app/eu.betterbird.Betterbird/.thunderbird/$bb_name"
        [firefox]="/home/$SRC_USER/.config/mozilla/firefox/$ff_profile"
        [darktable]="/home/$SRC_USER/.var/app/org.darktable.Darktable/config/darktable"
        [fotos]="/home/$SRC_USER/fotos"
        [fotos-uitzoeken]="/home/$SRC_USER/fotos-uitzoeken"
        [pictures]="/home/$SRC_USER/Pictures"
        [prusaslicer-printer]="/home/$SRC_USER/.var/app/com.prusa3d.PrusaSlicer/config/PrusaSlicer/printer"
        [prusaslicer-filament]="/home/$SRC_USER/.var/app/com.prusa3d.PrusaSlicer/config/PrusaSlicer/filament"
        [prusaslicer-print]="/home/$SRC_USER/.var/app/com.prusa3d.PrusaSlicer/config/PrusaSlicer/print"
        [prusaslicer-physical-printer]="/home/$SRC_USER/.var/app/com.prusa3d.PrusaSlicer/config/PrusaSlicer/physical_printer"
    )
    declare -A DEST=(
        [betterbird]="/home/$DEST_USER/.var/app/eu.betterbird.Betterbird/.thunderbird/$bb_dest_profile"
        [firefox]="/home/$DEST_USER/.config/mozilla/firefox/$ff_dest_profile"
        [darktable]="/home/$DEST_USER/.var/app/org.darktable.Darktable/config/darktable"
        [fotos]="/home/$DEST_USER/fotos"
        [fotos-uitzoeken]="/home/$DEST_USER/fotos-uitzoeken"
        [pictures]="/home/$DEST_USER/Pictures"
        [prusaslicer-printer]="/home/$DEST_USER/.var/app/com.prusa3d.PrusaSlicer/config/PrusaSlicer/printer"
        [prusaslicer-filament]="/home/$DEST_USER/.var/app/com.prusa3d.PrusaSlicer/config/PrusaSlicer/filament"
        [prusaslicer-print]="/home/$DEST_USER/.var/app/com.prusa3d.PrusaSlicer/config/PrusaSlicer/print"
        [prusaslicer-physical-printer]="/home/$DEST_USER/.var/app/com.prusa3d.PrusaSlicer/config/PrusaSlicer/physical_printer"
    )

    local run_items=()
    for name in "${ALL_ITEMS[@]}"; do
        want "$name" && run_items+=("$name")
    done

    local src_paths=()
    for name in "${run_items[@]}"; do
        src_paths+=("${SRC[$name]}")
    done
    check_disk_space src_paths

    for name in "${run_items[@]}"; do
        sync_dir "$name" "${SRC[$name]}" "${DEST[$name]}"
    done

    if $FINAL; then
        echo "==> Verifying final sync (should show no differences)..."
        for name in "${run_items[@]}"; do
            verify_dir "$name" "${SRC[$name]}" "${DEST[$name]}"
        done
    fi

    echo "==> Done."
}

main
