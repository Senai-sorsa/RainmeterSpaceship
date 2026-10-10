-- Systems dial (the square screen left of the globe, now a circle). Six controls around it:
--   left  BRT brightness  VOL volume  MIC microphone      right  PWR power mode  HZ refresh rate  GLW HUD glow
-- Click a label to select it (the glass wedge swings to it). Scroll anywhere on the dial to change the
-- selected control, or click a point on the ring to jump there. Stepped controls (power mode, refresh
-- rate) turn the ring into big segments, one per option.
-- Reading / setting: brightness + mic through ShipCore (Data\sys.txt), volume through Win7AudioPlugin,
-- power mode + refresh rate through Legion Toolkit (llt.ps1), glow = GlowAlpha in Settings.inc.
local H
local tick = 0
local sel = 1
local sys = { BRIGHT = -1, MIC = -1, MICMUTE = 0 }
local llt = {}
local pending = {}            -- control id -> { value, at }
local dirty = true
local CX, CY = 94.5, 86
local A0, SWEEP = 135, 270    -- ring runs from bottom-left, over the top, to bottom-right
local R_TICK, R_SEG, R_VAL, R_IN = 74, 64, 55, 46
local RR = R_TICK + 2         -- the ring's click disc

-- time in Update ticks (Update=100 ms); os.clock is CPU time, not wall time
local function now() return tick end

local function readSys()
  local f = io.open(H.res .. 'Data\\sys.txt', 'r')
  if not f then return end
  for line in f:lines() do
    local k, v = string.match(line, '^(%u+) (.+)$')
    if k then sys[k] = tonumber(v) or sys[k] end
  end
  f:close()
end

