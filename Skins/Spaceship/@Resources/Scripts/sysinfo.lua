-- Ship identity card (reference: VANDUUL SCYTHE / DREAD PIRATE ROBERTS / RN RV, 1028-1228 x 226-302).
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
  local function X(rx) return (rx - 1028) * SXR end
  local function Y(ry) return (ry - 226) * SYR end
  -- top rail with dot
  c:line(X(1032), Y(240), X(1218), Y(232), W, 1.1, 170)
  c:dot(X(1032), Y(240), 2.5, W)
  H.text(1, 1, X(1176), Y(244), H.str('DeviceName', 'PC'), { size = 9, weight = 700, align = 'RightCenter', color = W })
  H.text(1, 2, X(1176), Y(255), H.str('DeviceModel', '') .. ' / ' .. H.str('OsName', ''), { size = 6.5, weight = 700, align = 'RightCenter', color = H.C.hi })
  -- emblem + boxed number (reference skull + [2]) -> GPU glyph + GPU count
  c:icon('gpu', X(1192), Y(246), 22, W, 1.4)
  c:rect(X(1203), Y(238), X(1215) - X(1203), Y(252) - Y(238), H.C.hi, 1.5)
  H.text(1, 3, (X(1203) + X(1215)) / 2, (Y(238) + Y(252)) / 2, '2', { size = 8, weight = 700, align = 'CenterCenter', color = H.C.hi })
  -- RN / RV rows -> uptime / IP
  H.text(1, 4, X(1168), Y(270), 'UP', { size = 7, weight = 700, align = 'RightCenter', color = W })
  H.text(1, 5, X(1222), Y(270), H.sval('mUptime', '--'), { size = 7, weight = 700, align = 'RightCenter', color = W })
  H.text(1, 6, X(1168), Y(280), 'IP', { size = 7, weight = 700, align = 'RightCenter', color = W })
  H.text(1, 7, X(1222), Y(280), H.sval('mIP', '--'), { size = 7, weight = 700, align = 'RightCenter', color = W })
  -- dot + double chevron, double rail with highlight segment
  c:dot(X(1037), Y(284), 3, A1)
  c:poly({ { X(1046), Y(281) }, { X(1042), Y(284) }, { X(1046), Y(287) } }, A1, 1.6)
  c:poly({ { X(1051), Y(281) }, { X(1047), Y(284) }, { X(1051), Y(287) } }, A1, 1.6)
  c:line(X(1035), Y(295), X(1222), Y(292), W, 1.2, 200)
  c:line(X(1035), Y(298), X(1222), Y(296), W, 1, 150)
  c:line(X(1035), Y(298), X(1080), Y(297.3), H.C.hi, 2)
  H.hit(1, 1, 0, 0, z.w, z.h, H.str('CpuName', '') .. ' ' .. H.str('CpuCores', '') .. 'C/' .. H.str('CpuThreads', '') .. 'T  |  ' ..
    H.str('DGpuName', '') .. ' + ' .. H.str('IGpuName', '') .. '  |  ' .. H.str('RamGB', '') .. ' GB  |  ' .. H.str('DisplayName', '') .. '   (click: About)')
  c:flush()
  return 0
end

function OnClick(z, k) SKIN:Bang('["ms-settings:about"]') end
function OnRightClick(z, k) SKIN:Bang('["msinfo32.exe"]') end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
