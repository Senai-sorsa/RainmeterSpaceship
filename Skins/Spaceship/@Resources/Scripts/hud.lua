-- Flight HUD (reference: speed ladders 350/360/370, diamond pipper, [ <50 bracket, M/S THR 50).
-- Left ladder = CPU clock (GHz), right ladder = GPU (clock if HWiNFO maps it, else load %),
-- the < pointer on the bracket = CPU load. Ladders scroll smoothly at 20 fps on the FULL tier.
local H
local frame = 0
local s = { cpu = nil, gpu = nil, load = nil }
local SXR, SYR = 2560 / 1260, 1600 / 709
-- zone 484..776 is centred on the screen axis (x = 630); the pipper sits on it
local function X(rx) return (rx - 484) * SXR end
local function Y(ry) return (ry - 256) * SYR end  -- reference rows; the zone itself now sits 32 px higher

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function ease(old, new, k) if not old then return new end; return old + (new - old) * k end

-- ladder: x = rail x, side -1 labels left / +1 labels right, v = smoothed value, step = label step, ppu = px per unit
local function ladder(c, ti, x, side, v, step, ppu, fmt)
  local A1, W = H.C.accent, H.C.white
  local top, bot, mid = Y(260), Y(362), Y(311)
  -- dashed rail scrolls with the value
  local spacing = 7
  local off = (v * ppu) % spacing
  local y = top + off
  while y <= bot do
    c:hair(x - 3, y, x + 3, y, A1, 1.4, 200)
    y = y + spacing
  end
  -- major tick at the centre line
  c:line(side < 0 and x - 26 or x, mid, side < 0 and x or x + 26, mid, A1, 2.2)
  local lx = side < 0 and X(510) or X(750)
  local al = side < 0 and 'RightCenter' or 'LeftCenter'
  H.text(1, ti, lx, Y(268), string.format(fmt, v + step), { size = 7.6, weight = 700, align = al, color = A1 })
  H.text(1, ti + 1, side < 0 and X(512) or X(748), mid, string.format(fmt, v), { size = 14, weight = 700, align = al, color = A1 })
  H.text(1, ti + 2, lx, Y(353), string.format(fmt, math.max(0, v - step)), { size = 7.6, weight = 700, align = al, color = A1 })
  c:line(x - 4, Y(268), x + 4, Y(268), A1, 1.4)
  c:line(x - 4, Y(353), x + 4, Y(353), A1, 1.4)
end

function Update()
  frame = frame + 1
  if frame % 20 == 1 then H.refreshTier() end
  local every = ({ [0] = 1, [1] = 3 })[H.tier] or 20
  if frame > 1 and every > 1 and frame % every ~= 0 then return 0 end
  local z = H.zones[1]
  local c = H.canvas(1)
  local A1, W = H.C.accent, H.C.white
  local k = H.tier == 0 and 0.12 or 1
  local mhz = H.num('CpuBaseMHz', 2000) * H.val('mCpuPerf', 100) / 100
  s.cpu = ease(s.cpu, mhz / 1000, k)
  local gclk = H.hw('mHwGpuClock')
  local gfmt, gstep, gppu
  if gclk then s.gpu = ease(s.gpu, gclk / 1000, k); gfmt, gstep, gppu = '%.2f', 0.25, 120
  else s.gpu = ease(s.gpu, H.clamp(H.val('mGPU', 0), 0, 100), k); gfmt, gstep, gppu = '%.0f', 10, 3 end
  s.load = ease(s.load, H.val('mCPU', 0), k)
  ladder(c, 1, X(527), -1, s.cpu, 0.5, 60, '%.1f')
  ladder(c, 4, X(733), 1, s.gpu, gstep, gppu, gfmt)
  -- bracket [ with the CPU-load pointer (reference: [ <50)
  local by0, by1 = Y(311), Y(362)
  c:poly({ { X(537.5), by0 }, { X(533.5), by0 }, { X(533.5), by1 }, { X(537.5), by1 } }, A1, 1.6)
  local py = by1 - (by1 - by0) * H.clamp(s.load / 100, 0, 1)
  c:poly({ { X(542), py - 5 }, { X(537.5), py }, { X(542), py + 5 } }, A1, 1.6, 255, true)
  H.text(1, 7, X(544), py, string.format('%.0f', s.load), { size = 7.5, weight = 700, align = 'LeftCenter', color = A1 })
  -- faint horizon + diamond pipper with corner ticks
  local cx, cy = X(630), Y(311)
  c:hair(cx, Y(268), cx, Y(296), A1, 1, 70)
  c:hair(cx, Y(326), cx, Y(354), A1, 1, 70)
  c:hair(X(567), cy, X(612), cy, A1, 1, 70)
  c:hair(X(648), cy, X(692), cy, A1, 1, 70)
  local d = 17 * (1 + (H.tier == 0 and math.sin(frame * 0.1) * 0.04 or 0))
  c:poly({ { cx, cy - d }, { cx + d, cy }, { cx, cy + d }, { cx - d, cy } }, A1, 2, 255, true)
  for _, p in ipairs({ { 0, -1 }, { 1, 0 }, { 0, 1 }, { -1, 0 } }) do
    c:line(cx + p[1] * (d + 2), cy + p[2] * (d + 2), cx + p[1] * (d + 9), cy + p[2] * (d + 9), A1, 1.6)
  end
  -- readout (reference: M/S  THR 50)
  H.text(1, 8, X(525), Y(381), 'GHZ', { size = 7, weight = 700, align = 'RightCenter', color = A1 })
  H.text(1, 9, X(525), Y(391), string.format('THR %.0f', s.load), { size = 7, weight = 700, align = 'RightCenter', color = A1 })
  for t = 10, 24 do H.hideText(1, t) end
  if frame < 3 then H.hit(1, 1, X(600), Y(290), X(660) - X(600), Y(332) - Y(290), 'CPU clock (left), GPU (right), CPU load (pointer)') end
  c:flush()
  return 0
end

function OnClick(z, k) SKIN:Bang('["taskmgr.exe"]') end
function OnRightClick(z, k) end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
