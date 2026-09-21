#!/usr/bin/env bash
set -uo pipefail

readonly HAP_ADDRESS="${HAP_ADDRESS:-192.168.88.1}"
readonly CONNECT_BOX_ADDRESS="${CONNECT_BOX_ADDRESS:-192.168.2.1}"
readonly INTERNET_ADDRESSES=(1.1.1.1 8.8.8.8)
readonly ADGUARD_DNS=94.140.14.14
readonly ISP_DNS=62.179.104.196
readonly PUBLIC_DNS=1.1.1.1
readonly LOOKUP_NAME=google.com
readonly WAIT_SECONDS="${WAIT_SECONDS:-120}"
readonly RETRY_INTERVAL_SECONDS=10
readonly PROBE_NAMES=(hap connect_box internet hap_dns adguard_dns isp_dns public_dns)

declare -A probe_result=()
latest_verdict=""

log() {
    printf '[%(%T)T] %s\n' -1 "$*"
}

require_commands() {
    local command_name
    for command_name in "$@"; do
        command -v "$command_name" > /dev/null || {
            echo "Missing command: $command_name" >&2
            exit 1
        }
    done
}

responds_to_ping() {
    ping -c 2 -W 2 "$1" > /dev/null 2>&1
}

internet_reachable_by_address() {
    local address
    for address in "${INTERNET_ADDRESSES[@]}"; do
        responds_to_ping "$address" && return 0
    done
    curl --silent --output /dev/null --max-time 5 "https://${INTERNET_ADDRESSES[0]}"
}

resolves_via() {
    local answer
    answer=$(dig +short +time=2 +tries=1 A "$LOOKUP_NAME" "@$1" 2> /dev/null)
    grep -Eq '^[0-9]{1,3}(\.[0-9]{1,3}){3}$' <<< "$answer"
}

probe() {
    local name=$1
    shift
    if "$@"; then
        probe_result[$name]=ok
    else
        probe_result[$name]=fail
        return 1
    fi
}

probe_connectivity() {
    probe hap responds_to_ping "$HAP_ADDRESS" \
        && probe connect_box responds_to_ping "$CONNECT_BOX_ADDRESS" \
        && probe internet internet_reachable_by_address
}

probe_dns_resolvers() {
    probe hap_dns resolves_via "$HAP_ADDRESS"
    probe adguard_dns resolves_via "$ADGUARD_DNS"
    probe isp_dns resolves_via "$ISP_DNS"
    probe public_dns resolves_via "$PUBLIC_DNS"
}

run_probes() {
    probe_result=()
    probe_connectivity && probe_dns_resolvers
}

failed() {
    [[ ${probe_result[$1]:-} == fail ]]
}

diagnose_dns() {
    if ! failed hap_dns && ! failed adguard_dns; then
        echo HEALTHY
    elif failed hap_dns && ! failed adguard_dns; then
        echo HAP_DNS_FAILING
    elif ! failed isp_dns || ! failed public_dns; then
        echo ADGUARD_DNS_FAILING
    else
        echo ALL_DNS_FAILING
    fi
}

diagnose() {
    if failed hap; then
        echo HAP_UNREACHABLE
    elif failed connect_box; then
        echo CONNECT_BOX_UNREACHABLE
    elif failed internet; then
        echo INTERNET_UNREACHABLE
    else
        diagnose_dns
    fi
}

print_probe_summary() {
    local summary="" name
    for name in "${PROBE_NAMES[@]}"; do
        summary+="${name}=${probe_result[$name]:-skipped} "
    done
    log "${summary}=> ${latest_verdict}"
}

refresh_verdict() {
    run_probes
    latest_verdict=$(diagnose)
    print_probe_summary
}

wait_for_recovery() {
    local deadline=$((SECONDS + WAIT_SECONDS))
    while [[ $latest_verdict != HEALTHY ]] && ((SECONDS < deadline)); do
        sleep "$RETRY_INTERVAL_SECONDS"
        refresh_verdict
    done
}

print_recommendation() {
    echo "Recommended action:"
    case $1 in
        HAP_UNREACHABLE)
            echo "  The laptop cannot reach the MikroTik ($HAP_ADDRESS)."
            echo "  1. Check the laptop's Wi-Fi connection and the Ubiquiti AP (power, cable to the MikroTik)."
            echo "  2. If other devices are offline too, reboot the MikroTik."
            ;;
        CONNECT_BOX_UNREACHABLE)
            echo "  The MikroTik answers, but the Connect Box ($CONNECT_BOX_ADDRESS) does not."
            echo "  1. Check the cable between MikroTik ether1 and the Connect Box."
            echo "  2. Power-cycle the Connect Box."
            echo "  3. If still failing, reboot the MikroTik."
            ;;
        INTERNET_UNREACHABLE)
            echo "  The Connect Box answers, but nothing beyond it is reachable by IP address."
            echo "  From the laptop this cannot be told apart from a MikroTik routing problem."
            echo "  1. Check your ISP's status page."
            echo "  2. Power-cycle the Connect Box."
            echo "  3. If still failing, check the MikroTik: /ip dhcp-client print and /ip route print."
            ;;
        HAP_DNS_FAILING)
            echo "  Resolvers answer directly, but the MikroTik's DNS does not."
            echo "  1. Run /ip dns cache flush on the MikroTik."
            echo "  2. If still failing, reboot the MikroTik."
            ;;
        ADGUARD_DNS_FAILING)
            echo "  AdGuard DNS ($ADGUARD_DNS) does not answer, other resolvers do. No reboot needed."
            echo "  1. Wait, or add a fallback resolver on the MikroTik:"
            echo "     /ip dns set servers=94.140.14.14,94.140.15.15,$PUBLIC_DNS"
            ;;
        ALL_DNS_FAILING)
            echo "  The internet is reachable by IP, but no resolver answers."
            echo "  The MikroTik may be serving cached answers, hiding the outage."
            echo "  1. Check your ISP's status page."
            echo "  2. Power-cycle the Connect Box."
            ;;
    esac
    echo "  Reboot or power-cycle only. Never run /system reset-configuration."
}

print_route_evidence() {
    [[ $1 == INTERNET_UNREACHABLE ]] || return 0
    echo
    echo "Route trace (shows where packets stop; hop 1 = MikroTik, hop 2 = Connect Box):"
    mtr --report --report-cycles 3 --no-dns --max-ttl 6 "${INTERNET_ADDRESSES[0]}" 2>&1
}

print_final_report() {
    local first_verdict=$1
    echo
    if [[ $latest_verdict != HEALTHY ]]; then
        log "Still failing after ${WAIT_SECONDS}s: ${latest_verdict}"
        print_recommendation "$latest_verdict"
        print_route_evidence "$latest_verdict"
    elif [[ $first_verdict != HEALTHY ]]; then
        log "Recovered by itself (initial problem: ${first_verdict}). No action needed."
    else
        log "No problem detected right now. Run again during the next outage."
    fi
}

main() {
    require_commands ping dig mtr curl
    refresh_verdict
    local first_verdict=$latest_verdict
    wait_for_recovery
    print_final_report "$first_verdict"
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
    main
fi