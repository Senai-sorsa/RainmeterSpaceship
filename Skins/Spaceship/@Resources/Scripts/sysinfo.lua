-- Ship identity card (R_sysinfo, 440 x 130) - reference "VANDUUL SCYTHE / DREAD PIRATE ROBERTS / RN RV".
local H

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

function Update()
  H.refreshTier()
  local z = H.zones[1]
  local c = H.canvas(1)
  local A1, D, T = H.C.accent, H.C.dim, H.C.text
  local R = z.w - 70
  H.text(1, 1, R, 2, H.str('DeviceName', 'PC'), { size = 15, font = H.fontTitle, weight = 700, color = T, align = 'RightTop' })
  H.text(1, 2, R, 30, H.str('DeviceModel', '') .. '  /  ' .. string.upper(H.sval('mOS', H.str('OsName', ''))), { size = 9, color = A1, align = 'RightTop', clip = R - 40 })
  H.text(1, 3, R, 50, H.str('CpuName', '') .. '  ' .. H.str('CpuCores', '') .. 'C/' .. H.str('CpuThreads', '') .. 'T', { size = 9.5, color = D, align = 'RightTop' })
  H.text(1, 4, R, 66, H.str('DGpuName', '') .. '  +  ' .. H.str('IGpuName', ''), { size = 9.5, color = D, align = 'RightTop' })
  H.text(1, 5, R, 82, H.str('RamGB', '') .. ' GB RAM   ' .. H.str('DisplayName', ''), { size = 9.5, color = D, align = 'RightTop' })
  H.text(1, 6, R, 102, 'UP', { size = 9, weight = 700, color = A1, align = 'RightTop' })
  H.text(1, 7, R - 26, 102, 'IP ' .. H.sval('mIP', '--') .. '     ' .. H.sval('mUptime', '--'), { size = 10, font = H.fontNum, color = T, align = 'RightTop' })
  -- ship glyph + badge (top right), divider with chevrons (left)
  c:icon('gpu', z.w - 30, 28, 50, A1, 1.6)
  c:rect(z.w - 22, 62, 20, 20, A1, 1.2)
  H.text(1, 8, z.w - 12, 72, H.str('CpuCores', '0'), { size = 9, font = H.fontNum, align = 'CenterCenter', color = A1 })
  c:dot(8, 112, 3, A1)
  c:poly({ { 26, 106 }, { 20, 112 }, { 26, 118 } }, A1, 1.4); c:poly({ { 34, 106 }, { 28, 112 }, { 34, 118 } }, A1, 1.4)
  c:hair(40, 112, R - 140, 112, D, 1, 120)
  H.hit(1, 1, 0, 0, z.w, z.h, 'Open System Information')
  c:flush()
  return 0
end

function OnClick(z, k) SKIN:Bang('["ms-settings:about"]') end
function OnRightClick(z, k) SKIN:Bang('["msinfo32.exe"]') end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
