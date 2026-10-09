# Sends a media key:  media.ps1 -Key playpause|next|prev|mute
param([string]$Key = 'playpause')
$codes = @{ playpause = 0xB3; next = 0xB0; prev = 0xB1; mute = 0xAD }
Add-Type -Name K -Namespace W -MemberDefinition '[DllImport("user32.dll")] public static extern void keybd_event(byte k, byte s, int f, int e);'
$c = [byte]$codes[$Key]
[W.K]::keybd_event($c, 0, 1, 0); [W.K]::keybd_event($c, 0, 3, 0)
