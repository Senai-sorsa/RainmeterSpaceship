-- Flight HUD (C_hud, 520 x 245). Reference: speed ladders 350-370, diamond pipper, "M/S THR 50".
local H
local launchName, launchT = nil, nil
local smooth = { cpu = nil, gpu = nil }

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function utcToLocal(y, mo, d, h, mi, s)
  local t = os.time({ year = y, month = mo, day = d, hour = h, min = mi, sec = s })
  local now = os.time()
  local offset = os.difftime(now, os.time(os.date('!*t', now)))
  return t + offset
end

function OnLaunch()
  local s = H.sval('mLaunch', '')
  local name = string.match(s, '"name":%s*"([^"]+)"')
  local y, mo, d, h, mi, se = string.match(s, '"net":%s*"(%d+)-(%d+)-(%d+)T(%d+):(%d+):(%d+)')
  if name and y then
    launchName = string.upper(name)
    launchT = utcToLocal(tonumber(y), tonumber(mo), tonumber(d), tonumber(h), tonumber(mi), tonumber(se))
  end
end

-- vertical tape: value v, units per pixel, label spacing; returns next text index
local function tape(c, ti, x, top, bot, v, perPx, step, fmt, side, col)
  local mid = (top + bot) / 2
  local D = H.C.dim
  c:line(x, top, x, bot, col, 1.6)
  local lo = v - (mid - top) * perPx
  local first = math.ceil(lo / (step / 2)) * (step / 2)
  local k = first
  local used = 0
  while true do
    local y = mid - (k - v) / perPx
    if y < top then break end
    if y <= bot then
      local major = math.abs((k / step) - math.floor(k / step + 0.5)) < 1e-6
      local len = major and 14 or 8
      c:hair(x, y, x + side * len, y, col, 1.4, major and 255 or 160)
      if major and math.abs(y - mid) > 22 and used < 5 then
        used = used + 1
        H.text(1, ti, x + side * 20, y, string.format(fmt, k), { size = 9, font = H.fontNum, align = side < 0 and 'RightCenter' or 'LeftCenter', color = D })
        ti = ti + 1
      end
    end
    k = k + step / 2
  end
  for j = used + 1, 5 do H.hideText(1, ti); ti = ti + 1 end
  -- value box with pointer (reference: "< 50")
  local bx = side < 0 and x - 70 or x + 16
  c:fillRect(bx, mid - 13, 54, 26, H.C.panel, 200)
  c:rect(bx, mid - 13, 54, 26, col, 1.6)
  c:poly(side < 0 and { { x - 16, mid - 6 }, { x - 6, mid }, { x - 16, mid + 6 } } or { { x + 16, mid - 6 }, { x + 6, mid }, { x + 16, mid + 6 } }, col, 1.6)
  return ti, bx
end

