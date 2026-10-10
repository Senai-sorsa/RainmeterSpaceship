-- Bottom strip: four readouts each side of the dash arch, in the lane under it, the right side mirrored.
-- Left: CPU temp, GPU temp, CPU load, fan. Right: drive fill, disk activity, ping, Wi-Fi (network speeds are in
-- the network block now).
local H
local SXR, SYR = 2560 / 1260, 1600 / 709

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function fmt(v, f) if v == nil then return '--' end; return string.format(f, v) end
-- compact per-second rate that fits a cell: 820B/s, 4.2KB/s, 47KB/s, 312MB/s
local function short(b)
  local u, i = { 'B', 'KB', 'MB', 'GB' }, 1
  while b >= 1000 and i < #u do b = b / 1024; i = i + 1 end
  return string.format(b < 10 and i > 1 and '%.1f%s/s' or '%.0f%s/s', b, u[i])
end
local function rate(b)
  if b >= 1048576 then return string.format('%.1fM', b / 1048576) end
  return string.format('%.0fK', b / 1024)
end

-- readouts sit unboxed in the lane between the dash arch and its lower parallel (the zone follows the arch's
-- slope), grouped toward the outer ends; the right side is the mirror image
local STEP, CELLW = 84, 76

local function cells(zi, list, mirror)
  local z = H.zones[zi]
  local c = H.canvas(zi)
  local y = z.h / 2
  for i, cl in ipairs(list) do
    local x0 = mirror and (z.w - 4 - (i - 1) * STEP - CELLW) or (4 + (i - 1) * STEP)
    -- theme colours; a cell turns warn / alert only when its value crosses the thresholds in Settings.inc
    local col = cl[4] == 2 and H.C.alert or cl[4] == 1 and H.C.warn or H.C.white
    c:icon(cl[1], x0 + 9, y, 15, cl[4] == 2 and H.C.alert or cl[4] == 1 and H.C.warn or H.C.accent, 1.2)
    H.text(zi, i, x0 + 20, y, cl[2], { size = cl[5] or 5, weight = 700, align = 'LeftCenter', color = col, font = H.fontNum, clip = CELLW - 22 })
    H.hit(zi, i, x0, 0, CELLW, z.h, cl[3])
  end
  c:flush()
end

function Update()
  H.refreshTier()
  local load = H.val('mCPU', 0)
  local tot, free = H.val('mD1Total', 0), H.val('mD1Free', 0)
  local used = tot > 0 and (tot - free) / tot or 0
  local ct, gt = H.hw('mHwCpuTemp'), H.hw('mHwGpuTemp')
  -- 0 normal, 1 warn (near the limit), 2 alert (over it)
  local function lvl(v, limit, margin)
    if not v then return 0 end
    if v >= limit then return 2 end
    if v >= limit - margin then return 1 end
    return 0
  end
  -- outermost cell first on both sides
  cells(1, {
    { 'gauge', fmt(ct, '%.0fC'), 'CPU temperature', lvl(ct, H.num('WarnCpuTemp', 92), 5) },
    { 'gpu', fmt(gt, '%.0fC'), 'GPU temperature', lvl(gt, H.num('WarnGpuTemp', 85), 5) },
    { 'wave', string.format('%d%%', load), 'CPU load', lvl(load, 95, 10) },
    { 'gear', fmt(H.hw('mHwFan1'), '%.0f'), 'Fan speed (RPM)' },
  }, false)
  cells(2, {
    { 'drive', string.format('%s %d%%', string.sub(H.str('Drive1', 'C:'), 1, 1), math.floor(used * 100 + 0.5)),
      string.format('Drive %s  %.0f / %.0f GB used   click: open', H.str('Drive1', 'C:'), (tot - free) / 1073741824, tot / 1073741824), lvl(used * 100, H.num('WarnDiskPct', 90), 5) },
    { 'disk', short(H.val('mDiskIO', 0)), 'Disk activity (read + write per second)', 0, 4.6 },
    { 'orbit', string.format('%dms', H.val('mPing', 0)), 'Ping' },
    { 'wave', string.format('%d%%', H.val('mWifi', 0)), 'Wi-Fi signal' },
  }, true)
  return 0
end

function OnClick(z, k)
  if z == 2 and k == 1 then SKIN:Bang('["' .. H.str('Drive1', 'C:') .. '\\"]') else SKIN:Bang('["taskmgr.exe" "/7"]') end
end
function OnRightClick(z, k) end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
