-- Target lock (C_target, 260 x 205): the busiest process, reference orange reticle.
local H
local rank, spin = 1, 0

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

function Update()
  H.refreshTier()
  local z = H.zones[1]
  local c = H.canvas(1)
  local O, D = H.C.warn, H.C.dim
  local threads = math.max(1, H.val('mThreads', 20))
  local name = H.sval('mTop' .. rank, '')
  name = string.gsub(name, '#%d+$', '')
  local cpu = H.val('mTop' .. rank, 0) / threads
  H.set('mTargetRam', 'Name', name ~= '' and name or 'explorer')
  local ram = H.val('mTargetRam', 0)
  if H.tier == 0 then spin = (spin + 12) % 360 end
  local cx, cy = 170, 98
  -- outer reticle with rotating gaps
  for q = 0, 3 do c:arc(cx, cy, 78, spin + q * 90 + 12, spin + q * 90 + 78, O, 1.4, 220) end
  for q = 0, 3 do
    local a = math.rad(q * 90 + 45)
    c:line(cx + 84 * math.cos(a), cy + 84 * math.sin(a), cx + 92 * math.cos(a), cy + 92 * math.sin(a), O, 1.4)
  end
  -- inner lock rings, thickness follows CPU share
  local w = 3 + 6 * H.clamp(cpu / 50, 0, 1)
  c:circle(cx, cy, 36, O, w)
  c:circle(cx, cy, 24, O, 1.4, 200)
  c:dot(cx, cy, 5, O)
  -- rank badge + memory readout (reference: [2] 567m)
  c:rect(20, 74, 26, 26, O, 1.6)
  H.text(1, 1, 33, 87, tostring(rank), { size = 11, font = H.fontNum, align = 'CenterCenter', color = O })
  H.text(1, 2, 33, 108, ram > 0 and string.format('%.0fm', ram / 1048576) or '--', { size = 10.5, font = H.fontNum, align = 'CenterTop', color = O })
  -- labels
  H.text(1, 3, cx, 190, name ~= '' and string.upper(name) or 'NO TARGET', { size = 10, weight = 700, align = 'CenterBottom', color = O, clip = 170 })
  H.text(1, 4, z.w, 2, string.format('%.0f%% CPU', cpu), { size = 10, font = H.fontNum, align = 'RightTop', color = O })
  H.text(1, 5, 0, 2, 'LOCK', { size = 9, font = H.fontTitle, weight = 700, color = O })
  H.hit(1, 1, 0, 0, z.w, z.h, 'Target ' .. rank .. ': ' .. name .. '  - click: next target, right-click: Task Manager')
  c:flush()
  return cpu
end

function OnClick(z, k) rank = rank % 5 + 1; Update() end
function OnRightClick(z, k) SKIN:Bang('["taskmgr.exe"]') end
function OnScroll(z, k, d) rank = (rank - 1 + d) % 5 + 1; Update() end
function OnHover(z, k, on) end
