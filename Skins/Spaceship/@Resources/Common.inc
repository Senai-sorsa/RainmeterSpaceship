; Included by every Spaceship module (after its own [Rainmeter] Update=...).
[Rainmeter]
AccurateText=1
DynamicWindowSize=1
Group=Spaceship
OnRefreshAction=[!Move "((#WX#+#DX#)*#Scale#+#OriginX#+#MonX#)" "((#WY#+#DY#)*#Scale#+#OriginY#+#MonY#)"][!ZPos -2][!KeepOnScreen 0][!Draggable 0][!SnapEdges 0]
ContextTitle=Control Center
ContextAction=[!ToggleConfig "Spaceship\Overlay\Control" "Control.ini"]
ContextTitle2=App drawer (CARGO)
ContextAction2=[!ToggleConfig "Spaceship\Overlay\Drawer" "Drawer.ini"]
ContextTitle3=Edit mode on / off
ContextAction3=[!CommandMeasure mScript "ToggleEdit()" "Spaceship\Controller"]
ContextTitle4=Refresh HUD
ContextAction4=[!RefreshGroup Spaceship]

[Variables]
@IncludeSettings=#@#Settings.inc
@IncludeHardware=#@#Hardware.inc
@IncludeState=#@#State.inc
@IncludeOffsets=#@#Offsets.inc
@IncludeGeometry=#CURRENTPATH#Geometry.inc

[sText]
AntiAlias=1
FontFace=#FontText#
FontSize=11
FontWeight=600
FontColor=#ColorText#
StringAlign=LeftTop
X=0
Y=0
Text=
