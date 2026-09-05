# Custom resource checking whether a desktop-file-id is pinned to the panel/taskbar - mirrors
# pyinfra/panel_pin.py's two storage locations (KDE Task Manager's launchers= line, Cinnamon's
# grouped-window-list pinned-apps.value) so every "X is pinned" control doesn't repeat the same
# os.debian? branch.
class PanelPin < Inspec.resource(1)
  name 'panel_pin'
  desc 'Checks whether a desktop-file-id is pinned to the panel/taskbar'
  example "
    describe panel_pin('com.mitchellh.ghostty.desktop', 'sebastiaan') do
      it { should be_pinned }
    end

    describe panel_pin('md.obsidian.Obsidian.desktop', 'sebastiaan', true) do
      it { should be_pinned }
    end
  "

  def initialize(desktop_file_id, username, flatpak = false)
    @desktop_file_id = desktop_file_id
    @username = username
    @flatpak = flatpak
  end

  def pinned?
    if inspec.os.debian?
      # grouped-window-list needs a ":flatpak" suffix to resolve a Flatpak app's pin - see
      # pyinfra/panel_pin.py's _pin_cinnamon docstring. An exact-match check against the form
      # the caller asserts, rather than a substring check, is required to actually catch a
      # regression here: a substring check matches both "id.desktop" and "id.desktop:flatpak",
      # so it stayed green while pyinfra was pinning Flatpak apps in the wrong (bare) form -
      # confirmed live against dell_laptop.
      expected_launcher = @flatpak ? "#{@desktop_file_id}:flatpak" : @desktop_file_id
      cmd = inspec.command(
        "python3 -c \"import json; print(json.load(open('$(ls " \
        "/home/#{@username}/.config/cinnamon/spices/grouped-window-list@cinnamon.org/*.json" \
        ")'))['pinned-apps']['value'])\""
      )
      cmd.stdout.include?("'#{expected_launcher}'")
    else
      cmd = inspec.command(
        "grep '^launchers=' /home/#{@username}/.config/plasma-org.kde.plasma.desktop-appletsrc"
      )
      cmd.stdout.include?("applications:#{@desktop_file_id}")
    end
  end

  def to_s
    "Panel pin for #{@desktop_file_id}"
  end
end
