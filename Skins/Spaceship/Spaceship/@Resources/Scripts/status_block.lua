-- Small "ship + counters" blocks at the bottom of each side column (230 x 80).
-- Kind=upkeep : Windows updates (diamond) + Gmail unread (envelope, from ShipCore) - winget count in the caption
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

-- Gmail unread count from ShipCore (Data\mail.txt): number, or nil + reason
local mail = { n = nil, why = 'starting' }
local function readMail()
  local f = io.open(H.res .. 'Data\\mail.txt', 'r')
  if not f then mail = { n = nil, why = 'helper not running' }; return end
  local m = { n = nil, why = 'no data' }
  for line in f:lines() do
    local k, v = string.match(line, '^(%u+) ?(.*)$')
    if k == 'UNREAD' then m.n = tonumber(v); m.why = nil
    elseif k == 'ERR' then m.why = v
    elseif k == 'OFF' then m.why = 'off' end
  end
  f:close()
  mail = m
end

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
  local list = rows()
  -- reference: pink diamond + count, cyan gear + count
  local function n2(v) local x = tonumber(v); if not x or x < 0 then return '-' end; return tostring(x) end
  local r1 = kind == 'upkeep' and { n2(vals[1]), list[1][4] } or { n2(vals[1]), list[1][4] }
  local r2 = kind == 'upkeep' and { n2(vals[2]), list[2][4] } or { n2(vals[2]), list[2][4] }
  local isMail = kind == 'upkeep'
  if isMail then
    if tick % 5 == 1 then readMail() end
    r1[2] = r1[2] .. '   winget upgrades ' .. n(vals[2])
    if mail.n then r2 = { tostring(mail.n), mail.n == 1 and '1 unread Gmail message - click: open Gmail' or (mail.n .. ' unread Gmail messages - click: open Gmail') }
    elseif mail.why == 'off' then r2 = { '-', 'Gmail not set up - Control Center > DATA > GMAIL' }
    else r2 = { '!', 'Gmail: ' .. (mail.why or '?') .. '   (Control Center > DATA > GMAIL)' } end
  end
  local x0 = kind == 'upkeep' and 4 or z.w - 40
  local y1, y2 = z.h * 0.33, z.h * 0.72
  c:poly({ { x0 + 8, y1 - 8 }, { x0 + 16, y1 }, { x0 + 8, y1 + 8 }, { x0, y1 } }, H.C.hi, 1.8, 255, true)
  c:dot(x0 + 8, y1, 2.5, H.C.hi)
  H.text(1, 1, x0 + 22, y1, r1[1], { size = 8, weight = 700, align = 'LeftCenter', color = H.C.hi })
  if isMail then
    -- envelope: brighter when there is unread mail
    local mc = (mail.n or 0) > 0 and H.C.white or H.C.accent
    c:icon('mail', x0 + 8, y2, 18, mc, 1.3)
    H.text(1, 2, x0 + 22, y2, r2[1], { size = 8, weight = 700, align = 'LeftCenter', color = mail.why and mail.why ~= 'off' and H.C.warn or mc })
  else
    c:icon('gear', x0 + 8, y2, 18, H.C.accent, 1.3)
    H.text(1, 2, x0 + 22, y2, r2[1], { size = 8, weight = 700, align = 'LeftCenter', color = H.C.accent })
  end
  local extra = kind == 'upkeep' and ('   AV ' .. (vals[3] or '--') .. ' ' .. (vals[4] or '')) or ('   Tailscale ' .. (vals[3] or '--'))
  H.hit(1, 1, 0, 0, z.w, z.h / 2, r1[2] .. extra)
  H.hit(1, 2, 0, z.h / 2, z.w, z.h / 2, r2[2])
  c:flush()
  return 0
end

function OnClick(z, k)
  if kind == 'upkeep' then
    if k == 1 then SKIN:Bang('["ms-settings:windowsupdate"]')
    elseif k == 2 then SKIN:Bang('["https://mail.google.com"]')
    else SKIN:Bang('["windowsdefender:"]') end
  else
    if k == 1 then SKIN:Bang('["wt.exe"]')
    elseif k == 2 then SKIN:Bang('["wt.exe" "ollama ps"]')
    else SKIN:Bang('["C:\\Program Files\\Tailscale\\tailscale-ipn.exe"]') end
  end
end
function OnRightClick(z, k)
  if kind == 'upkeep' and k == 2 then
    local f = io.open(H.res .. 'Data\\mail.refresh', 'w'); if f then f:write('1'); f:close() end
  else SKIN:Bang('!CommandMeasure', 'mRun', 'Run') end
end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
