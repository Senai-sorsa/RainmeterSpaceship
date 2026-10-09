-- Coordinates bar (L_location, 440 x 130) - reference LAT / LON / VRT block.
local H
local lat, lon, alt, place, tz, src = nil, nil, nil, '', '', ''
local tick = 0

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

local function dms(v, pos, neg)
  if not v then return '--' end
  return string.format('%08.4f %s', math.abs(v), v >= 0 and pos or neg)
end

function Update()
  H.refreshTier()
  tick = tick + 1
  if H.num('LocationEnabled', 1) == 1 and (tick == 3 or tick % 600 == 0) then SKIN:Bang('!CommandMeasure', 'mGeoPrecise', 'Run') end
  local z = H.zones[1]
  local c = H.canvas(1)
  local A1, D, T = H.C.accent, H.C.dim, H.C.text
  local mask = H.num('LocationMask', 0) == 1
  -- crosshair glyph (reference: diagonal vector over a cross)
  local gx, gy = 70, 66
  c:hair(gx - 54, gy, gx + 54, gy, D, 1, 150)
  c:hair(gx, gy - 54, gx, gy + 54, D, 1, 150)
  for i = -4, 4 do if i ~= 0 then c:hair(gx + i * 12, gy - 3, gx + i * 12, gy + 3, D, 1, 150); c:hair(gx - 3, gy + i * 12, gx + 3, gy + i * 12, D, 1, 150) end end
  local ang = lon and math.rad(-lon) or math.rad(-40)
  c:line(gx, gy, gx + 48 * math.cos(ang), gy + 48 * math.sin(ang), A1, 2)
  c:dot(gx, gy, 3, A1)
  c:circle(gx, gy, 24, D, 1, 120)
  -- values
  local x0 = 160
  local rows = { { 'LAT', dms(lat, 'N', 'S') }, { 'LON', dms(lon, 'E', 'W') }, { alt and 'ALT' or 'TZ', alt and string.format('%.0f M', alt) or (tz ~= '' and string.upper(tz) or '--') } }
  for i, r in ipairs(rows) do
    local y = 6 + (i - 1) * 30
    H.text(1, i * 2 - 1, x0, y, r[1], { size = 11, weight = 700, color = A1 })
    local v = r[2]
    if mask and i < 3 then v = string.gsub(v, '%d', '*') end
    H.text(1, i * 2, x0 + 52, y - 1, v, { size = 13, font = H.fontNum, color = T, clip = z.w - x0 - 52 })
  end
  local line = (place ~= '' and string.upper(place) or 'ACQUIRING POSITION') .. (src ~= '' and ('   [' .. src .. ']') or '')
  if H.num('LocationEnabled', 1) == 0 then line = 'LOCATION OFF (Settings: LocationEnabled)' end
  H.text(1, 7, x0, 100, line, { size = 9, color = D, clip = z.w - x0 })
  c:hair(x0 - 8, 4, x0 - 8, 118, D, 1, 160)
  H.hit(1, 1, 0, 0, z.w, z.h, mask and 'Click to show coordinates' or 'Click to mask coordinates')
  c:flush()
  return 0
end

function OnClick(z, k) H.save('LocationMask', H.num('LocationMask', 0) == 1 and 0 or 1); Update() end
function OnRightClick(z, k) SKIN:Bang('!CommandMeasure', 'mGeoPrecise', 'Run') end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
