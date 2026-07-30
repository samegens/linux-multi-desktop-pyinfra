# System tools

control "git is installed and working" do
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
  describe service('docker') do
    it { should be_enabled }
    it { should be_running }
  end
end

control "user is in the docker group" do
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
  describe file('/usr/local/bin/starship') do
    it { should exist }
    it { should be_executable }
  end
  describe command('starship --version') do
    its('stdout') { should match /^starship/ }
    its('exit_status') { should eq 0 }
  end
end

# TODO: uncomment once a fastfetch module is built (deferred, see README backlog)
# control "fastfetch is installed and working" do
#   describe file('/usr/bin/fastfetch') do
#     it { should exist }
#     it { should be_executable }
#   end
# end

# TODO: uncomment once an azure-cli module is built (deferred, see README backlog)
# control "azure cli is installed and working" do
#   describe file('/usr/bin/az') do
#     it { should exist }
#     it { should be_executable }
#   end
# end

# TODO: uncomment once a claude-code module is built (deferred, see README backlog)
# control "claude is installed and working" do
#   describe file("/home/#{input('username')}/.local/bin/claude") do
#     it { should exist }
#     it { should be_executable }
#   end
# end

# Security scanning tools

# TODO: uncomment once gitleaks/trufflehog install modules are built (deferred)
# control "gitleaks is installed and working" do
#   describe file('/usr/local/bin/gitleaks') do
#     it { should exist }
#     it { should be_executable }
#   end
# end

# TODO: uncomment once gitleaks/trufflehog install modules are built (deferred)
# control "trufflehog is installed and working" do
#   describe file('/usr/local/bin/trufflehog') do
#     it { should exist }
#     it { should be_executable }
#   end
# end

# Kubernetes tools

control "k3s is installed and working" do
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
  describe service('k3s') do
    it { should be_enabled }
    it { should be_running }
  end
end

control "k3s kubeconfig is world-readable" do
  describe file('/etc/rancher/k3s/k3s.yaml') do
    it { should exist }
    its('mode') { should cmp '0644' }
  end
end

control "k9s is installed and working" do
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
  describe file('/usr/bin/code') do
    it { should exist }
    it { should be_executable }
  end
end

control "vscode config files are in place" do
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
  describe command("code --list-extensions") do
    its('stdout') { should match /ms-python\.python/ }
    its('exit_status') { should eq 0 }
  end
end

# TODO: uncomment once a dedicated PowerShell/.NET SDK module is built - see modules/vscode.py's
# docstring for why it's not part of that module (Fedora/Microsoft dotnet-sdk-8.0 name collision).
# control "dotnet is installed and working" do
#   describe file('/usr/bin/dotnet') do
#     it { should exist }
#     it { should be_executable }
#   end
#   describe command('dotnet --version') do
#     its('exit_status') { should eq 0 }
#   end
# end
#
# control "powershell is installed and working" do
#   describe file('/usr/bin/pwsh') do
#     it { should exist }
#     it { should be_executable }
#   end
# end

control "go is installed and working" do
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
  describe file("/home/#{input('username')}/.cargo/bin/cargo") do
    it { should exist }
    it { should be_executable }
  end
end

# TODO: uncomment once a p4merge module is built (deferred, see README backlog)
# control "p4merge is installed and working" do
#   describe file('/usr/local/bin/p4merge') do
#     it { should exist }
#     it { should be_executable }
#   end
# end

# Double Commander

control "doublecmd is installed and working" do
  describe file('/usr/local/bin/doublecmd') do
    it { should exist }
    it { should be_executable }
    it { should be_symlink }
    its('link_path') { should match %r{^/opt/doublecmd-} }
  end
end

control "doublecmd config files are in place" do
  username = input('username')
  config_dir = "/home/#{username}/.config/doublecmd"
  ["doublecmd.xml", "multiarc.ini", "session.ini", "shortcuts.scf"].each do |config_file|
    describe file("#{config_dir}/#{config_file}") do
      it { should exist }
    end
  end
end

control "doublecmd desktop entry is in place" do
  username = input('username')
  describe file("/home/#{username}/.local/share/applications/doublecmd.desktop") do
    it { should exist }
    its('content') { should match /Exec=\/usr\/local\/bin\/doublecmd/ }
  end
  describe file("/home/#{username}/.local/share/icons/doublecmd.svg") do
    it { should exist }
  end
end

# Workrave

control "workrave is installed and working" do
  describe file('/usr/bin/workrave') do
    it { should exist }
    it { should be_executable }
  end
end

control "workrave autostart entry is in place" do
  username = input('username')
  describe file("/home/#{username}/.config/autostart/workrave.desktop") do
    it { should exist }
    its('content') { should match /Exec=workrave/ }
  end
end

# Obsidian

control "obsidian flatpak is installed" do
  describe command('flatpak info md.obsidian.Obsidian') do
    its('exit_status') { should eq 0 }
  end
end

control "obsidian config is in place" do
  username = input('username')
  describe file("/home/#{username}/.var/app/md.obsidian.Obsidian/config/obsidian/obsidian.json") do
    it { should exist }
    its('content') { should match /Dropbox\/projects\/Obsidian\/notes/ }
  end
end

# Firefox

control "firefox has non-free codec support (Fedora only - Mint ships codecs by default)" do
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
