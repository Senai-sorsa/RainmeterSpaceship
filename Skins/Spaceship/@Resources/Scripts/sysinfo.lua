-- Ship identity block: the mirror image of the location block on the left (same rails, same rows,
-- labels and values flipped), showing this PC instead of coordinates.
local H
local SXR, SYR = 2560 / 1260, 1600 / 709

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

function Update()
  H.refreshTier()
  local z = H.zones[1]
  local c = H.canvas(1)
  local A1, W = H.C.accent, H.C.white
  -- the location block's reference positions, mirrored inside the (mirrored) zone
  local function X(rx) return z.w - (rx - 34) * SXR end
  local function Y(ry) return (ry - 222) * SYR end
  c:line(X(40), Y(228), X(226), Y(228), A1, 1.3, 220)
  c:dot(X(40), Y(228), 3, A1); c:dot(X(226), Y(228), 3, A1)
  -- emblem where the location crosshair sits: GPU glyph, a boxed GPU count and a ring
  local gx, gy = X(100), Y(262)
  c:circle(gx, gy, 40, W, 1, 90)
  c:icon('gpu', gx, gy, 40, W, 1.4)
  c:rect(gx + 30, gy + 22, 24, 22, H.C.hi, 1.5)
  H.text(1, 7, gx + 42, gy + 33, '2', { size = 7, weight = 700, align = 'CenterCenter', color = H.C.hi, font = H.fontNum })
  local rows = { { 'SYS', H.str('DeviceName', 'PC'), W }, { 'UP', H.sval('mUptime', '--'), H.C.hi }, { 'IP', H.sval('mIP', '--'), W } }
  for i, r in ipairs(rows) do
    local y = Y(({ 246.5, 257.8, 269.5 })[i])
    H.text(1, i * 2 - 1, X(152), y, r[1], { size = 8, weight = 700, align = 'LeftCenter', color = r[3] })
    H.text(1, i * 2, X(158), y, r[2], { size = 7, weight = 700, align = 'RightCenter', color = r[3], font = H.fontNum, clip = X(158) - X(228) })
  end
  H.hideText(1, 8)
  local function ly(rx, base) return base - (10 / 196 - 4 / 187) * (rx - 34) * SYR end
  c:line(X(35), ly(35, z.h - 9), X(222), ly(222, z.h - 9), A1, 1.3, 220)
  c:line(X(35), ly(35, z.h - 2.5), X(222), ly(222, z.h - 2.5), A1, 1, 160)
  H.hit(1, 1, 0, 0, z.w, z.h, H.str('DeviceModel', '') .. ' / ' .. H.str('OsName', '') .. '  |  ' .. H.str('CpuName', '') .. ' ' .. H.str('CpuCores', '') .. 'C/' .. H.str('CpuThreads', '') .. 'T  |  ' ..
    H.str('DGpuName', '') .. ' + ' .. H.str('IGpuName', '') .. '  |  ' .. H.str('RamGB', '') .. ' GB  |  ' .. H.str('DisplayName', '') .. '   (click: About)')
  c:flush()
  return 0
end

function OnClick(z, k) SKIN:Bang('["ms-settings:about"]') end
function OnRightClick(z, k) SKIN:Bang('["msinfo32.exe"]') end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