function Update()
  H.refreshTier()
  local z = H.zones[1]
  local c = H.canvas(1)
  local A1, D, T = H.C.accent, H.C.dim, H.C.text
  local cx = z.w / 2
  -- clock box (top centre) + chevron
  c:rect(cx - 64, 0, 128, 30, A1, 1.6)
  H.text(1, 1, cx, 15, H.sval('mTime', '--:--:--'), { size = 14, font = H.fontNum, align = 'CenterCenter', color = T })
  c:poly({ { cx - 8, 40 }, { cx, 33 }, { cx + 8, 40 } }, A1, 1.6)
  -- pitch lines + diamond pipper
  local py = 122
  for _, dy in ipairs({ -48, 48 }) do
    c:line(cx - 82, py + dy, cx - 30, py + dy, A1, 1.6)
    c:line(cx + 30, py + dy, cx + 82, py + dy, A1, 1.6)
    c:line(cx - 82, py + dy, cx - 82, py + dy + (dy < 0 and 8 or -8), A1, 1.6)
    c:line(cx + 82, py + dy, cx + 82, py + dy + (dy < 0 and 8 or -8), A1, 1.6)
  end
  c:line(cx - 150, py, cx - 64, py, A1, 1.4)
  c:line(cx + 64, py, cx + 150, py, A1, 1.4)
  c:poly({ { cx, py - 9 }, { cx + 9, py }, { cx, py + 9 }, { cx - 9, py } }, A1, 1.8, 255, true)
  c:line(cx - 34, py, cx - 10, py, A1, 1.8); c:line(cx + 10, py, cx + 34, py, A1, 1.8); c:line(cx, py - 10, cx, py - 26, A1, 1.8)
  -- CPU clock tape (left)
  local mhz = H.num('CpuBaseMHz', 2000) * H.val('mCpuPerf', 100) / 100
  smooth.cpu = smooth.cpu and (smooth.cpu * 0.6 + mhz * 0.4) or mhz
  local ti = 2
  local bxL
  ti, bxL = tape(c, ti, 96, 42, 202, smooth.cpu / 1000, 0.012, 0.5, '%.1f', -1, A1)
  H.text(1, ti, bxL + 27, py, string.format('%.2f', smooth.cpu / 1000), { size = 11, font = H.fontNum, align = 'CenterCenter', color = T }); ti = ti + 1
  H.text(1, ti, 96, 36, 'CPU GHZ', { size = 8.5, weight = 700, align = 'CenterBottom', color = D }); ti = ti + 1
  -- GPU tape (right): core clock from HWiNFO if mapped, else load %
  local gclk = H.hw('mHwGpuClock')
  local gv, per, step, fmt, lab, box
  if gclk then gv, per, step, fmt, lab, box = gclk, 6, 250, '%.0f', 'GPU MHZ', string.format('%.0f', gclk)
  else local g = H.clamp(H.val('mGPU', 0), 0, 100); gv, per, step, fmt, lab, box = g, 0.5, 20, '%.0f', 'GPU %', string.format('%.0f', g) end
  smooth.gpu = smooth.gpu and (smooth.gpu * 0.6 + gv * 0.4) or gv
  local bxR
  ti, bxR = tape(c, ti, z.w - 96, 42, 202, smooth.gpu, per, step, fmt, 1, A1)
  H.text(1, ti, bxR + 27, py, box, { size = 11, font = H.fontNum, align = 'CenterCenter', color = T }); ti = ti + 1
  H.text(1, ti, z.w - 96, 36, lab, { size = 8.5, weight = 700, align = 'CenterBottom', color = D }); ti = ti + 1
  -- network variometer (between right tape and edge): arrow length = up/down rate
  local down, up = H.val('mNetIn', 0), H.val('mNetOut', 0)
  local function vlen(b) return H.clamp(math.log(1 + b / 1024) / math.log(1 + 100 * 1024), 0, 1) * 70 end
  local vx = z.w - 8
  c:hair(vx - 6, py, vx + 6, py, D, 1, 200)
  c:line(vx, py, vx, py - vlen(up), H.C.good, 2)
  c:line(vx, py, vx, py + vlen(down), A1, 2)
  -- readouts (reference "M/S  THR 50")
  local fan = H.hw('mHwFan1')
  H.text(1, ti, 40, 214, fan and string.format('FAN %d', fan) or 'FAN --', { size = 10, font = H.fontNum, color = A1 }); ti = ti + 1
  H.text(1, ti, 40, 230, string.format('THR %d', H.val('mCPU', 0)), { size = 10, font = H.fontNum, color = A1 }); ti = ti + 1
  H.text(1, ti, z.w - 40, 214, 'DN ' .. H.rate(down), { size = 9.5, font = H.fontNum, align = 'RightTop', color = A1 }); ti = ti + 1
  H.text(1, ti, z.w - 40, 230, 'UP ' .. H.rate(up), { size = 9.5, font = H.fontNum, align = 'RightTop', color = H.C.good }); ti = ti + 1
  -- date + next launch countdown (bottom centre)
  H.text(1, ti, cx, 206, string.upper(H.sval('mDate', '')), { size = 10, weight = 700, align = 'CenterTop', color = D }); ti = ti + 1
  local line = 'NEXT LAUNCH: --'
  if launchT then
    local dt = launchT - os.time()
    if dt > 0 then
      line = string.format('T-%dD %02d:%02d:%02d  %s', math.floor(dt / 86400), math.floor(dt % 86400 / 3600), math.floor(dt % 3600 / 60), dt % 60, launchName)
    else line = 'LIFTOFF  ' .. launchName end
  end
  H.text(1, ti, cx, 226, line, { size = 9, font = H.fontNum, align = 'CenterTop', color = H.C.warn, clip = 300 }); ti = ti + 1
  for k = ti, 30 do H.hideText(1, k) end
  H.hit(1, 1, cx - 64, 0, 128, 30, 'Click: open Clock / alarms')
  c:flush()
  return 0
end

function OnClick(z, k) SKIN:Bang('["ms-clock:"]') end
function OnRightClick(z, k) SKIN:Bang('!CommandMeasure', 'mLaunch', 'Update') end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
