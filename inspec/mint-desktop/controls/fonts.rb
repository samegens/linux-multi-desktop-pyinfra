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

control "Microsoft core/ClearType fonts resolve to the real font, not a fallback" do
  tag :fonts
  # fc-match falls back to a substitute (e.g. Liberation Sans, Liberation Serif) when the
  # named font isn't actually installed - checking fc-list for the name isn't enough since
  # fontconfig's own substitution rules can make fc-match "succeed" against a fallback.
  # Only fc-match's actual output naming the real font proves it's genuinely installed.
  ["Arial", "Times New Roman", "Calibri", "Consolas"].each do |font_name|
    describe command("fc-match \"#{font_name}\"") do
      its('stdout') { should match /#{Regexp.escape(font_name)}/ }
    end
  end
end
