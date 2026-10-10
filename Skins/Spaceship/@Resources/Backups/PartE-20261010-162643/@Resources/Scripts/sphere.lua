-- Holographic sphere: one smooth deep-blue sphere (pre-blurred sprite with a brighter limb), two disks
-- through its centre - a tilted one with its rim, inner ring and orange sweep, and a level one crossing it -
-- a base ring, blips on stalks and the "DSP RNGE" box. Centred on the screen axis.
-- Blips = busiest processes; ISS and your position ride on the rotating globe; the box = network rate.
local H
local frame, rot, yaw = 0, 0, 0
local iss = nil
local SXR, SYR = 2560 / 1260, 1600 / 709
local function X(rx) return (rx - 514) * SXR end
local function Y(ry) return (ry - 407) * SYR end
local CX, CY, R = (746 - 514) / 2 * SXR, Y(491), 180   -- centred in the zone, i.e. on the screen axis
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

local function project(lat, lon)
  local la, lo = rad(lat), rad(lon) + yaw
  local x, y, z = R * cos(la) * sin(lo), R * sin(la), R * cos(la) * cos(lo)
  local t = rad(18)
  return CX + x, CY - (y * cos(t) - z * sin(t)), y * sin(t) + z * cos(t)
end

local function hash(s)
  local h = 0
  for i = 1, #s do h = (h * 31 + string.byte(s, i)) % 3600 end
  return h / 10
end

