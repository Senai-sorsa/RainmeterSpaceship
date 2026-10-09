-- Bottom strip: four readouts each side of the dash arch, in the lane under it, the right side mirrored.
-- Left: CPU temp, GPU temp, load (the red cell), fan. Right: down, up, ping, Wi-Fi.
local H
local SXR, SYR = 2560 / 1260, 1600 / 709

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function fmt(v, f) if v == nil then return '--' end; return string.format(f, v) end
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
    local col = cl[4] and H.C.hi or H.C.white
    c:icon(cl[1], x0 + 9, y, 15, cl[4] and H.C.hi or H.C.accent, 1.2)
    H.text(zi, i, x0 + 20, y, cl[2], { size = 5, weight = 700, align = 'LeftCenter', color = col, font = H.fontNum, clip = CELLW - 22 })
    H.hit(zi, i, x0, 0, CELLW, z.h, cl[3])
  end
  c:flush()
end

function Update()
  H.refreshTier()
  local load = H.val('mCPU', 0)
  -- outermost cell first on both sides
  cells(1, {
    { 'gauge', fmt(H.hw('mHwCpuTemp'), '%.0fC'), 'CPU temperature' },
    { 'gpu', fmt(H.hw('mHwGpuTemp'), '%.0fC'), 'GPU temperature' },
    { 'wave', string.format('%d%%', load), 'CPU load', true },
    { 'gear', fmt(H.hw('mHwFan1'), '%.0f'), 'Fan speed (RPM)' },
  }, false)
  cells(2, {
    { 'cloud', rate(H.val('mNetIn', 0)), 'Download' },
    { 'nodes', rate(H.val('mNetOut', 0)), 'Upload' },
    { 'orbit', string.format('%dms', H.val('mPing', 0)), 'Ping' },
    { 'wave', string.format('%d%%', H.val('mWifi', 0)), 'Wi-Fi signal' },
  }, true)
  return 0
end

function OnClick(z, k) SKIN:Bang('["taskmgr.exe" "/7"]') end
function OnRightClick(z, k) end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
