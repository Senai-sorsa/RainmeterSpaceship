<#
.SYNOPSIS
  One-time setup for the Spaceship HUD's Jarvis voice assistant. Safe to run again.

  Checks / installs (asks before installing anything):
    1. Python 3 (python.org build, via winget)       - runs the Jarvis service
    2. faster-whisper, sounddevice, numpy (pip)      - speech recognition + microphone / speaker audio
    3. Ollama + a model                              - the AI brain (runs locally on your GPU)
    4. Optional: Piper + the "Alan" British voice    - natural voice (otherwise the built-in Windows voice)
  Then writes the Jarvis settings into Settings.inc and refreshes the HUD.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File "<skin>\@Resources\Jarvis\Setup-Jarvis.ps1"
#>
$ErrorActionPreference = 'Stop'
$Res = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Settings = Join-Path $Res 'Settings.inc'
function Step($t) { Write-Host "`n>> $t" -ForegroundColor Cyan }
function Ask($q) { $a = Read-Host "$q [Y/n]"; return ($a -eq '' -or $a -match '^[Yy]') }
function Set-Setting($key, $value) {
  $text = Get-Content $Settings -Raw
  if ($text -match "(?m)^\s*$([regex]::Escape($key))\s*=") {
    $text = [regex]::Replace($text, "(?m)^(\s*$([regex]::Escape($key))\s*=).*$", "`${1}$value")
    Set-Content -Path $Settings -Value $text -NoNewline
  } else { Add-Content -Path $Settings -Value "$key=$value" }
}

# ------------------------------------------------------------------ 1. Python
Step 'Python'
$py = Get-Command py -ErrorAction SilentlyContinue
if (-not $py) {
  if (Ask 'Python is not installed. Install Python 3.12 with winget?') {
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
    $py = Get-Command py -ErrorAction SilentlyContinue
  }
  if (-not $py) { Write-Host 'Python is needed for Jarvis. Install it from python.org (tick "py launcher"), then run this again.' -ForegroundColor Yellow; exit 1 }
}
& py -3 --version

# ------------------------------------------------------------------ 2. Python packages
Step 'Speech + audio packages (faster-whisper, sounddevice, numpy)'
& py -3 -m pip install --upgrade --user faster-whisper sounddevice numpy
if ($LASTEXITCODE -ne 0) { Write-Host 'pip install failed - see the messages above.' -ForegroundColor Yellow; exit 1 }
Write-Host 'Downloading the speech-recognition model (one time, ~150 MB)...'
& py -3 -c "from faster_whisper import WhisperModel; WhisperModel('base.en', device='cpu', compute_type='int8'); print('speech model ready')"
Step 'Microphone'
& py -3 -c "import sounddevice as sd; d = sd.query_devices(kind='input'); print('Microphone:', d['name'])"
if ($LASTEXITCODE -ne 0) { Write-Host 'No microphone found. Plug one in, and check Settings > Privacy & security > Microphone > "Let desktop apps access your microphone".' -ForegroundColor Yellow }

# ------------------------------------------------------------------ 3. Ollama + model
Step 'Ollama'
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
  if (Ask 'Ollama is not installed. Install it with winget?') {
    winget install -e --id Ollama.Ollama --accept-package-agreements --accept-source-agreements
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
    $ollama = Get-Command ollama -ErrorAction SilentlyContinue
  }
}
if ($ollama) {
  $models = (& ollama list 2>$null | Select-Object -Skip 1 | ForEach-Object { ($_ -split '\s+')[0] }) | Where-Object { $_ }
  Write-Host ("Models you have: " + ($(if ($models) { $models -join ', ' } else { 'none' })))
  $default = 'llama3.1:8b'
  $choice = Read-Host "Model for Jarvis (Enter = $default; a smaller, faster one: llama3.2:3b)"
  if ($choice -eq '') { $choice = $default }
  if (-not ($models -contains $choice -or $models -contains "${choice}:latest")) {
    if (Ask "Download $choice now?") { & ollama pull $choice }
  }
  Set-Setting 'JarvisModel' $choice
} else { Write-Host 'Skipped - Jarvis needs Ollama to answer.' -ForegroundColor Yellow }

# ------------------------------------------------------------------ 4. Optional natural voice (Piper)
Step 'Voice'
if (Ask 'Install the natural "Alan" British voice (Piper, ~65 MB)? No = the built-in Windows voice') {
  & py -3 -m pip install --upgrade --user piper-tts
  $vdir = Join-Path $PSScriptRoot 'voices'
  New-Item -ItemType Directory -Force -Path $vdir | Out-Null
  $base = 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium'
  foreach ($ext in '.onnx', '.onnx.json') {
    $out = Join-Path $vdir "en_GB-alan-medium$ext"
    if (-not (Test-Path $out)) { Invoke-WebRequest -Uri "$base$ext" -OutFile $out -UseBasicParsing }
  }
  Set-Setting 'JarvisVoice' (Join-Path $vdir 'en_GB-alan-medium.onnx')
}

# ------------------------------------------------------------------ 5. Sounds
Step 'Sounds'
$snd = Join-Path $Res 'Sounds'
New-Item -ItemType Directory -Force -Path $snd | Out-Null
if (Test-Path (Join-Path $snd 'startup.wav')) { Write-Host 'startup.wav found - it plays with the startup sequence and when you click Jarvis.' }
else { Write-Host "Put your startup sound in $snd as startup.wav (WAV only - convert an MP3 first)." -ForegroundColor Yellow }

# ------------------------------------------------------------------ voice check
Step 'Voice check'
if (-not (Get-Content $Settings -Raw | Select-String -Pattern '(?m)^\s*JarvisVoice\s*=\s*\S')) {
  try {
    Add-Type -AssemblyName System.Speech
    $s = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $gb = $s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -eq 'en-GB' } | Select-Object -First 1
    if ($gb) { $s.SelectVoice($gb.VoiceInfo.Name) }
    Write-Host ("Using the Windows voice: " + $s.Voice.Name + "  (you should hear it now)")
    $s.Speak('Jarvis online.'); $s.Dispose()
  } catch { Write-Host 'The Windows voice is not available - install the Piper voice above instead.' -ForegroundColor Yellow }
} else { Write-Host 'Using the Piper voice.' }

# ------------------------------------------------------------------ done
Step 'Starting Jarvis'
Set-Setting 'JarvisEnabled' '1'
$rm = Get-Process Rainmeter -ErrorAction SilentlyContinue | Select-Object -First 1
if ($rm -and $rm.Path) { Start-Process $rm.Path -ArgumentList '!Refresh "Spaceship\Center\Sphere"' }
Write-Host "`nDone. Click the hologram in the middle of the HUD and talk. The first answer takes a few extra seconds while the models load." -ForegroundColor Green