function Update()
  frame = frame + 1
  if frame % 20 == 1 then H.refreshTier() end
  local tier = H.tier
  if tier == 3 then
    if frame % 40 == 1 then local c = H.canvas(1); for k = 1, 8 do H.hideText(1, k) end; H.hideSprite(1, 1); H.hideSprite(1, 2); c:flush() end
    return 0
  end
  local every = ({ [0] = 1, [1] = 3 })[tier] or 100
  if frame > 1 and every > 1 and frame % every ~= 0 then return 0 end
  rot = (rot + 1.1 * every) % 360
  yaw = (yaw + rad(0.5) * every) % (2 * math.pi)
  local c = H.canvas(1)
  local A1, W, O = H.C.accent, H.C.white, H.C.warn
  -- one smooth sphere: a pre-blurred body sprite in deep blue with a brighter limb (no stacked rings)
  local deep = H.mix(A1, { 10, 55, 150 }, 0.8)
  H.sprite(1, 1, CX, CY, R * 2.12, R * 2.12, 'sphere_body.png', deep, 220)
  H.sprite(1, 2, CX, CY, R * 2.12, R * 2.12, 'sphere_rim.png', H.mix(A1, W, 0.2), 170)
  c:circle(CX, CY, R, A1, 1.2, 90)
  -- one tilted disk through the centre: filled plane, bright rim, inner ring and the orange sweep
  local tilt, TA = 0.17, -9                                  -- disk aspect and tilt (degrees)
  local ey = CY + 6
  -- plus one flat (level) plane crossing it: its far half is drawn first, behind the tilted disk,
  -- its near half after, so the two planes visibly pass through each other
  local ft = 0.22
  c:fillPoly(H.ellipsePts(CX, ey, R * 0.99, R * 0.99 * ft, 0, 0, 360, 64), A1, 14)
  c:poly(H.ellipsePts(CX, ey, R * 0.99, R * 0.99 * ft, 0, 180, 360, 32), A1, 1.6, 120)
  local disk = H.ellipsePts(CX, ey, R * 0.97, R * 0.97 * tilt, TA, 0, 360, 64)
  c:fillPoly(disk, H.mix(A1, W, 0.4), 30)
  c:poly(disk, W, 2.2, 235)
  c:poly(H.ellipsePts(CX, ey, R * 0.42, R * 0.42 * tilt, TA, 0, 360, 36), W, 1.3, 160)
  c:poly(H.ellipsePts(CX, ey, R * 0.97, R * 0.97 * tilt, TA, rot * 1.5, rot * 1.5 + 55, 14), O, 3, 235)
  c:poly(H.ellipsePts(CX, ey, R * 0.99, R * 0.99 * ft, 0, 0, 180, 32), H.mix(A1, W, 0.3), 1.8, 215)
  local ct, st = math.cos(rad(TA)), math.sin(rad(TA))
  -- base ring under the sphere (the projector's beam)
  c:poly(H.ellipsePts(CX, CY + R * 0.9, R * 0.55, R * 0.1, 0, 0, 360, 40), A1, 1.6, 200)
  -- process blips on stalks
  local threads = math.max(1, H.val('mThreads', 20))
  local ti = 1
  for i = 1, 8 do
    local name = string.gsub(H.sval('mP' .. i, ''), '#%d+$', '')
    if name ~= '' then
      local share = H.clamp(H.val('mP' .. i, 0) / threads / 30, 0, 1)
      local a = rad(hash(name) + rot * 0.35)
      local r = 0.95 - 0.65 * share
      local dx, dy = R * 0.9 * r * cos(a), R * 0.9 * tilt * r * sin(a)
      local bx, by = CX + dx * ct - dy * st, ey + dx * st + dy * ct
      local hgt = 14 + 70 * share
      c:hair(bx, by, bx, by - hgt, W, 1, 160)
      local s2 = i == 1 and 9 or 5
      c:poly({ { bx, by - hgt - s2 }, { bx + s2, by - hgt }, { bx, by - hgt + s2 }, { bx - s2, by - hgt } }, i == 1 and W or A1, 1.6, 255, true)
      if i == 1 then c:dot(bx, by - hgt, 2.5, W); c:line(bx + 10, by - hgt, bx + 80, by - hgt + 14, W, 1.2, 200) end
    end
  end
  local function marker(lat, lon, label, col)
    local x, y, z = project(lat, lon)
    if z < 0 then return end
    c:rect(x - 4, y - 4, 8, 8, col, 1.4)
    H.text(1, ti, x + 8, y - 6, label, { size = 6, weight = 700, color = col }); ti = ti + 1
  end
  if iss then marker(iss[1], iss[2], 'ISS', H.C.good) end
  local g = H.sval('mGeo', '')
  local la, lo = tonumber(string.match(g, '"lat":%s*(-?[%d%.]+)')), tonumber(string.match(g, '"lon":%s*(-?[%d%.]+)'))
  if la and lo then marker(la, lo, 'YOU', W) end
  -- side label box (reference "DSP RNGE" with a bar) -> download speed in Mbps. Label pinned left, value
  -- right-aligned to the bar's end, so they can't run into each other; the bar is the share of your
  -- connection in use (LinkDownMbps = last speed test, Settings.inc)
  local down, up = H.val('mNetIn', 0), H.val('mNetOut', 0)
  local bx0, bx1, by = X(687), X(744), Y(541)   -- wide enough for "NET" + the longest value ("99.9 Mbps")
  H.text(1, ti, bx0, Y(536), 'NET', { size = 5.4, weight = 700, align = 'LeftBottom', color = H.mix(A1, W, 0.3) }); ti = ti + 1
  H.text(1, ti, bx1, Y(536), H.mbps(down), { size = 5.2, weight = 700, align = 'RightBottom', color = W, font = H.fontNum }); ti = ti + 1
  local link = math.max(1, H.num('LinkDownMbps', 200))
  local use = H.clamp(down * 8 / 1000000 / link, 0, 1)
  c:hair(bx0, by, bx1, by, W, 1, 120)
  if use > 0.002 then c:line(bx0, by, bx0 + (bx1 - bx0) * math.max(use, 0.03), by, use > 0.8 and O or A1, 2.4) end
  if frame < 3 or frame % 20 == 0 then
    H.hit(1, 2, bx0, Y(526), bx1 - bx0, Y(544) - Y(526), string.format('Network   down %s   up %s   link %d / %d Mbps (last speed test)',
      H.mbps(down), H.mbps(up), link, H.num('LinkUpMbps', 0)))
  end
  for k = ti, 8 do H.hideText(1, k) end
  if frame < 3 then H.hit(1, 1, CX - R, CY - R, 2 * R, 2 * R, 'Radar: busiest processes, ISS and your position - click: Task Manager') end
  c:flush()
  return 0
end

function OnClick(z, k) SKIN:Bang('["taskmgr.exe"]') end
function OnRightClick(z, k) end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
