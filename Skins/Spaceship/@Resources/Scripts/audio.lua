-- Audio screen (B_audio, 260 x 168). Reference: the "TARGET SAR" waveform screen.
local H
local frame, disabled = 0, false

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function media(key)
  SKIN:Bang('!SetOption', 'mMedia', 'Parameter', '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' .. SKIN:GetVariable('@') .. 'Scripts\\media.ps1" -Key ' .. key)
  SKIN:Bang('!UpdateMeasure', 'mMedia')
  SKIN:Bang('!CommandMeasure', 'mMedia', 'Run')
end

function Update()
  frame = frame + 1
  if frame % 20 == 1 then H.refreshTier() end
  -- waveform cost control: 20 fps at FULL, 5 fps LITE, frozen at LOW/STEALTH
  local every = ({ [0] = 1, [1] = 4 })[H.tier] or 20
  if H.tier >= 2 and not disabled then SKIN:Bang('!DisableMeasureGroup', 'Audio'); disabled = true
  elseif H.tier < 2 and disabled then SKIN:Bang('!EnableMeasureGroup', 'Audio'); disabled = false end
  if frame > 1 and frame % every ~= 0 and every > 1 then return 0 end
  local z = H.zones[1]
  local c = H.canvas(1)
  local A1, D, T = H.C.accent, H.C.dim, H.C.text
  -- header: device name (click cycles)
  c:fillPoly({ { 0, 0 }, { 90, 0 }, { 80, 18 }, { 0, 18 } }, H.C.panel, 160)
  H.text(1, 1, 6, 1, 'AUDIO', { size = 9.5, font = H.fontTitle, weight = 700, color = A1 })
  local dev = string.upper(H.sval('mVol', 'NO DEVICE'))
  H.text(1, 2, z.w - 4, 2, dev, { size = 8.5, align = 'RightTop', color = T, clip = z.w - 100 })
  H.hit(1, 1, 90, 0, z.w - 90, 20, 'Output: ' .. dev .. '  - click to switch device')
  -- waveform (mirrored bars about a centre line)
  local wx, wy, ww, wh = 4, 28, 168, 76
  local mid = wy + wh / 2
  c:hair(wx, mid, wx + ww, mid, D, 1, 160)
  local n = 24
  local bw = ww / n
  for i = 0, n - 1 do
    local v = disabled and 0.04 or H.clamp(H.val('mBand' .. i, 0), 0, 1)
    local h = math.max(1, v * wh / 2)
    c:fillRect(wx + i * bw + 1, mid - h, bw - 2, 2 * h, i % 6 == 0 and H.C.warn or A1, 200)
  end
  c:brackets(wx - 2, wy - 2, ww + 4, wh + 4, 8, D, 1, 200)
  -- volume arc
  local vol = H.val('mVol', 0)
  local muted = vol < 0
  if muted then vol = 0 end
  local cx, cy, r = 216, 66, 32
  c:arc(cx, cy, r, 135, 405, D, 3, 90)
  if vol > 0 then c:arc(cx, cy, r, 135, 135 + 270 * vol / 100, muted and H.C.alert or A1, 4) end
  H.text(1, 3, cx, cy, muted and 'MUTE' or string.format('%d', vol), { size = muted and 9 or 13, font = H.fontNum, align = 'CenterCenter', color = muted and H.C.alert or T })
  H.text(1, 4, cx, cy + 40, 'VOL', { size = 8, weight = 700, align = 'CenterCenter', color = D })
  H.hit(1, 2, cx - r, cy - r, 2 * r, 2 * r, 'Click: mute   Scroll: volume')
  -- media keys
  local by = 124
  local bx = { 30, 86, 142 }
  local lbl = { 'prev', 'playpause', 'next' }
  for i = 1, 3 do
    c:chamfer(bx[i] - 24, by, 48, 30, 6, D, 1.2, 255, 120)
    H.hit(1, 2 + i, bx[i] - 24, by, 48, 30, lbl[i])
  end
  c:poly({ { 36, by + 8 }, { 24, by + 15 }, { 36, by + 22 } }, A1, 1.6, 255, true); c:line(22, by + 8, 22, by + 22, A1, 1.6)
  c:poly({ { 80, by + 8 }, { 94, by + 15 }, { 80, by + 22 } }, A1, 1.6, 255, true)
  c:poly({ { 136, by + 8 }, { 148, by + 15 }, { 136, by + 22 } }, A1, 1.6, 255, true); c:line(150, by + 8, 150, by + 22, A1, 1.6)
  H.text(1, 5, z.w - 4, by + 15, 'MEDIA', { size = 8.5, weight = 700, align = 'RightCenter', color = D })
  H.hit(1, 6, 180, by, 76, 30, 'Mute toggle')
  c:flush()
  return vol
end

function OnClick(z, k)
  if k == 1 then SKIN:Bang('!CommandMeasure', 'mVol', 'ToggleNext')
  elseif k == 2 or k == 6 then SKIN:Bang('!CommandMeasure', 'mVol', 'ToggleMute')
  elseif k == 3 then media('prev') elseif k == 4 then media('playpause') elseif k == 5 then media('next') end
end
function OnRightClick(z, k) SKIN:Bang('["ms-settings:sound"]') end
function OnScroll(z, k, d)
  if k == 2 then SKIN:Bang('!CommandMeasure', 'mVol', 'ChangeVolume ' .. (-5 * d)) end
end
function OnHover(z, k, on) end
