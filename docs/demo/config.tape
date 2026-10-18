# Shared settings and hidden launch for every demo tape.
# Window decorations (WindowBar, BorderRadius, Padding, Margin) are left out:
# they need a newer ffmpeg than some Windows installs ship.

Set Shell "powershell"
Set FontSize 16
Set Width 1100
Set Height 760
Set TypingSpeed 70ms

Hide
Type "Remove-Item Env:NO_COLOR -ErrorAction SilentlyContinue; .\venv\Scripts\python.exe -m ebird_cli.main"
Enter
Wait+Screen@90s /⋙/
Ctrl+L
Sleep 500ms
Show
