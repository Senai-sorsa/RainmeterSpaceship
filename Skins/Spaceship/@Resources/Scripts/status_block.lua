-- Small "ship + counters" blocks at the bottom of each side column (230 x 80).
-- Kind=upkeep : updates | upgrades | antivirus        (hourly)
-- Kind=dev    : wsl | ollama | tailscale | docker      (every 2 min)
local H
local kind, mirror = 'upkeep', false
local vals = {}
local tick = 0

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
  kind = SELF:GetOption('Kind', 'upkeep')
  mirror = SELF:GetOption('Mirror', '0') == '1'
end

function OnRun()
  local out = H.sval('mRun', '')
  vals = {}
  for p in string.gmatch(string.gsub(out, '[\r\n]', '') .. '|', '(.-)|') do vals[#vals + 1] = p end
end

local function n(v) local x = tonumber(v); if not x or x < 0 then return '--' end; return tostring(x) end

local function rows()
  if kind == 'upkeep' then
    return {
      { 'UPD', n(vals[1]), (tonumber(vals[1]) or 0) > 0, 'Pending Windows updates - click: Windows Update' },
      { 'PKG', n(vals[2]), (tonumber(vals[2]) or 0) > 0, 'winget upgrades available - click: upgrade in Terminal' },
      { 'AV', vals[3] and (vals[3] .. ' ' .. (vals[4] or '')) or '--', vals[4] == 'OFF', 'Antivirus - click: Windows Security' },
    }, 'shield'
  end
  return {
    { 'WSL', n(vals[1]), false, 'Running WSL distros - click: Terminal' },
    { 'LLM', n(vals[2]), false, 'Ollama models loaded - click: ollama ps' },
    { 'NET', vals[3] or '--', vals[3] ~= nil and vals[3] ~= 'RUNNING' and vals[3] ~= 'NONE', 'Tailscale state - click: Tailscale' },
  }, 'nodes'
end

function Update()
  H.refreshTier()
  tick = tick + 1
  local period = kind == 'upkeep' and 3600 or 120
  if tick == 5 or tick % period == 0 then SKIN:Bang('!CommandMeasure', 'mRun', 'Run') end
  local z = H.zones[1]
  local c = H.canvas(1)
  local A1, D, T = H.C.accent, H.C.dim, H.C.text
  local list, icon = rows()
  local ix = mirror and z.w - 34 or 34
  c:icon(icon, ix, 40, 56, A1, 1.6)
  local x0 = mirror and 0 or 76
  local w = z.w - 76
  for i, r in ipairs(list) do
    local y = 4 + (i - 1) * 25
    local col = r[3] and H.C.warn or A1
    c:poly({ { x0 + 4, y + 10 }, { x0 + 10, y + 4 }, { x0 + 16, y + 10 }, { x0 + 10, y + 16 } }, col, 1.4, 255, true)
    H.text(1, i * 2 - 1, x0 + 24, y + 1, r[1], { size = 9.5, weight = 700, color = D })
    H.text(1, i * 2, x0 + 62, y, r[2], { size = 10.5, font = H.fontNum, color = r[3] and H.C.warn or T, clip = w - 62 })
    H.hit(1, i, x0, y, w, 24, r[4])
  end
  c:flush()
  return 0
end

function OnClick(z, k)
  if kind == 'upkeep' then
    if k == 1 then SKIN:Bang('["ms-settings:windowsupdate"]')
    elseif k == 2 then SKIN:Bang('["wt.exe" "winget upgrade --all --interactive"]')
    else SKIN:Bang('["windowsdefender:"]') end
  else
    if k == 1 then SKIN:Bang('["wt.exe"]')
    elseif k == 2 then SKIN:Bang('["wt.exe" "ollama ps"]')
    else SKIN:Bang('["C:\\Program Files\\Tailscale\\tailscale-ipn.exe"]') end
  end
end
function OnRightClick(z, k) SKIN:Bang('!CommandMeasure', 'mRun', 'Run') end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
