# Precise location from Windows Location Services (needs Location turned on for desktop apps).
# Output: lat|lon|alt   (empty on failure; the skin then falls back to IP geolocation)
$ErrorActionPreference = 'SilentlyContinue'
Add-Type -AssemblyName System.Device
$w = New-Object System.Device.Location.GeoCoordinateWatcher
$w.Start()
$t = 0
while (($w.Status -ne 'Ready') -and ($t -lt 50)) { Start-Sleep -Milliseconds 100; $t++ }
$c = $w.Position.Location
if ($c -and -not $c.IsUnknown) { Write-Output ("{0:F4}|{1:F4}|{2:F0}" -f $c.Latitude, $c.Longitude, $c.Altitude) }
$w.Stop()
