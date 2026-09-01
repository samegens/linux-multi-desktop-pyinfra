# System tools

control "git is installed and working" do
  tag :tools
  describe file('/usr/bin/git') do
    it { should exist }
    it { should be_executable }
  end
  describe command('git --version') do
    its('stdout') { should match /^git version/ }
    its('exit_status') { should eq 0 }
  end
end

control "docker is installed and working" do
  tag :tools
  describe file('/usr/bin/docker') do
    it { should exist }
    it { should be_executable }
  end
  describe command('docker --version') do
    its('stdout') { should match /^Docker version/ }
    its('exit_status') { should eq 0 }
  end
end

control "docker service is enabled and running" do
  tag :tools
  describe service('docker') do
    it { should be_enabled }
    it { should be_running }
  end
end

control "user is in the docker group" do
  tag :tools
  describe user(input('username')) do
    its('groups') { should include 'docker' }
  end
end

# TODO: uncomment once a terraform module is built (deferred, see README backlog)
# control "terraform is installed and working" do
#   describe file('/usr/local/bin/terraform') do
#     it { should exist }
#     it { should be_executable }
#   end
# end

# TODO: uncomment once a packer module is built (deferred, see README backlog)
# control "packer is installed and working" do
#   describe file('/usr/bin/packer') do
#     it { should exist }
#     it { should be_executable }
#   end
# end

# TODO: uncomment once a vagrant module is built (deferred, see README backlog)
# control "vagrant is installed and working" do
#   describe file('/usr/bin/vagrant') do
#     it { should exist }
#     it { should be_executable }
#   end
# end

control "cinc-auditor is installed and working" do
  tag :tools
  describe file('/opt/cinc-auditor/bin/cinc-auditor') do
    it { should exist }
    it { should be_executable }
  end
  describe command('cinc-auditor --version') do
    its('stdout') { should match /^7\.1\.7/ }
    its('exit_status') { should eq 0 }
  end
end

# CLI tools

control "starship is installed and working" do
  tag :tools
  describe file('/usr/local/bin/starship') do
    it { should exist }
    it { should be_executable }
  end
  describe command('starship --version') do
    its('stdout') { should match /^starship/ }
    its('exit_status') { should eq 0 }
  end
end

control "fastfetch is installed and working" do
  tag :tools
  describe file('/usr/bin/fastfetch') do
    it { should exist }
    it { should be_executable }
  end
  describe command('fastfetch --version') do
    its('stdout') { should match /^fastfetch/ }
    its('exit_status') { should eq 0 }
  end
end

# TODO: uncomment once an azure-cli module is built (deferred, see README backlog)
# control "azure cli is installed and working" do
#   describe file('/usr/bin/az') do
#     it { should exist }
#     it { should be_executable }
#   end
# end

control "claude is installed and working" do
  tag :tools
  describe file("/home/#{input('username')}/.local/bin/claude") do
    it { should exist }
    it { should be_executable }
  end
  describe command("/home/#{input('username')}/.local/bin/claude --version") do
    its('stdout') { should match /^[0-9]/ }
    its('exit_status') { should eq 0 }
  end
end

# Security scanning tools

control "gitleaks is installed and working" do
  tag :tools
  describe file('/usr/local/bin/gitleaks') do
    it { should exist }
    it { should be_executable }
  end
  describe command('gitleaks version') do
    its('stdout') { should match /[0-9]/ }
    its('exit_status') { should eq 0 }
  end
end

control "trufflehog is installed and working" do
  tag :tools
  describe file('/usr/local/bin/trufflehog') do
    it { should exist }
    it { should be_executable }
  end
  describe command('trufflehog --version') do
    its('exit_status') { should eq 0 }
  end
end

control "detect-secrets is installed in the pyinfra-latest venv" do
  tag :tools
  username = input('username')
  describe command("/home/#{username}/python3-venv/pyinfra-latest/bin/detect-secrets-hook --version") do
    its('exit_status') { should eq 0 }
  end
end

# Kubernetes tools

control "k3s is installed and working" do
  tag :tools
  describe file('/usr/local/bin/k3s') do
    it { should exist }
    it { should be_executable }
  end
  describe command('k3s --version') do
    its('stdout') { should match /^k3s version/ }
    its('exit_status') { should eq 0 }
  end
