# Ghostty - see pyinfra/modules/ghostty.py

control "ghostty is installed and working" do
  tag :ghostty
  describe command('ghostty --version') do
    its('exit_status') { should eq 0 }
  end
end

control "ghostty new windows are maximized" do
  tag :ghostty
  username = input('username')
  describe file("/home/#{username}/.config/ghostty/config.ghostty") do
    it { should exist }
    its('content') { should match /^maximize=true$/ }
  end
end

control "ghostty is pinned to the panel" do
  tag :ghostty
  describe panel_pin('com.mitchellh.ghostty.desktop', input('username')) do
    it { should be_pinned }
  end
end
