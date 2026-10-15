<#
.SYNOPSIS
  One-time setup for the Spaceship HUD's Jarvis voice assistant. Safe to run again.

  Checks / installs (asks before installing anything):
    1. Python 3 (python.org build, via winget)       - runs the Jarvis service
    2. The packages in requirements.txt (pip)        - into a private folder (%LOCALAPPDATA%\SpaceshipHUD\venv),
                                                       exact versions, so your other Python programs are untouched
    3. Ollama + a model                              - the AI brain (runs locally on your GPU)
    4. Optional: Kokoro-82M natural voice (~400 MB) - otherwise the built-in Windows voice
       Optional: wake word, stop words (Vosk, ~41 MB), smart note search
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
Step 'Jarvis packages (private copy, pinned versions - the first time is a large download)'
$venv = Join-Path $env:LOCALAPPDATA 'SpaceshipHUD\venv'
$vpy = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $vpy)) { & py -3 -m venv $venv }
if (-not (Test-Path $vpy)) { Write-Host "Could not create $venv - see the messages above." -ForegroundColor Yellow; exit 1 }
& $vpy -m pip install --disable-pip-version-check -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { Write-Host 'pip install failed - see the messages above.' -ForegroundColor Yellow; exit 1 }
Set-Setting 'JarvisPython' (Join-Path $venv 'Scripts\pythonw.exe')
# the GPU voice: onnxruntime-gpu 1.23 (CUDA 12, the same libraries as Whisper) replaces the CPU build in the same
# folder. chromadb / openwakeword / piper / kokoro / faster-whisper ask for "onnxruntime" by name and work with either
# (tested 2026-10-14), so the line above reinstalls the CPU build each run: uninstall it, then force the GPU build back.
& $vpy -m pip uninstall -y --disable-pip-version-check onnxruntime
& $vpy -m pip install --disable-pip-version-check --force-reinstall --no-deps -r (Join-Path $PSScriptRoot 'requirements-gpu.txt')
if ($LASTEXITCODE -ne 0) { Write-Host 'GPU voice packages failed - see the messages above.' -ForegroundColor Yellow; exit 1 }
Write-Host 'Downloading the speech-recognition model (one time, ~500 MB)...'
& $vpy -c "from faster_whisper import WhisperModel; WhisperModel('small.en', device='cpu', compute_type='int8'); print('speech model ready')"
Step 'Microphone'
& $vpy -c "import sounddevice as sd; d = sd.query_devices(kind='input'); print('Microphone:', d['name'])"
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

# ------------------------------------------------------------------ 4. Natural voice (Kokoro-82M)
Step 'Voice'
if (Ask 'Install the natural Kokoro voice (~400 MB download, runs on the NVIDIA card if there is one)? No = the built-in Windows voice') {
  if ($true) {
    $vdir = Join-Path $PSScriptRoot 'voices'
    New-Item -ItemType Directory -Force -Path $vdir | Out-Null
    $base = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0'
    # int8 = the CPU voice; the full model is only used on the GPU (int8 runs 3x slower there)
    foreach ($f in 'kokoro-v1.0.int8.onnx', 'kokoro-v1.0.onnx', 'voices-v1.0.bin') {
      $out = Join-Path $vdir $f
      if (-not (Test-Path $out) -or (Get-Item $out).Length -lt 1MB) {
        Write-Host "Downloading $f ..."
        try { Invoke-WebRequest -Uri "$base/$f" -OutFile $out -UseBasicParsing }
        catch { Write-Host "Download failed: $($_.Exception.Message)" -ForegroundColor Yellow }
      }
    }
    $model = Join-Path $vdir 'kokoro-v1.0.int8.onnx'
    if ((Test-Path $model) -and (Test-Path (Join-Path $vdir 'voices-v1.0.bin'))) {
      Set-Setting 'JarvisVoice' $model
      Set-Setting 'JarvisKokoroVoice' 'bm_george'
      Write-Host 'Kokoro ready (voice: bm_george - change it in Control Center > JARVIS > KOKORO VOICE).'
      & $vpy -c "from kokoro_onnx import Kokoro; import sounddevice as sd; k = Kokoro(r'$model', r'$(Join-Path $vdir 'voices-v1.0.bin')'); s, r = k.create('Jarvis online.', voice='bm_george', speed=1.0, lang='en-gb'); sd.play(s, r); sd.wait()"
    }
  }
}

