-- Audio reactor (the screen right of the globe; the systems dial on the left is its twin).
-- Built from the reference rings:
--   outer ring   rounded dashes = volume (lit dashes), gap at the bottom for the device + volume readout
--   top ticks    red segments = live peak meter
--   thick sweep  lower-left arc = live loudness (RMS)
--   thin rings   two concentric circles with small gaps
--   waveform     96 analyser bands wrapped into a mirrored radial ring (fine grain, bass at the bottom)
--   core         glowing centre that pulses with the sound - click to mute
--   glass wedge  on the right, holding previous / play / next
-- Scroll anywhere on it: volume. Click the bottom readout: next output device. Right-click: sound settings.
local H
local frame, disabled = 0, false
local NB = 96                 -- analyser bands (Audio.ini: Bands=96, mBand0..mBand95)
local sm = {}                 -- smoothed band levels
local rmsS, peakS, quiet = 0, 0, 0
local CX, CY = 94.5, 84
local R_DASH, R_TICK, R_SWEEP, R_RING1, R_RING2, R_W0, R_W1 = 70, 78, 58, 50, 45, 25, 41
local DASH_A0, DASH_SWEEP = 120, 300          -- outer ring from bottom-left round to bottom-right
local WEDGE = { -26, 26 }

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function media(key)
  SKIN:Bang('!SetOption', 'mMedia', 'Parameter', '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' .. SKIN:GetVariable('@') .. 'Scripts\\media.ps1" -Key ' .. key)
  SKIN:Bang('!UpdateMeasure', 'mMedia')
  SKIN:Bang('!CommandMeasure', 'mMedia', 'Run')
end

local function P(r, a) local ar = math.rad(a); return { CX + r * math.cos(ar), CY + r * math.sin(ar) } end

-- small media glyphs centred at x, y
local function glyph(c, kind, x, y, col)
  local s = 4.5
  if kind == 'prev' then
    c:poly({ { x + s * 0.4, y - s }, { x - s * 0.6, y }, { x + s * 0.4, y + s } }, col, 1.3, 255, true)
    c:line(x - s * 0.9, y - s, x - s * 0.9, y + s, col, 1.3)
  elseif kind == 'next' then
    c:poly({ { x - s * 0.4, y - s }, { x + s * 0.6, y }, { x - s * 0.4, y + s } }, col, 1.3, 255, true)
    c:line(x + s * 0.9, y - s, x + s * 0.9, y + s, col, 1.3)
  else
    c:poly({ { x - s * 0.5, y - s * 1.1 }, { x + s * 0.8, y }, { x - s * 0.5, y + s * 1.1 } }, col, 1.4, 255, true)
  end
end

local placed = false
local function placeHits(dev)
  local RR = R_TICK + 2
  local z = H.zones[1]
  -- H1_1: the whole disc (scroll = volume), drawn first so the others sit on top of it
  H.set('H1_1', 'X', string.format('%.2f', (z.x + CX - RR) * H.S))
  H.set('H1_1', 'Y', string.format('%.2f', (z.y + CY - RR) * H.S))
  H.set('H1_1', 'Shape', string.format('Ellipse %.2f,%.2f,%.2f | Fill Color 0,0,0,1 | StrokeWidth 0', RR * H.S, RR * H.S, RR * H.S))
  H.set('H1_1', 'TransformationMatrix', '1;0;0;1;0;0')
  H.set('H1_1', 'Hidden', '0')
  H.tips['1_1'] = { tip = 'Scroll: volume   right-click: sound settings', x0 = (z.x + CX - RR) * H.S, y0 = (z.y + CY - RR) * H.S,
    x1 = (z.x + CX + RR) * H.S, y1 = (z.y + CY + RR) * H.S }
  H.hit(1, 2, CX - 20, CY - 20, 40, 40, 'Mute / unmute')
  H.hit(1, 3, CX - 44, CY + 64, 88, 18, 'Output: ' .. dev .. '   click: next device')
  local ys = { -18, 0, 18 }
  local tips = { 'Previous', 'Play / pause', 'Next' }
  for i = 1, 3 do
    local p = P(62, ys[i])
    H.hit(1, 3 + i, p[1] - 8, p[2] - 8, 16, 16, tips[i])
  end
  placed = true
