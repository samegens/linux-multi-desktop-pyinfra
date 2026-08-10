# Double Commander - see pyinfra/modules/doublecmd.py

control "doublecmd is installed and working" do
  tag :doublecmd
  describe file('/usr/local/bin/doublecmd') do
    it { should exist }
    it { should be_executable }
    it { should be_symlink }
    its('link_path') { should match %r{^/opt/doublecmd-} }
  end
end

control "doublecmd config files are in place" do
  tag :doublecmd
  username = input('username')
  config_dir = "/home/#{username}/.config/doublecmd"
  ["doublecmd.xml", "multiarc.ini", "session.ini", "shortcuts.scf"].each do |config_file|
    describe file("#{config_dir}/#{config_file}") do
      it { should exist }
    end
  end
end

control "doublecmd desktop entry is in place" do
  tag :doublecmd
  username = input('username')
  describe file("/home/#{username}/.local/share/applications/doublecmd.desktop") do
    it { should exist }
    its('content') { should match /Exec=\/usr\/local\/bin\/doublecmd/ }
  end
  describe file("/home/#{username}/.local/share/icons/doublecmd.svg") do
    it { should exist }
  end
end

control "doublecmd F9 launches ghostty in the active directory" do
  tag :doublecmd
  username = input('username')

  shortcuts_content = file("/home/#{username}/.config/doublecmd/shortcuts.scf").content
  f9_command_setting = shortcuts_content[/<Shortcut>F9<\/Shortcut>\s*<Command>(\w+)<\/Command>/, 1]
  describe 'doublecmd F9 hotkey command' do
    subject { f9_command_setting }
    it { should cmp 'cm_RunTerm' }
  end

  doublecmd_xml_content = file("/home/#{username}/.config/doublecmd/doublecmd.xml").content
  just_run_terminal_setting = doublecmd_xml_content[/<JustRunTerminal>(.*?)<\/JustRunTerminal>/, 1]
  describe 'doublecmd JustRunTerminal command' do
    subject { just_run_terminal_setting }
    it { should cmp 'ghostty' }
  end

  just_run_term_params_setting = doublecmd_xml_content[/<JustRunTermParams>(.*?)<\/JustRunTermParams>/, 1]
  describe 'doublecmd JustRunTermParams passes the active directory' do
    subject { just_run_term_params_setting }
    it { should cmp '--working-directory=%d' }
  end
end