# ------------------------------------------------------------------ 4b. Wake word
Step 'Wake word ("Hey Jarvis")'
if (Ask 'Install the "Hey Jarvis" wake word (openWakeWord, small, runs on the CPU)?') {
  & $vpy -c "import openwakeword; openwakeword.utils.download_models(model_names=['hey_jarvis']); print('wake word model ready')"
  if ($LASTEXITCODE -eq 0) { Set-Setting 'JarvisWakeWord' '1'; Write-Host 'Say "Hey Jarvis" to wake him (turn it off in Control Center > JARVIS > WAKE WORD).' }
  else { Write-Host 'Wake word install failed - clicking the hologram still works.' -ForegroundColor Yellow }
}

# ------------------------------------------------------------------ 4b2. Stop words while he speaks (Vosk)
Step 'Stop words ("stop", "be quiet" while he talks)'
$vosk = Join-Path $PSScriptRoot 'vosk'
$vname = 'vosk-model-small-en-us-0.15'
if (Test-Path (Join-Path $vosk "$vname\am")) { Write-Host 'Stop-word model found.' }
elseif (Ask 'Install the stop-word model (Vosk, ~41 MB download, 68 MB on disk, runs on the CPU only while he talks)?') {
  $zip = Join-Path $env:TEMP "$vname.zip"
  try {
    Invoke-WebRequest -Uri "https://alphacephei.com/vosk/models/$vname.zip" -OutFile $zip -UseBasicParsing
    # pinned: the exact file tested with Jarvis (2026-10-14)
    if ((Get-FileHash $zip -Algorithm SHA256).Hash -ne '30F26242C4EB449F948E42CB302DD7A686CB29A3423A8367F99FF41780942498') { throw 'the download does not match the expected file' }
    New-Item -ItemType Directory -Force -Path $vosk | Out-Null
    Expand-Archive -Path $zip -DestinationPath $vosk -Force
    Write-Host 'Stop-word model ready.'
  } catch { Write-Host "Stop-word model not installed ($($_.Exception.Message)) - a click or the stop key still stops him." -ForegroundColor Yellow }
  finally { Remove-Item $zip -ErrorAction SilentlyContinue }
}

# ------------------------------------------------------------------ 4c. Smart note search (ChromaDB)
Step 'Smart note search (ChromaDB)'
if (Ask 'Install smart note search (ChromaDB - finds notes by meaning, ~100 MB first time)?') {
  & $vpy -c "from chromadb.utils import embedding_functions as e; e.DefaultEmbeddingFunction()(['warm up']); print('search model ready')"
  if ($LASTEXITCODE -eq 0) { Set-Setting 'JarvisSmartSearch' '1' }
  else { Write-Host 'ChromaDB did not start - Jarvis uses keyword search instead.' -ForegroundColor Yellow }
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
  } catch { Write-Host 'The Windows voice is not available - install the Kokoro voice above instead.' -ForegroundColor Yellow }
} else { Write-Host 'Using the natural voice (you should have heard "Jarvis online." above).' }

# ------------------------------------------------------------------ done
Step 'Refreshing the HUD'
$rm = Get-Process Rainmeter -ErrorAction SilentlyContinue | Select-Object -First 1
if ($rm -and $rm.Path) { Start-Process $rm.Path -ArgumentList '!Refresh "Spaceship\Center\Sphere"' }
Write-Host "`nDone. If Jarvis is switched off, turn him on in Control Center > JARVIS. Then click the hologram in the middle of the HUD and talk. The first answer takes a few extra seconds while the models load." -ForegroundColor Green
