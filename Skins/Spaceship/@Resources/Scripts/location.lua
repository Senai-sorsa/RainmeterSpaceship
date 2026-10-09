-- Coordinates block (reference LAT / LON / VRT, 34-230 x 222-302).
local H
local lat, lon, alt, place, tz, src = nil, nil, nil, '', '', ''
local tick, sweep = 0, 0
local SXR, SYR = 2560 / 1260, 1600 / 709

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

function OnGeo()
  local s = H.sval('mGeoIP', '')
  if string.find(s, '"success"') and src ~= 'GPS' then
    lat = tonumber(string.match(s, '"lat":%s*(-?[%d%.]+)'))
    lon = tonumber(string.match(s, '"lon":%s*(-?[%d%.]+)'))
    place = (string.match(s, '"city":%s*"([^"]*)"') or '') .. ', ' .. (string.match(s, '"countryCode":%s*"([^"]*)"') or '')
    tz = string.match(s, '"timezone":%s*"([^"]*)"') or ''
    src = 'IP'
  end
end

function OnPrecise()
  local a, b, c = string.match(H.sval('mGeoPrecise', ''), '(-?[%d%.]+)|(-?[%d%.]+)|(-?[%d%.]+)')
  if a then lat, lon, alt, src = tonumber(a), tonumber(b), tonumber(c), 'GPS' end
end

local function fmt(v, pos, neg)
  if not v then return '--' end
  return string.format('%.4f%s', math.abs(v), v >= 0 and pos or neg)
end

function Update()
  H.refreshTier()
  tick = tick + 1
  if H.num('LocationEnabled', 1) == 1 and (tick == 3 or tick % 600 == 0) then SKIN:Bang('!CommandMeasure', 'mGeoPrecise', 'Run') end
  local z = H.zones[1]
  local c = H.canvas(1)
  local A1, W = H.C.accent, H.C.white
  local function X(rx) return (rx - 34) * SXR end
  local function Y(ry) return (ry - 222) * SYR end
  -- top rail with end dots (reference 40,228 -> 226,238 follows the zone slant)
  c:line(X(40), Y(228), X(226), Y(228), A1, 1.3, 220)
  c:dot(X(40), Y(228), 3, A1); c:dot(X(226), Y(228), 3, A1)
  -- crosshair: dashed vertical, cross ticks, heading vector (pink) + diagonal
  local gx, gy = X(100), Y(262)
  for i = -5, 5 do if i ~= 0 then c:hair(gx, gy + i * 9 - 3, gx, gy + i * 9 + 3, W, 1.2, 170) end end
  c:hair(gx - 44, gy, gx + 44, gy, W, 1, 90)
  sweep = (sweep + (H.tier == 0 and 4 or 0)) % 360
  local ang = math.rad(lon and (-lon / 2 - 35) or -40)
  c:line(gx - 40 * math.cos(ang), gy - 40 * math.sin(ang), gx + 40 * math.cos(ang), gy + 40 * math.sin(ang), W, 1.2, 200)
  c:line(gx - 34, gy + 32, gx, gy, H.C.hi, 2)
  -- values (reference: labels right-aligned, LON value pink)
  local mask = H.num('LocationMask', 0) == 1
  local rows = { { 'LAT', fmt(lat, 'N', 'S'), H.C.white }, { 'LON', fmt(lon, 'E', 'W'), H.C.hi },
                 { alt and 'ALT' or 'TZ', alt and string.format('%.0fM', alt) or (tz ~= '' and string.upper(string.match(tz, '[^/]+$') or tz) or '--'), H.C.white } }
  for i, r in ipairs(rows) do
    local y = Y(({ 246.5, 257.8, 269.5 })[i])
    local v = r[2]
    if mask and i < 3 then v = string.gsub(v, '%d', '*') end
    H.text(1, i * 2 - 1, X(152), y, r[1], { size = 8, weight = 700, align = 'RightCenter', color = r[3] })
    H.text(1, i * 2, X(158), y, v, { size = 8, weight = 700, align = 'LeftCenter', color = r[3] })
  end
  H.hideText(1, 7)
  -- double bottom rail (reference 35,292 -> 222,296)
  -- the reference's bottom rails slope less than the panel (292 -> 296 over 187 px)
  local function ly(rx, base) return base - (10 / 196 - 4 / 187) * (rx - 34) * SYR end
  c:line(X(35), ly(35, z.h - 9), X(222), ly(222, z.h - 9), A1, 1.3, 220)
  c:line(X(35), ly(35, z.h - 2.5), X(222), ly(222, z.h - 2.5), A1, 1, 160)
  H.hit(1, 1, 0, 0, z.w, z.h, (place ~= '' and (string.upper(place) .. ' [' .. src .. ']   ') or '') .. (mask and 'Click to show coordinates' or 'Click to mask coordinates   (right-click: refresh)'))
  c:flush()
  return 0
end

function OnClick(z, k) H.save('LocationMask', H.num('LocationMask', 0) == 1 and 0 or 1); Update() end
function OnRightClick(z, k) SKIN:Bang('!CommandMeasure', 'mGeoPrecise', 'Run') end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
