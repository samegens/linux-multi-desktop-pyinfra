username = input('username')

# Services

['ssh'].each do |svc|
  control "#{svc} service is enabled and running" do
    describe service(svc) do
      it { should be_enabled }
      it { should be_running }
    end
  end
end

# TODO: uncomment once modules/docker.py is built
# ['docker'].each do |svc|
#   control "#{svc} service is enabled and running" do
#     describe service(svc) do
#       it { should be_enabled }
#       it { should be_running }
#     end
#   end
# end

# TODO: uncomment once a k3s module is built (deferred, see README backlog)
# control "k3s service is enabled and running" do
#   describe service('k3s') do
#     it { should be_enabled }
#     it { should be_running }
#   end
# end

# Group memberships

# TODO: uncomment once modules/docker.py is built (adds username to the docker group)
# control "user is in docker group" do
#   describe user(username) do
#     its('groups') { should include 'docker' }
#   end
# end

# TODO: uncomment if/once webcam (video) and USB (dialout) access tasks are ported
# ['video', 'dialout'].each do |grp|
#   control "user is in #{grp} group" do
#     describe user(username) do
#       its('groups') { should include grp }
#     end
#   end
# end

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
  # /etc/default/locale is a symlink to ../locale.conf on this (systemd-style) layout -
  # modules/base.py writes the real underlying file, see the comment there.
  describe file('/etc/locale.conf') do
    it { should exist }
    its('content') { should match /LANG=en_US\.UTF-8/ }
  end
end

# Config files

control ".inputrc is configured" do
  describe file("/home/#{username}/.inputrc") do
    it { should exist }
    its('owner') { should eq username }
    its('content') { should match /completion-ignore-case On/ }
  end
end

control "go PATH script is in place" do
  describe file('/etc/profile.d/go.sh') do
    it { should exist }
    its('content') { should match %r{/usr/local/go/bin} }
  end
end

# TODO: uncomment once pyinfra/run.sh creates /var/log/pyinfra (task 5)
# control "pyinfra log directory exists with correct ownership" do
#   describe directory('/var/log/pyinfra') do
#     it { should exist }
#     its('owner') { should eq username }
#   end
# end

# SSH

control "ssh directory has correct permissions" do
  describe file("/home/#{username}/.ssh") do
    it { should be_directory }
    its('mode') { should cmp '0700' }
    its('owner') { should eq username }
  end
end

# TODO: uncomment once ssh.py writes ~/.ssh/config (deferred until real hosts/keys are added)
# control "ssh config is in place with correct permissions" do
#   describe file("/home/#{username}/.ssh/config") do
#     it { should exist }
#     its('mode') { should cmp '0600' }
#     its('owner') { should eq username }
#   end
# end

# TODO: uncomment and populate once group_data/all.py:ssh_key_names has entries
# ssh_keys = []
# ssh_keys.each do |key_name|
#   control "SSH private key #{key_name} is installed with correct permissions" do
#     describe file("/home/#{username}/.ssh/#{key_name}") do
#       it { should exist }
#       its('mode') { should cmp '0600' }
#       its('owner') { should eq username }
#     end
#   end
#
#   control "SSH public key #{key_name}.pub is installed" do
#     describe file("/home/#{username}/.ssh/#{key_name}.pub") do
#       it { should exist }
#       its('owner') { should eq username }
#     end
#   end
# end

# Git config

control "git is configured correctly" do
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

# Bashrc

control ".bashrc is configured" do
  describe file("/home/#{username}/.bashrc") do
    it { should exist }
    its('content') { should match /\.cargo\/bin/ }
    its('content') { should match /alias ll=/ }
  end
end

# TODO: uncomment once modules/python_venv.py is built
# control "Python venv pyinfra-latest exists" do
#   describe file("/home/#{username}/python3-venv/pyinfra-latest/bin/activate") do
#     it { should exist }
#     its('owner') { should eq username }
#   end
# end
