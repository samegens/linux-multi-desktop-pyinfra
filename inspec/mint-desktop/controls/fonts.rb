# JetBrainsMono Nerd Font + Google Fonts - see pyinfra/modules/fonts.py

control "JetBrainsMono Nerd Font is installed globally" do
  tag :fonts
  describe command('fc-list') do
    its('stdout') { should match /JetBrainsMono Nerd Font/ }
    its('stdout') { should match /JetBrainsMonoNL Nerd Font/ }
  end
end

control "Google Fonts are installed globally" do
  tag :fonts
  describe command('fc-list') do
    its('stdout') { should match /Great Vibes/ }
    its('stdout') { should match /Playfair Display/ }
  end
end