end

control "k3s service is enabled and running" do
  tag :tools
  describe service('k3s') do
    it { should be_enabled }
    it { should be_running }
  end
end

control "k3s kubeconfig is world-readable" do
  tag :tools
  describe file('/etc/rancher/k3s/k3s.yaml') do
    it { should exist }
    its('mode') { should cmp '0644' }
  end
end

control "k9s is installed and working" do
  tag :tools
  describe file('/usr/local/bin/k9s') do
    it { should exist }
    it { should be_executable }
    it { should be_symlink }
    its('link_path') { should match %r{^/opt/k9s-} }
  end
  describe command('k9s version --short') do
    its('exit_status') { should eq 0 }
  end
end

control "helm is installed and working" do
  tag :tools
  describe file('/usr/local/bin/helm') do
    it { should exist }
    it { should be_executable }
    it { should be_symlink }
    its('link_path') { should match %r{^/opt/helm-} }
  end
  describe command('helm version --short') do
    its('exit_status') { should eq 0 }
  end
end

# Development tools

control "vscode is installed and working" do
  tag :tools
  describe file('/usr/bin/code') do
    it { should exist }
    it { should be_executable }
  end
end

control "vscode config files are in place" do
  tag :tools
  username = input('username')
  describe file("/home/#{username}/.config/Code/User/settings.json") do
    it { should exist }
  end
  describe file("/home/#{username}/.config/Code/User/keybindings.json") do
    it { should exist }
  end
  describe file("/home/#{username}/.config/Code/User/snippets/csharp.json") do
    it { should exist }
  end
end

control "vscode extensions are installed" do
  tag :tools
  describe command("code --list-extensions") do
    its('stdout') { should match /ms-python\.python/ }
    its('exit_status') { should eq 0 }
  end
end

control "vscode is pinned to the panel" do
  tag :tools
  describe panel_pin('code.desktop', input('username')) do
    it { should be_pinned }
  end
end

control "dotnet is installed and working" do
  tag :tools
  describe file('/usr/local/bin/dotnet') do
    it { should exist }
    it { should be_executable }
    it { should be_symlink }
    its('link_path') { should match %r{^/opt/dotnet-} }
  end
  describe command('dotnet --version') do
    its('exit_status') { should eq 0 }
  end
end

# Checks the actual toolchain works - dotnet --version alone only proves the binary runs, not
# that it can resolve its shared frameworks/SDK packs and actually compile a project into a real
# apphost executable (the real risk with a non-standard, non-distro-packaged install). Builds
# and then runs the produced executable directly, not `dotnet run` - proves the apphost itself
# (not just `dotnet` acting as a JIT/run wrapper) is correctly wired to the installed runtime.
# One control per runtime channel modules/dotnet.py's DOTNET_EXTRA_RUNTIME_CHANNELS installs
# side-by-side (7.0/8.0/9.0 EOL, plus 10.0 - the pinned SDK's own bundled runtime), so an old
# csproj's TargetFramework is proven to actually run, not just that dotnet-install.sh reported
# success installing it. `dotnet new console -f <tfm>` can't scaffold this directly - confirmed
# live that SDK 10's console template only accepts its own current TFM as a valid -f value
# ("net7.0 is not a valid value for -f"); sed the .csproj afterward instead, which `dotnet build`
# honors for any TargetFramework as long as the runtime/targeting pack is present.
["7.0", "8.0", "9.0", "10.0"].each do |framework|
  control "dotnet can build and run a net#{framework} executable" do
    tag :tools
    workdir = "/tmp/dotnet-net#{framework}-inspec-test"
    project = "Net#{framework.sub('.', '')}InspecTest"

    describe command(
      "rm -rf #{workdir} && mkdir -p #{workdir} && cd #{workdir} && " \
      "dotnet new console --no-restore -o . -n #{project} && " \
      "sed -i 's#<TargetFramework>.*</TargetFramework>#<TargetFramework>net#{framework}</TargetFramework>#' " \
      "#{project}.csproj && " \
      "dotnet build -c Release -o out && ./out/#{project}; " \
      "status=$?; rm -rf #{workdir}; exit $status"
    ) do
      its('exit_status') { should eq 0 }
      its('stdout') { should match /Hello, World!/ }
    end
  end
