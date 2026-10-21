-- Mission clock (left side, where LAT / LON / ALT used to be): the next events from the calendars you
-- switched on in Control Center > DATA > CALENDARS. ShipCore fetches them (Data\calendar.txt).
-- Rows: when + title for the next three; inside 24 h the 'when' is the clock time (10:24AM), after that the weekday, then the date.
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

-- 12-hour clock without a leading zero: 10:24AM, 9:05PM (built by hand so the system language cannot change AM/PM)
local function clock12(ts)
  local t = os.date('*t', ts)
  return string.format('%d:%02d%s', t.hour % 12 == 0 and 12 or t.hour % 12, t.min, t.hour < 12 and 'AM' or 'PM')
end

local function when(e, now)
  local today = os.date('*t', now)
  local t = os.date('*t', e.s)
  local days = math.floor((os.time({ year = t.year, month = t.month, day = t.day, hour = 12 }) -
    os.time({ year = today.year, month = today.month, day = today.day, hour = 12 })) / 86400 + 0.5)
  if e.allday then
    if days == 0 then return 'TODAY' end
  elseif e.s - now < 86400 then return clock12(e.s) end        -- under 24 h away: the time it is at
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
  -- upcoming = not yet ended; the first one sets the colour of its row
  local up = {}
  for _, e in ipairs(cal.ev) do if e.e > now then up[#up + 1] = e end end
  local first = up[1]
  local col = A1
  if first and first.s <= now then col = H.C.good
  elseif first then
    local dt = first.s - now
    col = dt < 900 and H.C.alert or (dt < 3600 and H.C.warn or A1)
  end
  H.hideText(1, 7); H.hideText(1, 8) -- the countdown ring is gone; its space goes to the rows
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
      H.text(1, i * 2 - 1, X(80), y, lab, { size = 5.4, weight = 700, align = 'RightCenter', color = lc, font = H.fontNum })
      H.text(1, i * 2, X(84), y, title, { size = 5.4, weight = 700, align = 'LeftCenter', color = tc, clip = X(228) - X(84) })
    else H.hideText(1, i * 2 - 1); H.hideText(1, i * 2) end
  end
  local function ly(rx, base) return base - (10 / 196 - 4 / 187) * (rx - 34) * SYR end
  c:line(X(35), ly(35, z.h - 9), X(222), ly(222, z.h - 9), A1, 1.3, 220)
  c:line(X(35), ly(35, z.h - 2.5), X(222), ly(222, z.h - 2.5), A1, 1, 160)
  if tick < 3 or tick % 5 == 0 then
    -- the full title only when a row may cut it; shortcut: counts characters, not measured width, upgrade to H.textWidth
    local tip
    if first and #first.title > 22 then tip = string.format('%s   %s   %s', first.title, os.date(first.allday and '%a %d %b' or '%a %d %b  %H:%M', first.s), first.label) end
    if cal.err > 0 then tip = (tip and tip .. '   ' or '') .. cal.err .. ' feed failed' end
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
