-- Bottom strip: four boxed cells each side of the dash arch, the right side mirrored.
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

-- four boxed cells per side stepping up toward the centre along the dash arch (reference left strip:
-- cells at x 429 / 474 / 519 / 564, tops 661 / 656 / 654 / 651, 37 x 15); the right side is its mirror
local CX, CY, CW_, CH_ = { 4, 49, 94, 139 }, { 11, 6, 4, 1 }, 37, 15

local function cells(zi, list, mirror)
  local z = H.zones[zi]
  local c = H.canvas(zi)
  for i, cl in ipairs(list) do
    local w, h = CW_ * SXR, CH_ * SYR
    local x0 = mirror and (z.w - (CX[i] + CW_) * SXR) or CX[i] * SXR
    local y0 = CY[i] * SYR
    local col = cl[5] and H.C.hi or H.C.white
    c:rect(x0, y0, w, h, col, 1.3, 210, 4)
    c:icon(cl[1], x0 + 16, y0 + h / 2, 18, col, 1.2)
    H.text(zi, i, x0 + 32, y0 + h / 2, cl[2], { size = 6, weight = 700, align = 'LeftCenter', color = col, font = H.fontNum, clip = w - 36 })
    H.hit(zi, i, x0, y0, w, h, cl[3])
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
