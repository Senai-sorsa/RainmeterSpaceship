-- Target lock (reference orange reticle at 657,203 with [2] 567m). Animated at 20 fps on FULL tier:
-- outer ring rotates, inner ring breathes, and the reticle zooms in to lock whenever the target changes.
local H
local rank, frame = 1, 0
local lastName, lockAnim = '', 0
local name, cpu, ram = '', 0, 0
local SXR, SYR = 2560 / 1260, 1600 / 709

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function sample()
  local threads = math.max(1, H.val('mThreads', 20))
  name = string.gsub(H.sval('mTop' .. rank, ''), '#%d+$', '')
  cpu = H.val('mTop' .. rank, 0) / threads
  H.set('mTargetRam', 'Name', name ~= '' and name or 'explorer')
  ram = H.val('mTargetRam', 0)
  if name ~= lastName then lastName, lockAnim = name, 18 end
end

function Update()
  frame = frame + 1
  if frame % 20 == 1 then H.refreshTier(); sample() end
  local animate = H.tier == 0
  if not animate and frame % 20 ~= 1 then return 0 end
  local c = H.canvas(1)
  local O = H.C.warn
  local function X(rx) return (rx - 583) * SXR end
  local function Y(ry) return (ry - 155) * SYR end
  local cx, cy = X(657), Y(203)
  local t = frame * 0.05
  local zoom = 1
  if lockAnim > 0 then zoom = 1 + lockAnim / 18 * 0.1; lockAnim = lockAnim - (animate and 1 or 18) end
  local rot = animate and (frame * 1.2) % 360 or 0
  -- outer ring: two long arcs with gaps (reference), rotating
  local R = 86 * zoom
  for q = 0, 1 do
    local a0 = rot + q * 180 + 18
    c:arc(cx, cy, R, a0, a0 + 144, O, 1.8, 235)
  end
  -- short tick marks in the gaps
  for q = 0, 1 do
    local a = math.rad(rot + q * 180)
    c:line(cx + (R - 7) * math.cos(a), cy + (R - 7) * math.sin(a), cx + (R + 3) * math.cos(a), cy + (R + 3) * math.sin(a), O, 1.6)
  end
  -- inner lock ring: thick, breathing, thicker with CPU share
  local pulse = animate and (math.sin(t * 2) * 0.06) or 0
  local r2 = 36 * (1 + pulse) * (zoom > 1 and zoom * 0.9 or 1)
  -- double lock ring with a blue core (reference)
  local thick = 4 + 3 * H.clamp(cpu / 50, 0, 1)
  c:circle(cx, cy, r2, O, thick)
  c:circle(cx, cy, r2 - thick - 4, H.mix(O, H.C.white, 0.35), thick * 0.7, 230)
  c:fillCircle(cx, cy, r2 - 2 * thick - 6, { 20, 60, 140 }, 150)
  c:dot(cx, cy, 3.5, H.C.accent)
  -- [n] box + memory readout
  local bx0, by0, bx1, by1 = X(597), Y(192), X(608), Y(203)
  local flash = lockAnim > 0 and (lockAnim % 4 < 2)
  c:rect(bx0, by0, bx1 - bx0, by1 - by0, O, 1.8, flash and 120 or 255)
  H.text(1, 1, (bx0 + bx1) / 2, (by0 + by1) / 2, tostring(rank), { size = 8, weight = 700, align = 'CenterCenter', color = O })
  H.text(1, 2, (bx0 + bx1) / 2 - 2, Y(210), ram > 0 and string.format('%.0fm', ram / 1048576) or '--', { size = 7.5, weight = 700, align = 'CenterCenter', color = O })
  H.hideText(1, 3)
  if frame % 20 == 1 then
    H.hit(1, 1, 0, 0, H.zones[1].w, H.zones[1].h, string.format('Target %d: %s  %.0f%% CPU  %.0f MB  - click: next target, right-click: Task Manager', rank, name, cpu, ram / 1048576))
  end
  c:flush()
  return cpu
end

function OnClick(z, k) rank = rank % 5 + 1; frame = 0; Update() end
function OnRightClick(z, k) SKIN:Bang('["taskmgr.exe"]') end
function OnScroll(z, k, d) rank = (rank - 1 + d) % 5 + 1; frame = 0; Update() end
function OnHover(z, k, on) end
