# Bashrc - see pyinfra/modules/bashrc.py

control ".bashrc is configured" do
  tag :bashrc
  username = input('username')
  describe file("/home/#{username}/.bashrc") do
    it { should exist }
    its('content') { should match /\.cargo\/bin/ }
    its('content') { should match /alias ll=/ }
  end
end

control ".inputrc is configured" do
  tag :bashrc
  username = input('username')
  describe file("/home/#{username}/.inputrc") do
    it { should exist }
    its('owner') { should eq username }
    its('content') { should match /completion-ignore-case On/ }
  end
end