end

control "powershell is installed and working" do
  tag :tools
  describe file('/usr/local/bin/pwsh') do
    it { should exist }
    it { should be_executable }
    it { should be_symlink }
    its('link_path') { should match %r{^/opt/powershell-} }
  end
  describe command('pwsh --version') do
    its('stdout') { should match /^PowerShell/ }
    its('exit_status') { should eq 0 }
  end
end

control "powershell can run a hello world script" do
  tag :tools
  describe command("pwsh -NoProfile -Command \"Write-Output 'Hello, World!'\"") do
    its('exit_status') { should eq 0 }
    its('stdout') { should match /Hello, World!/ }
  end
end

control "go is installed and working" do
  tag :tools
  describe file('/usr/local/go/bin/go') do
    it { should exist }
    it { should be_executable }
  end
  describe command('/usr/local/go/bin/go version') do
    its('stdout') { should match /^go version/ }
    its('exit_status') { should eq 0 }
  end
end

control "rustc is installed and working" do
  tag :tools
  describe file("/home/#{input('username')}/.cargo/bin/rustc") do
    it { should exist }
    it { should be_executable }
  end
  describe command("/home/#{input('username')}/.cargo/bin/rustc --version") do
    its('stdout') { should match /^rustc/ }
    its('exit_status') { should eq 0 }
  end
end

control "cargo is installed and working" do
  tag :tools
  describe file("/home/#{input('username')}/.cargo/bin/cargo") do
    it { should exist }
    it { should be_executable }
  end
end

control "ts is installed" do
  tag :tools
  describe command("which ts") do
    its('stdout') { should match /^.*\/ts$/ }
    its('exit_status') { should eq 0 }
  end
end

# TODO: uncomment once a p4merge module is built (deferred, see README backlog)
# control "p4merge is installed and working" do
#   describe file('/usr/local/bin/p4merge') do
#     it { should exist }
#     it { should be_executable }
#   end
# end

# Workrave

control "workrave is installed and working" do
  tag :tools
  describe file('/usr/bin/workrave') do
    it { should exist }
    it { should be_executable }
  end
end

control "workrave autostart entry is in place" do
  tag :tools
  username = input('username')
  describe file("/home/#{username}/.config/autostart/workrave.desktop") do
    it { should exist }
    its('content') { should match /Exec=workrave/ }
  end
end

# Obsidian

control "obsidian flatpak is installed" do
  tag :tools
  describe command('flatpak info md.obsidian.Obsidian') do
    its('exit_status') { should eq 0 }
  end
end

control "obsidian config is in place" do
  tag :tools
  username = input('username')
  describe file("/home/#{username}/.var/app/md.obsidian.Obsidian/config/obsidian/obsidian.json") do
    it { should exist }
    its('content') { should match /Dropbox\/projects\/Obsidian\/notes/ }
  end
end

control "obsidian is pinned to the panel" do
  tag :tools
  describe panel_pin('md.obsidian.Obsidian.desktop', input('username')) do
    it { should be_pinned }
  end
end

# KeePassXC

control "keepassxc is installed and working" do
  tag :tools
  # keepassxc itself is a GUI app that aborts (SIGABRT) without a display when run headless -
  # keepassxc-cli is its companion CLI tool and safe to invoke the same way balenaEtcher's
  # control checks file presence instead of running the GUI binary.
  describe command('keepassxc-cli --version') do
    its('stdout') { should match /^\d+\.\d+\.\d+/ }
    its('exit_status') { should eq 0 }
  end
end

control "keepassxc is pinned to the panel" do
  tag :tools
  describe panel_pin('org.keepassxc.KeePassXC.desktop', input('username')) do
    it { should be_pinned }
  end
end

# Betterbird

control "betterbird flatpak is installed" do
  tag :tools
  describe command('flatpak info eu.betterbird.Betterbird') do
    its('exit_status') { should eq 0 }
  end
end

control "betterbird is pinned to the panel" do
  tag :tools
  describe panel_pin('eu.betterbird.Betterbird.desktop', input('username')) do
    it { should be_pinned }
  end
