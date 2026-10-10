-- The two tilted screens at the bottom of the dash (reference: the small angled list screens). The zones are
-- the upper part of each pane, sheared with it, so the text sits on the screen at the screen's angle.
-- Left : pilot (Windows user), date, time, week, year progress, UTC offset, boot time, uptime, idle time.
-- Right: host, Windows, display, CPU threads, memory, OS bits, monitors, IP address, Wi-Fi network.
local H

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function rows(zi, list)
  local z = H.zones[zi]
  local c = H.canvas(zi)
  local A1, W = H.C.accent, H.C.white
  local rh = z.h / (#list + 0.3)
  for i, r in ipairs(list) do
    local y = rh * (i - 0.35)
    if i < #list then c:hair(6, y + rh * 0.5, z.w - 6, y + rh * 0.5, A1, 1, 45) end
    H.text(zi, i * 2 - 1, 6, y, r[1], { size = 3.0, weight = 700, align = 'LeftCenter', color = A1, alpha = 220, glow = false })
    H.text(zi, i * 2, z.w - 5, y, r[2], { size = 3.3, weight = 700, align = 'RightCenter', color = r[3] or W, font = H.fontNum, clip = z.w * 0.66 })
  end
  c:flush()
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
  local thr, ram = H.val('mThreads', 0), H.val('mRamTotal', 0)
  local bits, mons = H.val('mBits', 0), H.val('mMonitors', 0)
  local ip, ssid = H.sval('mIP', ''), H.sval('mSSID', '')
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
  rows(2, {
    { 'HOST', string.upper(H.sval('mHost', '--')) },
    { 'OS', string.upper(H.str('OsName', 'WINDOWS')) },
    { 'DISP', H.str('SCREENAREAWIDTH', '?') .. 'x' .. H.str('SCREENAREAHEIGHT', '?') },
    { 'CPU', thr > 0 and string.format('%d THREADS', thr) or '--' },
    { 'RAM', ram > 0 and string.format('%.0f GB', ram / 1073741824) or '--' },
    { 'ARCH', bits > 0 and string.format('%d-BIT', bits) or '--' },
    { 'MONS', mons > 0 and string.format('%d DISPLAY%s', mons, mons > 1 and 'S' or '') or '--' },
    { 'IP', (ip ~= '' and ip ~= '0.0.0.0') and ip or 'OFFLINE' },
    { 'WIFI', ssid ~= '' and string.upper(ssid) or 'NO WIFI' },
  })
  H.hit(1, 1, 0, 0, H.zones[1].w, H.zones[1].h, 'Pilot, date and time, week, year, time zone, boot, uptime and idle time - click: Calendar')
  H.hit(2, 1, 0, 0, H.zones[2].w, H.zones[2].h, 'Host, Windows, display, CPU, memory, OS bits, monitors, IP and Wi-Fi - click: Display settings')
  return 0
end

function OnClick(z, k) SKIN:Bang(z == 1 and '["outlookcal:"]' or '["ms-settings:display"]') end
function OnRightClick(z, k) end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
