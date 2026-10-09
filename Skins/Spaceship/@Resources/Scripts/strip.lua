-- Bottom strip (reference: four boxed cells "1500  7  0%  443" on the left of the arch, two open
-- cells "20  20" on the right). Left: CPU temp, GPU temp, load (the red cell), fan. Right: down, up.
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

function Update()
  H.refreshTier()
  local A1, W = H.C.accent, H.C.white
  -- left: boxed cells
  local c = H.canvas(1)
  local function X(rx) return (rx - 425) * SXR end
  local function Y(ry) return (ry - 650) * SYR end
  local load = H.val('mCPU', 0)
  local cells = {
    { 429, 661, 'gauge', fmt(H.hw('mHwCpuTemp'), '%.0fC'), 'CPU temperature' },
    { 474, 656, 'gpu', fmt(H.hw('mHwGpuTemp'), '%.0fC'), 'GPU temperature' },
    { 519, 654, 'wave', string.format('%d%%', load), 'CPU load', true },
    { 564, 651, 'gear', fmt(H.hw('mHwFan1'), '%.0f'), 'Fan speed (RPM)' },
  }
  for i, cl in ipairs(cells) do
    local x0, y0 = X(cl[1]), Y(cl[2])
    local w, h = 37 * SXR, 15 * SYR
    local col = cl[6] and H.C.hi or W
    c:rect(x0, y0, w, h, col, 1.3, 210, 4)
    c:icon(cl[3], x0 + 16, y0 + h / 2, 18, col, 1.2)
    H.text(1, i, x0 + 32, y0 + h / 2, cl[4], { size = 7.5, weight = 700, align = 'LeftCenter', color = col })
    H.hit(1, i, x0, y0, w, h, cl[5])
  end
  c:flush()
  -- right: open cells
  local d = H.canvas(2)
  local function X2(rx) return (rx - 742) * SXR end
  local function Y2(ry) return (ry - 654) * SYR end
  local open = {
    { 750, 661, 'cloud', rate(H.val('mNetIn', 0)), 'Download   (ping ' .. string.format('%d', H.val('mPing', 0)) .. ' ms)' },
    { 792, 669, 'nodes', rate(H.val('mNetOut', 0)), 'Upload   (Wi-Fi ' .. string.format('%d', H.val('mWifi', 0)) .. '%)' },
  }
  for i, cl in ipairs(open) do
    local x0, y0 = X2(cl[1]), Y2(cl[2])
    d:icon(cl[3], x0 + 8, y0, 18, W, 1.2)
    H.text(2, i, x0 + 22, y0, cl[4], { size = 7.5, weight = 700, align = 'LeftCenter', color = W })
    H.hit(2, i, x0, y0 - 14, 70, 28, cl[5])
  end
  d:flush()
  return 0
end

function OnClick(z, k) SKIN:Bang('["taskmgr.exe" "/7"]') end
function OnRightClick(z, k) end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
