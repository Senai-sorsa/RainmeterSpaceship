-- Mission clock (left side, where LAT / LON / ALT used to be): the next events from the calendars you
-- switched on in Control Center > DATA > CALENDARS. ShipCore fetches them (Data\calendar.txt).
-- Ring: countdown to the next event, filling as it gets close (last 24 h). Rows: when + title for the next three.
-- Colours: in progress = good, under 60 min = warn, under 15 min = alert, otherwise the theme colour.
local H
local SXR, SYR = 2560 / 1260, 1600 / 709
local tick = 0
local cal = { t = 0, n = 0, err = 0, ev = {}, ok = false }

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function load()
  local f = io.open(H.res .. 'Data\\calendar.txt', 'r')
  if not f then cal.ok = false; return end
  local c = { t = 0, n = 0, err = 0, ev = {}, ok = true }
  for line in f:lines() do
    local k, v = string.match(line, '^(%u) (.*)$')
    if k == 'T' then c.t = tonumber(v) or 0
    elseif k == 'C' then local a, b = string.match(v, '(%d+) (%d+)'); c.n, c.err = tonumber(a) or 0, tonumber(b) or 0
    elseif k == 'E' then
      local s, e, ad, lab, title = string.match(v, '^(%d+)|(%d+)|(%d)|([^|]*)|(.*)$')
      if s then c.ev[#c.ev + 1] = { s = tonumber(s), e = tonumber(e), allday = ad == '1', label = lab, title = title } end
    end
  end
  f:close()
  cal = c
end

local function countdown(sec)
  sec = math.max(0, math.floor(sec))
  if sec < 600 then return string.format('%d:%02d', math.floor(sec / 60), sec % 60) end
  if sec < 3600 then return string.format('%dM', math.floor(sec / 60)) end
  if sec < 86400 then return string.format('%dH%02d', math.floor(sec / 3600), math.floor(sec % 3600 / 60)) end
  return string.format('%dD', math.floor(sec / 86400))
end

local function when(e, now)
  local today = os.date('*t', now)
  local t = os.date('*t', e.s)
  local days = math.floor((os.time({ year = t.year, month = t.month, day = t.day, hour = 12 }) -
    os.time({ year = today.year, month = today.month, day = today.day, hour = 12 })) / 86400 + 0.5)
  if e.allday then return days == 0 and 'TODAY' or (days == 1 and 'TMRW' or string.upper(os.date('%a', e.s))) end
  if days == 0 then return os.date('%H:%M', e.s) end
  if days < 7 then return string.upper(os.date('%a', e.s)) end
  return os.date('%m/%d', e.s)
end

function Update()
  H.refreshTier()
  tick = tick + 1
  if tick % 5 == 1 then load() end
  local z = H.zones[1]
  local c = H.canvas(1)
  local A1, W, D = H.C.accent, H.C.white, H.C.dim
  local function X(rx) return (rx - 34) * SXR end
  local function Y(ry) return (ry - 220) * SYR end
  c:line(X(40), Y(228), X(226), Y(228), A1, 1.3, 220)
  c:dot(X(40), Y(228), 3, A1); c:dot(X(226), Y(228), 3, A1)
  local now = os.time()
  -- upcoming = not yet ended; the first one drives the ring
  local up = {}
  for _, e in ipairs(cal.ev) do if e.e > now then up[#up + 1] = e end end
  local first = up[1]
  local gx, gy, R = X(92), Y(256), 34
  local col, big, small = A1, '--', 'NO EVENTS'
  local frac = 0
  if first then
    local live = first.s <= now
    local dt = live and (first.e - now) or (first.s - now)
    if first.allday and not live then dt = first.s - now end
    if live then col, big, small = H.C.good, countdown(dt), first.allday and 'ALL DAY' or 'ENDS IN'
    else
      col = dt < 900 and H.C.alert or (dt < 3600 and H.C.warn or A1)
      big, small = countdown(dt), 'T-MINUS'
    end
    frac = live and 1 or H.clamp(1 - dt / 86400, 0, 1)
  elseif not cal.ok then small = 'NOT SET UP' end
  -- ring: faint full circle, tick marks every hour, progress arc from the top
  c:circle(gx, gy, R, D, 1, 120)
  for i = 0, 23 do
    local a = math.rad(i * 15 - 90)
    local r0 = i % 6 == 0 and R - 7 or R - 4
    c:hair(gx + r0 * math.cos(a), gy + r0 * math.sin(a), gx + R * math.cos(a), gy + R * math.sin(a), A1, 1, i % 6 == 0 and 170 or 90)
  end
  if frac > 0.003 then c:arc(gx, gy, R + 5, -90, -90 + 360 * frac, col, 2.4, 240) end
  H.text(1, 7, gx, gy - 3, big, { size = string.len(big) > 4 and 8 or 9.5, weight = 700, align = 'CenterCenter', color = col, font = H.fontNum })
  H.text(1, 8, gx, gy + 13, small, { size = 3.6, weight = 700, align = 'CenterCenter', color = D, glow = false })
  -- rows: when (right-aligned) + title
  for i = 1, 3 do
    local y = Y(({ 242, 253, 264 })[i])
    local e = up[i]
    local lab, title, lc, tc
    if e then
      lab, title = when(e, now), string.upper(e.title)
      local live = e.s <= now
      lc = live and H.C.good or (i == 1 and col or A1)
      tc = i == 1 and W or { 160, 185, 200 }
      if live and not e.allday then lab = 'NOW' end
    elseif i == 1 then
      lab, title, lc, tc = cal.ok and 'CLEAR' or 'SETUP', cal.ok and (cal.n == 0 and 'NO CALENDARS ON' or 'NO EVENTS IN 3 WEEKS') or 'CONTROL CENTER > DATA', A1, D
    end
    if lab then
      H.text(1, i * 2 - 1, X(152), y, lab, { size = 6.4, weight = 700, align = 'RightCenter', color = lc, font = H.fontNum })
      H.text(1, i * 2, X(158), y, title, { size = 6.4, weight = 700, align = 'LeftCenter', color = tc, clip = X(228) - X(158) })
    else H.hideText(1, i * 2 - 1); H.hideText(1, i * 2) end
  end
  local function ly(rx, base) return base - (10 / 196 - 4 / 187) * (rx - 34) * SYR end
  c:line(X(35), ly(35, z.h - 9), X(222), ly(222, z.h - 9), A1, 1.3, 220)
  c:line(X(35), ly(35, z.h - 2.5), X(222), ly(222, z.h - 2.5), A1, 1, 160)
  if tick < 3 or tick % 5 == 0 then
    local tip
    if first then
      tip = string.format('%s   %s   %s', first.title, os.date(first.allday and '%a %d %b' or '%a %d %b  %H:%M', first.s), first.label)
    else tip = cal.ok and 'Mission clock - no upcoming events' or 'Mission clock - add calendars in Control Center > DATA' end
    if cal.err > 0 then tip = tip .. '   (' .. cal.err .. ' calendar feed failed)' end
    H.hit(1, 1, 0, 0, z.w, z.h, tip)
  end
  c:flush()
  return first and (first.s - now) or -1
end

function OnClick(z, k) SKIN:Bang('["https://calendar.google.com"]') end
function OnRightClick(z, k)
  local f = io.open(H.res .. 'Data\\calendar.refresh', 'w')
  if f then f:write('1'); f:close() end
end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
