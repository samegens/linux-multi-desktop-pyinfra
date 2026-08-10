username = input('username')

# Services

ssh_service_name = os.debian? ? 'ssh' : 'sshd'

control "#{ssh_service_name} service is enabled and running" do
  tag :system
  describe service(ssh_service_name) do
    it { should be_enabled }
    it { should be_running }
  end
end

['docker'].each do |svc|
  control "#{svc} service is enabled and running" do
    tag :system
    describe service(svc) do
      it { should be_enabled }
      it { should be_running }
    end
  end
end

control "k3s service is enabled and running" do
  tag :system
  describe service('k3s') do
    it { should be_enabled }
    it { should be_running }
  end
end

# Group memberships

control "user is in docker group" do
  tag :system
  describe user(username) do
    its('groups') { should include 'docker' }
  end
end

['video', 'dialout'].each do |grp|
  control "user is in #{grp} group" do
    tag :system
    describe user(username) do
      its('groups') { should include grp }
    end
  end
end

# TODO: uncomment once an NFS mounts module is built (deferred, see README backlog)
# control "homeserver-public NFS share is mounted and accessible" do
#   describe mount('/mnt/homeserver-public') do
#     it { should be_mounted }
#   end
# end

# TODO: uncomment once a vm.max_map_count / OpenSearch module is built (deferred)
# control "vm.max_map_count is set to 262144 for OpenSearch" do
#   describe kernel_parameter('vm.max_map_count') do
#     its('value') { should eq 262144 }
#   end
# end

# TODO: uncomment once personal /etc/hosts entries are ported (deferred, see README backlog)
# control "hosts file contains required entries" do
#   describe file('/etc/hosts') do
#     its('content') { should match /liteserver/ }
#   end
# end

# Locale

control "locale is set to en_US.UTF-8" do
  tag :system
  describe command('localectl status') do
    its('stdout') { should match /LANG=en_US\.UTF-8/ }
  end
end

control "right Alt is configured as compose key" do
  tag :system
  if os.debian?
    describe file('/etc/default/keyboard') do
      its('content') { should match /XKBOPTIONS="?compose:ralt"?/ }
    end
  else
    describe command('localectl status') do
      its('stdout') { should match /X11 Options:.*compose:ralt/ }
    end
  end
end

# Config files

control "go PATH script is in place" do
  tag :system
  describe file('/etc/profile.d/go.sh') do
    it { should exist }
    its('content') { should match %r{/usr/local/go/bin} }
  end
end

# SSH

control "ssh directory has correct permissions" do
  tag :system
  describe file("/home/#{username}/.ssh") do
    it { should be_directory }
    its('mode') { should cmp '0700' }
    its('owner') { should eq username }
  end
end

control "ssh config is in place with correct permissions" do
  tag :system
  describe file("/home/#{username}/.ssh/config") do
    it { should exist }
    its('mode') { should cmp '0600' }
    its('owner') { should eq username }
  end
end

ssh_keys = [
  'cubi', 'fitpc', 'fitlet', 'fitlet-tst', 'fitlet-acc', 'liteserver', 'liteserver-tst',
  'github_samegens', 'github_blauwe-lucht', 'gitlab', 'github_adopteerregenwoud', 'bhosted',
]
ssh_keys.each do |key_name|
  control "SSH private key #{key_name} is installed with correct permissions" do
    tag :system
    describe file("/home/#{username}/.ssh/#{key_name}") do
      it { should exist }
      its('mode') { should cmp '0600' }
      its('owner') { should eq username }
    end
  end

  control "SSH public key #{key_name}.pub is installed" do
    tag :system
    describe file("/home/#{username}/.ssh/#{key_name}.pub") do
      it { should exist }
      its('owner') { should eq username }
    end
  end
end

control "homeserver key symlinks point to cubi" do
  tag :system
  describe file("/home/#{username}/.ssh/homeserver") do
    it { should be_symlink }
    it { should exist }
  end
  describe file("/home/#{username}/.ssh/homeserver.pub") do
    it { should be_symlink }
    it { should exist }
  end
end

# Root's own keys under /root/.ssh (mode 0700) aren't checked here - the test user can't stat
# inside /root without sudo, and this repo doesn't grant the test user broader sudo access just
# for that. Verified manually instead: `sudo ls -la /root/.ssh` on mint_vm after a real deploy.

# Only tests machines that are publicly reachable, we may be running the tests from
# outside the local network.
ssh_simple_auth_checks = {
  'github.com' => /successfully authenticated/,
  'github.com-blauwe-lucht' => /successfully authenticated/,
# broken, fix later  'github_adopteerregenwoud' => /successfully authenticated/,
  'gitlab.com' => /Welcome to GitLab/,
}
ssh_simple_auth_checks.each do |host_alias, expected_output|
  control "ssh key auth works for #{host_alias}" do
    tag :system
    describe command("ssh -T -o BatchMode=yes -o StrictHostKeyChecking=no #{host_alias} 2>&1") do
      its('stdout') { should match expected_output }
    end
  end
end

ssh_checks = [
  'bhosted',
  'liteserver',
# broken, fix later  'backup_server',
  'thuis',
]
ssh_checks.each do |host_alias|
  control "ssh works for #{host_alias}" do
    tag :system
    describe command("ssh -o BatchMode=yes -o StrictHostKeyChecking=no #{host_alias} -- echo success 2>&1") do
      its('stdout') { should match /success/ }
    end
  end
end

# Git config

control "git is configured correctly" do
  tag :system
  describe file("/home/#{username}/.gitconfig") do
    it { should exist }
    its('content') { should match /name\s*=\s*Sebastiaan/ }
    its('content') { should match /email\s*=\s*\S+/ }
    its('content') { should match /filemode\s*=\s*true/i }
    its('content') { should match /autosetupremote\s*=\s*true/i }
    its('content') { should match /defaultbranch\s*=\s*main/i }
    its('content') { should match /default\s*=\s*current/ }
  end
end

control "Python venv pyinfra-latest exists" do
  tag :system
  describe file("/home/#{username}/python3-venv/pyinfra-latest/bin/activate") do
    it { should exist }
    its('owner') { should eq username }
  end
end
