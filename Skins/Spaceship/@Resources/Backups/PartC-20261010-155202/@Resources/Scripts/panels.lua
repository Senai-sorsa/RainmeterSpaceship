-- The two tilted screens at the bottom of the dash (reference: the small angled list screens). The zones are
-- the upper part of each pane, sheared with it, so the text sits on the screen at the screen's angle.
-- Left : pilot (Windows user), date, time, week, year progress, UTC offset, boot time, uptime, idle time.
-- Right: condensed ship card - host, Windows, CPU, GPU, memory, display + refresh rate, uptime (the IP and
--        Wi-Fi live in the network block now) - and a TERMINAL button: left-click Windows Terminal,
--        right-click PowerShell.
local H

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function rows(zi, list, height, c)
  local z = H.zones[zi]
  local own = c == nil
  c = c or H.canvas(zi)
  local A1, W = H.C.accent, H.C.white
  local rh = (height or z.h) / (#list + 0.3)
  for i, r in ipairs(list) do
    local y = rh * (i - 0.35)
    if i < #list then c:hair(6, y + rh * 0.5, z.w - 6, y + rh * 0.5, A1, 1, 45) end
    H.text(zi, i * 2 - 1, 6, y, r[1], { size = 3.0, weight = 700, align = 'LeftCenter', color = A1, alpha = 220, glow = false })
    H.text(zi, i * 2, z.w - 5, y, r[2], { size = 3.3, weight = 700, align = 'RightCenter', color = r[3] or W, font = H.fontNum, clip = z.w * 0.66 })
  end
  for k = #list * 2 + 1, 18 do H.hideText(zi, k) end
  if own then c:flush() end
end

-- week of the year (Monday weeks, like the ISO number) from the portable %j / %w fields only:
-- os.date with %V would crash on some Windows C runtimes
local function week()
  local t = os.date('*t')
  local wd = (t.wday + 5) % 7 + 1                         -- Monday = 1 ... Sunday = 7
  return math.max(1, math.floor((t.yday - wd + 10) / 7)), t.yday
end

local function utcOffset()
  local t = os.time()
  local u = os.date('!*t', t)
  u.isdst = os.date('*t', t).isdst
  local off = math.floor(os.difftime(t, os.time(u)) / 60 + 0.5)
  return string.format('UTC%s%02d:%02d', off < 0 and '-' or '+', math.floor(math.abs(off) / 60), math.abs(off) % 60)
end

local function span(sec)                                    -- 3D 04:20 / 4:20 H / 12:05 / 9 S
  sec = math.max(0, math.floor(sec))
  local d, h, m, s = math.floor(sec / 86400), math.floor(sec / 3600) % 24, math.floor(sec / 60) % 60, sec % 60
  if d > 0 then return string.format('%dD %02d:%02d', d, h, m) end
  if h > 0 then return string.format('%d:%02d H', h, m) end
  if m > 0 then return string.format('%d:%02d', m, s) end
  return s .. ' S'
end

function Update()
  H.refreshTier()
  local wk, yd = week()
  local yr = tonumber(os.date('%Y'))
  local ylen = (yr % 4 == 0 and (yr % 100 ~= 0 or yr % 400 == 0)) and 366 or 365
  local up = H.val('mUptime', 0)
  local boot = up > 0 and string.upper(os.date(up < 86400 and '%H:%M' or '%a %H:%M', os.time() - up)) or '--'
  local ram = H.val('mRamTotal', 0)
  rows(1, {
    { 'PILOT', string.upper(H.sval('mUser', '--')) },
    { 'DATE', string.upper(os.date('%a %d %b')) },
    { 'TIME', os.date('%H:%M:%S'), H.C.hi },
    { 'WEEK', string.format('W%02d  D%03d', wk, yd) },
    { 'YEAR', string.format('%d  %.0f%%', yr, (yd - 1) / ylen * 100) },
    { 'ZONE', utcOffset() },
    { 'BOOT', boot },
    { 'UP', up > 0 and span(up) or '--' },
    { 'IDLE', span(H.val('mIdle', 0)) },
  })
  -- right screen: condensed card + terminal button
  local z2 = H.zones[2]
  local c2 = H.canvas(2)
  local hz = string.match(H.llt().refresh or '', '%d+')
  local res = H.str('SCREENAREAWIDTH', '?') .. 'x' .. H.str('SCREENAREAHEIGHT', '?')
  rows(2, {
    { 'HOST', string.upper(H.sval('mHost', '--')) },
    { 'OS', string.upper(H.str('OsName', 'WINDOWS')) },
    { 'CPU', H.str('CpuName', '--') },
    { 'GPU', H.str('DGpuName', '--') },
    { 'RAM', ram > 0 and string.format('%.0f GB', ram / 1073741824) or '--' },
    { 'DISP', hz and (res .. ' @' .. hz) or res },
    { 'UP', up > 0 and span(up) or '--', H.mix(H.C.accent, H.C.white, 0.4) },
  }, z2.h * 0.76, c2)
  local bx, by, bw, bh = 6, z2.h * 0.8, z2.w - 12, z2.h * 0.16
  c2:chamfer(bx, by, bw, bh, bh * 0.35, H.C.accent, 1.2, 230, 90)
  H.text(2, 15, bx + bw / 2, by + bh / 2, '>_ TERMINAL', { size = 3.6, weight = 700, align = 'CenterCenter', color = H.C.white, font = H.fontNum })
  c2:flush()
  H.hit(2, 2, bx, by, bw, bh, 'Click: Windows Terminal   right-click: PowerShell')
  H.hit(1, 1, 0, 0, H.zones[1].w, H.zones[1].h, 'Pilot, date and time, week, year, time zone, boot, uptime and idle time - click: Calendar')
  H.hit(2, 1, 0, 0, H.zones[2].w, H.zones[2].h * 0.78, H.str('DeviceModel', '') .. '   ' .. H.str('CpuName', '') .. ' ' .. H.str('CpuCores', '') .. 'C/' .. H.str('CpuThreads', '') .. 'T   ' ..
    H.str('DGpuName', '') .. ' + ' .. H.str('IGpuName', '') .. '   click: About')
  return 0
end

function OnClick(z, k)
  if z == 2 and k == 2 then SKIN:Bang('["wt.exe"]')
  elseif z == 2 then SKIN:Bang('["ms-settings:about"]')
  else SKIN:Bang('["outlookcal:"]') end
end
function OnRightClick(z, k)
  if z == 2 and k == 2 then SKIN:Bang('["powershell.exe"]') end
end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