end

function Update()
  frame = frame + 1
  if frame % 20 == 1 then H.refreshTier() end
  -- cost control: 20 fps FULL, 10 LITE, 7 LOW, frozen STEALTH; idle (silence for 2 s) drops to 2 fps
  local every = ({ [0] = 1, [1] = 2, [2] = 3 })[H.tier] or 20
  if quiet > 40 then every = math.max(every, 10) end
  if H.tier >= 3 and not disabled then SKIN:Bang('!DisableMeasureGroup', 'Audio'); disabled = true
  elseif H.tier < 3 and disabled then SKIN:Bang('!EnableMeasureGroup', 'Audio'); disabled = false end
  if frame > 1 and every > 1 and frame % every ~= 0 then return 0 end
  local c = H.canvas(1)
  local A1, W, D, RED = H.C.accent, H.C.white, H.C.dim, H.C.hi
  local vol = H.val('mVol', 0)
  local muted = vol < 0
  if muted then vol = 0 end
  local dev = string.upper(H.sval('mVol', 'NO DEVICE'))
  dev = string.gsub(dev, '%s*%b()', '')
  if not placed or frame % 100 == 1 then placeHits(dev) end
  -- live levels
  local rms = disabled and 0 or H.clamp(H.val('mRMS', 0), 0, 1)
  local peak = disabled and 0 or H.clamp(H.val('mPeak', 0), 0, 1)
  rmsS = rmsS * 0.6 + rms * 0.4
  peakS = math.max(peak, peakS * 0.85)
  quiet = (rms < 0.01) and quiet + every or 0
  for i = 0, NB - 1 do
    local v = disabled and 0 or H.clamp(H.val('mBand' .. i, 0), 0, 1)
    sm[i] = (sm[i] or 0) * 0.5 + v * 0.5
  end
  -- glass wedge (right) behind everything
  c:sector(CX, CY, R_RING2 - 2, R_TICK + 4, WEDGE[1], WEDGE[2], A1, 26, 90)
  -- top tick scale: red peak meter
  local nt = 13
  for i = 0, nt - 1 do
    local a = 238 + i * 64 / (nt - 1)
    local lit = (i + 1) / nt <= peakS + 0.02
    local p0, p1 = P(R_TICK - 4, a), P(R_TICK + 2, a)
    if lit then c:line(p0[1], p0[2], p1[1], p1[2], RED, 2.2, 240)
    else c:hair(p0[1], p0[2], p1[1], p1[2], RED, 1.4, 90) end
  end
  -- outer ring: rounded dashes, lit for the volume
  local nd = 30
  local seg = R_DASH * math.rad(DASH_SWEEP) / nd
  c:dashArc(CX, CY, R_DASH, DASH_A0, DASH_A0 + DASH_SWEEP, D, 3.4, 120, seg * 0.42, seg * 0.58, true)
  local va = DASH_A0 + DASH_SWEEP * H.clamp(vol / 100, 0, 1)
  if not muted and vol > 0 then c:dashArc(CX, CY, R_DASH, DASH_A0, va, A1, 3.4, 245, seg * 0.42, seg * 0.58) end
  -- thick loudness sweep, lower-left (just left of the readout, round to the left)
  c:hairPoly(H.arcPts(CX, CY, R_SWEEP, R_SWEEP, 112, 212, 30), D, 80, 4)
  if rmsS > 0.01 then c:arc(CX, CY, R_SWEEP, 112, 112 + 100 * H.clamp(rmsS * 1.6, 0, 1), A1, 4.6, 250) end
  -- thin concentric rings with gaps
  for q = 0, 3 do c:arc(CX, CY, R_RING1, q * 90 + 12, q * 90 + 78, A1, 1, 140) end
  c:arc(CX, CY, R_RING2, 200, 340, W, 0.9, 110); c:arc(CX, CY, R_RING2, 20, 160, W, 0.9, 110)
  -- radial waveform: bass at the bottom, treble at the top, the left half mirrors the right
  local half = 72
  local lv = {}
  for j = 0, half - 1 do
    local f = j / (half - 1) * (NB - 1)
    local i0 = math.floor(f)
    local i1 = math.min(NB - 1, i0 + 1)
    local v = (sm[i0] or 0) * (1 - (f - i0)) + (sm[i1] or 0) * (f - i0)
    lv[j] = math.sqrt(H.clamp(v, 0, 1))
  end
  local function comb(side)
    local pts, edge = {}, {}
    for j = 0, half - 1 do
      local a = 90 - 180 * j / (half - 1)
      if side < 0 then a = 180 - a end
      local r1 = R_W0 + 1 + lv[j] * (R_W1 - R_W0 - 1)
      local pi, po = P(R_W0, a), P(r1, a)
      if j % 2 == 0 then pts[#pts + 1] = pi; pts[#pts + 1] = po else pts[#pts + 1] = po; pts[#pts + 1] = pi end
      edge[#edge + 1] = po
    end
    return pts, edge
  end
  local cr, er = comb(1)
  local cl, el = comb(-1)
  c:hairPoly(cr, H.mix(A1, W, 0.5), 150, 0.7)
  c:hairPoly(cl, H.mix(A1, W, 0.5), 150, 0.7)
  c:poly(er, W, 0.9, 200)
  c:poly(el, W, 0.9, 200)
  c:hairPoly(H.arcPts(CX, CY, R_W0, R_W0, 0, 360, 48), A1, 110, 1)
  -- glowing core, pulsing with the loudness; red X over it when muted
  local pulse = H.clamp(rmsS * 2.2, 0, 1)
  c:fillCircle(CX, CY, 20, H.C.panel, 170)
  if H.tier < 2 then
    for k = 3, 1, -1 do c:fillCircle(CX, CY, 6 + k * 4 + pulse * 4, H.mix(A1, W, 0.6), math.floor((20 + pulse * 40) / k)) end
  end
  c:dot(CX, CY, 3.2 + pulse * 2.5, muted and D or W)
  if muted then c:line(CX - 7, CY - 7, CX + 7, CY + 7, RED, 1.8); c:line(CX + 7, CY - 7, CX - 7, CY + 7, RED, 1.8) end
  -- media keys in the wedge
  local kinds = { 'prev', 'play', 'next' }
  local ys = { -18, 0, 18 }
  for i = 1, 3 do
    local p = P(62, ys[i])
    glyph(c, kinds[i], p[1], p[2], i == 2 and W or A1)
  end
  -- bottom readout in the ring's gap: device + volume
  H.text(1, 1, CX, CY + 66, string.format('%s', muted and 'MUTED' or (math.floor(vol + 0.5) .. '%')), { size = 6.4, weight = 700, align = 'CenterCenter', color = muted and RED or W, font = H.fontNum })
  H.text(1, 2, CX, CY + 77, dev, { size = 3.6, weight = 700, align = 'CenterCenter', color = D, glow = false, clip = 90 })
  H.text(1, 3, CX, CY - 64, 'AUDIO', { size = 3.6, weight = 700, align = 'CenterCenter', color = H.mix(A1, D, 0.4), glow = false })
  for k = 4, 12 do H.hideText(1, k) end
  c:flush()
  return vol
end

function OnClick(z, k)
  if k == 2 then SKIN:Bang('!CommandMeasure', 'mVol', 'ToggleMute')
  elseif k == 3 then SKIN:Bang('!CommandMeasure', 'mVol', 'ToggleNext')
  elseif k == 4 then media('prev') elseif k == 5 then media('playpause') elseif k == 6 then media('next') end
end
function OnRightClick(z, k) SKIN:Bang('["ms-settings:sound"]') end
function OnScroll(z, k, d) SKIN:Bang('!CommandMeasure', 'mVol', 'ChangeVolume ' .. (-2 * d)) end
function OnHover(z, k, on) end