end

control "betterbird forces ISO 8601 date formatting" do
  tag :tools
  username = input('username')
  thunderbird_dir = "/home/#{username}/.var/app/eu.betterbird.Betterbird/.thunderbird"
  profile_dirs = command(
    "find #{thunderbird_dir} -mindepth 1 -maxdepth 1 -type d " \
    "-exec test -e '{}/prefs.js' \\; -print 2>/dev/null"
  ).stdout.split("\n")

  only_if("a Betterbird profile exists") { !profile_dirs.empty? }

  profile_dirs.each do |profile_dir|
    describe file("#{profile_dir}/user.js") do
      it { should exist }
      its('content') { should match /intl\.date_time\.pattern_override\.date_short.*yyyy-MM-dd/ }
      its('content') { should match /intl\.date_time\.pattern_override\.date_medium.*yyyy-MM-dd/ }
      its('content') { should match /intl\.date_time\.pattern_override\.date_long.*yyyy-MM-dd/ }
      its('content') { should match /intl\.date_time\.pattern_override\.date_full.*yyyy-MM-dd/ }
    end
  end
end

# darktable

control "darktable flatpak is installed" do
  tag :tools
  describe command('flatpak info org.darktable.Darktable') do
    its('exit_status') { should eq 0 }
  end
end

control "darktable settings are pinned" do
  tag :tools
  username = input('username')
  describe file("/home/#{username}/.var/app/org.darktable.Darktable/config/darktable/darktablerc") do
    it { should exist }
    its('content') { should match %r{^plugins/darkroom/workflow=scene-referred \(filmic\)$} }
    its('content') { should match %r{^plugins/darkroom/histogram/mode=histogram$} }
    its('content') { should match %r{^plugins/imageio/format/jpeg/quality=85$} }
    its('content') { should match /^session\/use_filename=TRUE$/ }
  end
end

# balenaEtcher

control "balenaEtcher is installed" do
  tag :tools
  describe file('/usr/bin/balena-etcher') do
    it { should exist }
    it { should be_executable }
  end
end

# Dropbox

control "dropbox is installed" do
  tag :tools
  describe file('/usr/bin/dropbox') do
    it { should exist }
    it { should be_executable }
  end
end

control "python3-gpg is importable (needed by dropbox to verify binary signatures)" do
  tag :tools
  describe command('python3 -c "import gpg"') do
    its('exit_status') { should eq 0 }
  end
end

# Firefox

control "firefox has non-free codec support (Fedora only - Mint ships codecs by default)" do
  tag :tools
  only_if('this is a dnf-based host') { !os.debian? }

  describe command('rpm -q libavcodec-freeworld') do
    its('exit_status') { should eq 0 }
  end
  describe command('rpm -q ffmpeg') do
    its('exit_status') { should eq 0 }
  end
  describe command('rpm -q ffmpeg-free') do
    its('exit_status') { should_not eq 0 }
  end
end

# bin/activate existing proves the venv itself
# was created, and `pip show` on one representative package per venv proves installs landed in
# that venv (not the system Python).
{
  "pyinfra-latest" => "pyinfra",
  "ansible-latest" => "ansible",
  "blauwe-lucht-rpa" => "rpa",
  "ansible-homedisplay" => "ansible",
}.each do |venv_name, sample_package|
  control "#{venv_name} venv is set up and working" do
    tag :tools
    username = input('username')
    venv = "/home/#{username}/python3-venv/#{venv_name}"
    describe file("#{venv}/bin/activate") do
      it { should exist }
    end
    describe command("#{venv}/bin/pip show #{sample_package}") do
      its('exit_status') { should eq 0 }
    end
  end
end

# TODO: uncomment once modules/nodejs.py is built
# control "Node.js version is >= 20" do
#   describe command('node --version') do
#     its('exit_status') { should eq 0 }
#     its('stdout') { should match /^v(2[0-9]|[3-9][0-9]|\d{3,})/ }
#   end
# end
#
# control "npm version is >= 10" do
#   describe command('npm --version') do
#     its('exit_status') { should eq 0 }
#     its('stdout') { should match /^([1-9][0-9]|\d{3,})/ }
#   end
# end
