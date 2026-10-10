-- Flight HUD (reference: speed ladders 350/360/370, diamond pipper, [ <50 bracket, M/S THR 50).
-- Left ladder = S&P 500 change today (%, Yahoo Finance every 5 min while the market is open), right ladder = GPU (clock if HWiNFO maps it, else load %),
-- the < pointer on the bracket = CPU load. Ladders scroll smoothly at 20 fps on the FULL tier.
local H
local frame = 0
local s = { cpu = nil, gpu = nil, load = nil, spx = nil }
local spx = { price = nil, prev = nil, open = false, t = 0 }
local SXR, SYR = 2560 / 1260, 1600 / 709
-- zone 484..776 is centred on the screen axis (x = 630); the pipper sits on it
local function X(rx) return (rx - 484) * SXR end
local function Y(ry) return (ry - 256) * SYR end  -- reference rows; the zone itself now sits 32 px higher

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function ease(old, new, k) if not old then return new end; return old + (new - old) * k end

-- Yahoo chart JSON for ^GSPC (HUD.ini mSPX): price, previous close, today's regular session
function OnSPX()
  local j = H.sval('mSPX', '')
  local price = tonumber(string.match(j, '"regularMarketPrice"%s*:%s*([%d%.]+)'))
  local prev = tonumber(string.match(j, '"chartPreviousClose"%s*:%s*([%d%.]+)')) or tonumber(string.match(j, '"previousClose"%s*:%s*([%d%.]+)'))
  local reg = string.match(j, '"regular"%s*:%s*(%b{})') or ''
  local rs, re = string.match(reg, '"start"%s*:%s*(%d+)'), string.match(reg, '"end"%s*:%s*(%d+)')
  if price and prev and prev > 0 then
    spx.price, spx.prev, spx.t = price, prev, os.time()
    local now = os.time()
    spx.open = (rs and re and now >= tonumber(rs) and now <= tonumber(re)) and true or false
    -- fetch every 5 min while the market is open, hourly while it's closed
    SKIN:Bang('!SetOption', 'mSPX', 'UpdateRate', spx.open and '6000' or '72000')
  end
end

-- ladder: x = rail x, side -1 labels left / +1 labels right, v = smoothed value, step = label step, ppu = px per unit
local function ladder(c, ti, x, side, v, step, ppu, fmt, col, centreFmt, signed, sizes)
  sizes = sizes or { 7.6, 12 }
  local A1, W = col or H.C.accent, H.C.white
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
  H.text(1, ti, lx, Y(268), string.format(fmt, v + step), { size = sizes[1], weight = 700, align = al, color = A1 })
  H.text(1, ti + 1, side < 0 and X(512) or X(748), mid, string.format(centreFmt or fmt, v), { size = sizes[2], weight = 700, align = al, color = A1, font = sizes[3] })
  H.text(1, ti + 2, lx, Y(353), string.format(fmt, signed and (v - step) or math.max(0, v - step)), { size = sizes[1], weight = 700, align = al, color = A1 })
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
  -- S&P 500: day change in percent
  local pct = (spx.price and spx.prev) and ((spx.price - spx.prev) / spx.prev * 100) or nil
  local scol = A1
  s.spx = ease(s.spx, pct or 0, k)
  -- the value is wider than the old 3-digit clock, so this tape uses a smaller, narrow-number face
  local sz = { 6.4, 7.2, H.fontNum }
  if pct then ladder(c, 1, X(527), -1, s.spx, 0.5, 60, '%+.1f', scol, '%+.2f%%', true, sz)
  else ladder(c, 1, X(527), -1, 0, 0.5, 60, '%+.1f', scol, '--', true, sz) end
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
  H.text(1, 8, X(525), Y(381), 'SPX', { size = 7, weight = 700, align = 'RightCenter', color = A1 })
  if pct and not spx.open then H.text(1, 10, X(525), Y(371), 'CLOSED', { size = 4.6, weight = 700, align = 'RightCenter', color = H.C.dim, glow = false })
  else H.hideText(1, 10) end
  H.text(1, 9, X(525), Y(391), string.format('THR %.0f', s.load), { size = 7, weight = 700, align = 'RightCenter', color = A1 })
  for t = 11, 24 do H.hideText(1, t) end
  if frame < 3 or frame % 100 == 0 then
    H.hit(1, 1, X(600), Y(290), X(660) - X(600), Y(332) - Y(290), 'GPU (right ladder), CPU load (pointer)')
    H.hit(1, 2, X(486), Y(258), X(540) - X(486), Y(395) - Y(258), pct and string.format('S&P 500  %s  %+.2f%% today  (previous close %s)   %s   click: chart',
      string.format('%.1f', spx.price), pct, string.format('%.1f', spx.prev), spx.open and 'market open' or 'market closed') or 'S&P 500 - waiting for data')
  end
  c:flush()
  return 0
end

function OnClick(z, k)
  if k == 2 then SKIN:Bang('["https://finance.yahoo.com/quote/%5EGSPC"]') else SKIN:Bang('["taskmgr.exe"]') end
end
function OnRightClick(z, k) end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