local function split(s)
  local t = {}
  for p in string.gmatch(s or '', '[^,]+') do t[#t + 1] = (string.gsub(p, '^%s*(.-)%s*$', '%1')) end
  return t
end

local POWER_NAMES = { quiet = 'QUIET', balance = 'BALANCED', performance = 'PERFORM', custom = 'CUSTOM', godmode = 'GOD MODE' }

local C = {}
local function buildControls()
  local modes = split(H.str('LltPowerModes', 'quiet,balance,performance'))
  local rates = split(H.str('LltRefreshRates', '60,165'))
  C = {
    { id = 'bright', label = 'BRT', name = 'BRIGHTNESS', ang = 205 },
    { id = 'vol', label = 'VOL', name = 'VOLUME', ang = 180 },
    { id = 'mic', label = 'MIC', name = 'MICROPHONE', ang = 155 },
    { id = 'power', label = 'PWR', name = 'POWER MODE', ang = -25, steps = modes },
    { id = 'hz', label = 'HZ', name = 'REFRESH', ang = 0, steps = rates },
    { id = 'glow', label = 'GLW', name = 'HUD GLOW', ang = 25 },
  }
end

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
  buildControls()
  sel = math.max(1, math.min(#C, math.floor(H.num('DialSel', 1))))
end

-- current value of a control: range -> 0..1 (nil = unavailable); stepped -> index (nil = unknown)
local function value(c)
  local p = pending[c.id]
  if p then return p.v end
  if c.id == 'bright' then return sys.BRIGHT >= 0 and sys.BRIGHT / 100 or nil
  elseif c.id == 'mic' then return sys.MIC >= 0 and sys.MIC / 100 or nil
  elseif c.id == 'vol' then local v = H.val('mVol', -1); return v >= 0 and v / 100 or (v < 0 and 0 or nil)
  elseif c.id == 'glow' then return H.clamp(H.num('GlowAlpha', 60) / 160, 0, 1)
  elseif c.id == 'power' then
    local cur = string.lower(llt.power or '')
    for i, m in ipairs(c.steps) do if string.find(cur, string.lower(m), 1, true) then return i end end
  elseif c.id == 'hz' then
    local cur = string.match(llt.refresh or '', '%d+')
    for i, r in ipairs(c.steps) do if cur == r then return i end end
  end
  return nil
end

local function frac(c, v)
  if v == nil then return 0 end
  if c.steps then return #c.steps > 1 and (v - 1) / (#c.steps - 1) or 1 end
  return v
end

local function runLlt(feature, val)
  local p = string.format('-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%sScripts\\llt.ps1" -Exe "%s" -Feature "%s" -Value "%s"',
    H.res, H.str('LltPath', ''), feature, val)
  SKIN:Bang('!SetOption', 'mLlt', 'Parameter', p)
  SKIN:Bang('!UpdateMeasure', 'mLlt')
  SKIN:Bang('!CommandMeasure', 'mLlt', 'Run')
end

local function apply(c, v)
  if c.id == 'bright' then SKIN:Bang('["' .. H.res .. 'Bin\\ShipCore.exe" brightness ' .. math.floor(v * 100 + 0.5) .. ']'); sys.BRIGHT = math.floor(v * 100 + 0.5)
  elseif c.id == 'mic' then SKIN:Bang('["' .. H.res .. 'Bin\\ShipCore.exe" mic ' .. math.floor(v * 100 + 0.5) .. ']'); sys.MIC = math.floor(v * 100 + 0.5)
  elseif c.id == 'vol' then SKIN:Bang('!CommandMeasure', 'mVol', 'SetVolume ' .. math.floor(v * 100 + 0.5))
  elseif c.id == 'glow' then
    H.save('GlowAlpha', math.floor(v * 160 + 0.5))
    SKIN:Bang('!RefreshGroup', 'Spaceship')
  elseif c.id == 'power' then runLlt(H.str('LltPowerFeature', 'power-mode'), c.steps[v]); llt.power = c.steps[v]
  elseif c.id == 'hz' then runLlt(H.str('LltRefreshFeature', 'refresh-rate'), c.steps[v]); llt.refresh = c.steps[v]
  end
end

-- change request: ranges wait until you stop scrolling (no flood of brightness calls), steps go at once
local function set(c, v)
  if c.steps then
    v = math.max(1, math.min(#c.steps, v))
    if v ~= value(c) then apply(c, v) end
    pending[c.id] = nil
  else
    pending[c.id] = { v = H.clamp(v, 0, 1), at = now() }
  end
  dirty = true
end

function OnLltDone()
  SKIN:Bang('!CommandMeasure', 'mStatus', 'Run', 'Spaceship\\Top\\Console')
end

local function label(c, v)
  if c.steps then
    if not v then return '--' end
    local s = c.steps[v]
    if c.id == 'hz' then return s .. ' HZ' end
    return POWER_NAMES[string.lower(s)] or string.upper(s)
  end
  if v == nil then return '--' end
  return string.format('%d%%', math.floor(v * 100 + 0.5))
end

local function draw()
  local c = H.canvas(1)
  local A1, W, D = H.C.accent, H.C.white, H.C.dim
  local cur = C[sel]
  local v = value(cur)
  local f = frac(cur, v)
  local avail = v ~= nil
  -- core glass
  c:fillCircle(CX, CY, R_IN - 4, H.C.panel, 120)
  -- tick scale across the top (the reference's short marks), lit up to the value
  local va = A0 + SWEEP * f
  for i = 0, 10 do
    local a = 225 + i * 9
    local lit = avail and a <= va
    local ar = math.rad(a)
    c:hair(CX + (R_TICK - 5) * math.cos(ar), CY + (R_TICK - 5) * math.sin(ar), CX + R_TICK * math.cos(ar), CY + R_TICK * math.sin(ar), lit and A1 or D, lit and 1.8 or 1.2, lit and 230 or 120)
  end
  -- segmented ring: 40 dashes for ranges, one segment per option for stepped controls
  local segs = cur.steps and #cur.steps or 40
  local seglen = R_SEG * math.rad(SWEEP) / segs
  local dash, gap = seglen * (cur.steps and 0.86 or 0.68), seglen * (cur.steps and 0.14 or 0.32)
  c:dashArc(CX, CY, R_SEG, A0, A0 + SWEEP, D, 4.5, 110, dash, gap, true)
  if avail then
    local litTo = cur.steps and (A0 + SWEEP * v / segs) or va
    if litTo > A0 + 0.5 then c:dashArc(CX, CY, R_SEG, A0, litTo, A1, 4.5, 240, dash, gap) end
  end
  -- thick value arc + track
  c:hairPoly(H.arcPts(CX, CY, R_VAL, R_VAL, A0, A0 + SWEEP, 60), D, 90, 2.5)
  if avail and f > 0.002 then c:arc(CX, CY, R_VAL, A0, va, H.mix(A1, W, 0.25), 3.2, 250) end
  if avail then
    local ar = math.rad(va)
    c:dot(CX + R_VAL * math.cos(ar), CY + R_VAL * math.sin(ar), 3, W)
  end
  -- inner thin ring with three gaps
  for q = 0, 2 do c:arc(CX, CY, R_IN, q * 120 + 100, q * 120 + 200, A1, 1, 150) end
  -- glass wedge pointing at the selected control
  c:sector(CX, CY, R_IN + 2, R_TICK + 6, cur.ang - 13, cur.ang + 13, A1, 34, 110)
  -- labels around the dial
  for i, k in ipairs(C) do
    local ar = math.rad(k.ang)
    local x, y = CX + 82 * math.cos(ar), CY + 82 * math.sin(ar)
    local on = i == sel
    H.text(1, i, x, y, k.label, { size = 5.4, weight = 700, align = 'CenterCenter', color = on and W or H.mix(A1, D, 0.3), alpha = on and 255 or 200, font = H.fontNum })
    H.hit(1, i + 3, x - 15, y - 9, 30, 18, k.name .. '   ' .. label(k, value(k)))
  end
  -- centre readout
  H.text(1, 7, CX, CY - 15, cur.name, { size = 3.8, weight = 700, align = 'CenterCenter', color = D, glow = false })
  H.text(1, 8, CX, CY + 2, label(cur, v), { size = cur.steps and 6.4 or 9.5, weight = 700, align = 'CenterCenter', color = avail and W or D, font = H.fontNum })
  local sub = ''
  if not avail then sub = (cur.id == 'power' or cur.id == 'hz') and 'NEEDS LEGION TOOLKIT' or (cur.id == 'bright' and 'NO PANEL CONTROL' or 'NO DATA')
  elseif cur.id == 'mic' and sys.MICMUTE == 1 then sub = 'MUTED'
  elseif pending[cur.id] then sub = 'SETTING...' end
  H.text(1, 9, CX, CY + 18, sub, { size = 3.4, weight = 700, align = 'CenterCenter', color = H.C.warn, glow = false })
  for k = 10, 14 do H.hideText(1, k) end
  c:flush()
end

function Update()
  tick = tick + 1
  if tick == 1 then PlaceRing(); for k = 1, 3 do H.hideHit(1, k) end end
  if tick % 10 == 1 then
    H.refreshTier()
    readSys()
    llt = H.llt()
    dirty = true
  end
  -- apply range changes ~0.4 s (4 ticks) after the last scroll step
  for _, c in ipairs(C) do
    local p = pending[c.id]
    if p and now() - p.at >= 4 and not p.sent then
      p.sent = true
      apply(c, p.v)
      p.at = now()
    elseif p and p.sent and now() - p.at > 30 then
      pending[c.id] = nil; dirty = true                 -- give the system a moment to report the new value
    end
  end
  if dirty then draw(); dirty = false end
  return sel
end

local function step(c, d)
  local v = value(c)
  if c.steps then set(c, (v or 1) + d)
  else set(c, (v or 0) + d * (c.id == 'glow' and 0.05 or 0.02)) end
end

-- hit ids: 4..9 = the six labels (Extra.inc, drawn above the ring), 10 = the ring disc (below them)
local function ctl(k) local i = k - 3; if i >= 1 and i <= #C then return i end end

function OnClick(z, k)
  local i = ctl(k)
  if i then
    sel = i
    H.save('DialSel', sel, H.res .. 'State.inc')
    dirty = true; Update()
  end
end

-- click on the ring: jump to that point (mouse position in percent of the ring's hit box)
function OnRing(px, py)
  local x0, y0, s = CX - RR, CY - RR, RR * 2
  local x, y = x0 + (tonumber(px) or 50) / 100 * s, y0 + (tonumber(py) or 50) / 100 * s
  local dx, dy = x - CX, y - CY
  local r = math.sqrt(dx * dx + dy * dy)
  if r < R_IN - 4 then return end
  local a = math.deg(math.atan2(dy, dx))
  while a < A0 do a = a + 360 end
  local f = (a - A0) / SWEEP
  if f > 1 then f = (f - 1) * SWEEP < (360 - SWEEP) / 2 and 1 or 0 end
  local c = C[sel]
  if c.steps then set(c, math.floor(f * (#c.steps - 1) + 0.5) + 1) else set(c, f) end
  Update()
end

function OnRightClick(z, k)
  local c = C[ctl(k) or sel]
  if c.id == 'vol' or c.id == 'mic' then SKIN:Bang('["ms-settings:sound"]')
  elseif c.id == 'bright' or c.id == 'hz' then SKIN:Bang('["ms-settings:display"]')
  elseif c.id == 'power' then SKIN:Bang('["ms-settings:powersleep"]')
  else SKIN:Bang('!ActivateConfig', 'Spaceship\\Overlay\\Control', 'Control.ini') end
end

function OnScroll(z, k, d)
  local c = C[ctl(k) or sel]
  step(c, -d)
  Update()
end

function OnHover(z, k, on) end

-- the ring's click / scroll disc (H1_10 in Extra.inc): a circle, so the labels just outside it stay clickable
function PlaceRing()
  local z = H.zones[1]
  H.set('H1_10', 'X', string.format('%.2f', (z.x + CX - RR) * H.S))
  H.set('H1_10', 'Y', string.format('%.2f', (z.y + CY - RR) * H.S))
  H.set('H1_10', 'Shape', string.format('Ellipse %.2f,%.2f,%.2f | Fill Color 0,0,0,1 | StrokeWidth 0', RR * H.S, RR * H.S, RR * H.S))
  H.set('H1_10', 'Hidden', '0')
  H.tips['1_10'] = { tip = 'Scroll: change   click the ring: jump to a value   right-click: Windows settings',
    x0 = (z.x + CX - RR) * H.S, y0 = (z.y + CY - RR) * H.S, x1 = (z.x + CX + RR) * H.S, y1 = (z.y + CY + RR) * H.S }
end
