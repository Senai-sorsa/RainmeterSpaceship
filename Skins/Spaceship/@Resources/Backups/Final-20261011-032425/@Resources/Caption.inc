; HUD hover caption, drawn on top of every module (included last by each module .ini).
; Scripts\lib.lua (H.caption) fills it in on mouse-over and hides it on mouse-leave / after a timeout.
; Set CaptionStyle=0 in Settings.inc to go back to Windows tooltips.
[CaptionBox]
Meter=Shape
Hidden=1
Shape=Rectangle 0,0,0,0 | Fill Color 0,0,0,0 | StrokeWidth 0

[Caption]
Meter=String
Hidden=1
StringAlign=LeftCenter
AntiAlias=1
FontWeight=700
FontSize=8
FontColor=215,240,255,255
