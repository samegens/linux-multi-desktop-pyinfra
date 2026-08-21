# JetBrainsMono Nerd Font - see pyinfra/modules/fonts.py

control "JetBrainsMono Nerd Font is installed globally" do
  tag :fonts
  describe command('fc-list') do
    its('stdout') { should match /JetBrainsMono Nerd Font/ }
    its('stdout') { should match /JetBrainsMonoNL Nerd Font/ }
  end
end
