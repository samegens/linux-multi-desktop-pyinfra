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
  username = input('username')
  if os.debian?
    # grouped-window-list (Cinnamon's taskbar) keeps its pinned-apps list in its own
    # per-instance xlet settings file - see panel_pin.py's _find_cinnamon_taskbar_settings_file
    # docstring for why this isn't org.cinnamon favorite-apps.
    describe command(
      "python3 -c \"import json; " \
      "print(json.load(open('$(ls /home/#{username}/.config/cinnamon/spices/" \
      "grouped-window-list@cinnamon.org/*.json)'))['pinned-apps']['value'])\""
    ) do
      its('stdout') { should match /com\.mitchellh\.ghostty\.desktop/ }
    end
  else
    describe command(
      "grep '^launchers=' " \
      "/home/#{username}/.config/plasma-org.kde.plasma.desktop-appletsrc"
    ) do
      its('stdout') { should match /applications:com\.mitchellh\.ghostty\.desktop/ }
    end
  end
end
