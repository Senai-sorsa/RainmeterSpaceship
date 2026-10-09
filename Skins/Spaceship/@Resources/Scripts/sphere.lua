-- Holographic radar sphere (C_sphere, 380 x 380).
local H
local yaw, frame = 0, 0
local iss = nil
local R, CX, CY, TILT = 132, 190, 168, math.rad(22)
local sin, cos, rad = math.sin, math.cos, math.rad

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

function OnISS()
  local s = H.sval('mISS', '')
  local la = tonumber(string.match(s, '"latitude":%s*"?(-?[%d%.]+)'))
  local lo = tonumber(string.match(s, '"longitude":%s*"?(-?[%d%.]+)'))
  if la and lo then iss = { la, lo } end
end

-- lat/lon (deg) -> screen x, y, depth
local function project(lat, lon)
  local la, lo = rad(lat), rad(lon) + yaw
  local x = R * cos(la) * sin(lo)
  local y = R * sin(la)
  local z = R * cos(la) * cos(lo)
  local y2 = y * cos(TILT) - z * sin(TILT)
  local z2 = y * sin(TILT) + z * cos(TILT)
  return CX + x, CY - y2, z2
end

-- draw a curve split into front (bright) and back (dim) runs
local function curve(c, fn, n, col)
  local run, front = {}, nil
  local function flush()
    if #run >= 2 then
      if front then c:poly(run, col, 1.3, 230) else c:hairPoly(run, col, 90) end
    end
  end
  for i = 0, n do
    local x, y, z = fn(i / n)
    local f = z >= 0
    if front == nil then front = f end
    if f ~= front then
      run[#run + 1] = { x, y }
      flush()
      run, front = { { x, y } }, f
    else
      run[#run + 1] = { x, y }
    end
  end
  flush()
end

local function hash(s)
  local h = 0
  for i = 1, #s do h = (h * 31 + string.byte(s, i)) % 3600 end
  return h / 10
end

function Update()
  frame = frame + 1
  if frame % 10 == 1 then H.refreshTier() end
  local tier = H.tier
  local every = ({ [0] = 1, [1] = 3, [2] = 100, [3] = 0 })[tier] or 1
  if tier == 3 then
    if frame % 20 == 1 then local c = H.canvas(1); for k = 1, 10 do H.hideText(1, k) end; c:flush() end
    return 0
  end
  if frame % every ~= 1 and every ~= 1 then return 0 end
  yaw = (yaw + rad(0.9) * every) % (2 * math.pi)
  local c = H.canvas(1)
  local A1, D, O = H.C.accent, H.C.dim, H.C.warn
  -- globe
  c:fillCircle(CX, CY, R, H.C.panel, 50)
  c:circle(CX, CY, R, A1, 1.2, 160)
  for lon = 0, 150, 30 do
    curve(c, function(t) return project(-90 + 180 * t, lon) end, 18, A1)
    curve(c, function(t) return project(-90 + 180 * t, lon + 180) end, 18, A1)
  end
  for _, lat in ipairs({ -60, -30, 0, 30, 60 }) do
    curve(c, function(t) return project(lat, 360 * t) end, 36, A1)
  end
  -- radar disk at the base (reference: orange ring with blips)
  local dy, rx, ry = CY + R * 0.62, 150, 34
  c:poly(H.arcPts(CX, dy, rx, ry, 0, 360, 48), O, 1.4, 200)
  c:poly(H.arcPts(CX, dy, rx * 0.6, ry * 0.6, 0, 360, 36), O, 1.2, 140)
  local net = H.val('mNetIn', 0)
  local pulse = (frame * 0.02 + math.min(1, net / (5 * 1048576))) % 1
  c:poly(H.arcPts(CX, dy, rx * pulse, ry * pulse, 0, 360, 36), O, 1, math.floor(200 * (1 - pulse)))
  local threads = math.max(1, H.val('mThreads', 20))
  local ti = 1
  for i = 1, 8 do
    local name = string.gsub(H.sval('mP' .. i, ''), '#%d+$', '')
    if name ~= '' then
      local share = H.clamp(H.val('mP' .. i, 0) / threads / 30, 0, 1)
      local a = rad(hash(name)) + yaw * 0.25
      local r = 0.95 - 0.7 * share
      local bx, by = CX + rx * r * cos(a), dy + ry * r * sin(a)
      local h = 12 + 60 * share
      c:hair(bx, by, bx, by - h, i == 1 and O or A1, 1, 170)
      c:poly({ { bx, by - h - 5 }, { bx + 5, by - h }, { bx, by - h + 5 }, { bx - 5, by - h } }, i == 1 and O or A1, 1.4, 255, true)
      if i <= 3 then
        H.text(1, ti, bx + 8, by - h, string.upper(name), { size = 7.5, weight = 700, align = 'LeftCenter', color = i == 1 and O or D, clip = 90 })
        ti = ti + 1
      end
    end
  end
  -- ISS + you
  local function marker(lat, lon, label, col)
    local x, y, z = project(lat, lon)
    if z < 0 then return end
    c:rect(x - 4, y - 4, 8, 8, col, 1.4)
    H.text(1, ti, x + 7, y - 8, label, { size = 7.5, weight = 700, color = col }); ti = ti + 1
  end
  if iss then marker(iss[1], iss[2], 'ISS', H.C.good) end
  local g = H.sval('mGeo', '')
  local la, lo = tonumber(string.match(g, '"lat":%s*(-?[%d%.]+)')), tonumber(string.match(g, '"lon":%s*(-?[%d%.]+)'))
  if la and lo then marker(la, lo, 'YOU', A1) end
  H.text(1, ti, CX, 362, iss and string.format('ISS %.1f %.1f', iss[1], iss[2]) or 'PROCESS RADAR', { size = 8, font = H.fontNum, align = 'CenterTop', color = D }); ti = ti + 1
  for k = ti, 10 do H.hideText(1, k) end
  if frame < 3 then H.hit(1, 1, CX - R, CY - R, 2 * R, 2 * R, 'Radar: busiest processes (disk), ISS and your position (globe)') end
  c:flush()
  return 0
end

function OnClick(z, k) SKIN:Bang('["taskmgr.exe"]') end
function OnRightClick(z, k) end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
