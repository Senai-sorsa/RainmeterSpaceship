param([double]$secs = 15)
function T { $t = 0.0; Get-Process | Where-Object { $_.Path -like '*ms-playwright*' } | ForEach-Object { $t += $_.TotalProcessorTime.TotalSeconds }; $t }
$a = T; Start-Sleep -Seconds $secs; $z = T
"{0:N1}% of one core" -f (($z - $a) / $secs * 100)
