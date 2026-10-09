-- Top-right battery bar, the mirror of the power bar: battery level + time to limit / to empty.
local H
local samples = {}

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function timeToLimit(pct, limit)
  local rem, full, rate = H.hw('mHwRemainCap'), H.hw('mHwFullCap'), H.hw('mHwChargeRate')
  if rem and full and rate and rate > 0.5 then
    local need = (limit / 100 * full - rem) / 1000
    if need <= 0 then return 0 end
    return need / rate * 3600
  end
  local now = os.time()
  if #samples == 0 or samples[#samples][2] ~= pct then samples[#samples + 1] = { now, pct } end
  while #samples > 2 and now - samples[1][1] > 600 do table.remove(samples, 1) end
  if #samples >= 2 then
    local dt = samples[#samples][1] - samples[1][1]
    local dp = samples[#samples][2] - samples[1][2]
    if dt > 60 and dp > 0 then return (limit - pct) / (dp / dt) end
  end
  return nil
end

function Update()
  H.refreshTier()
  local z = H.zones[1]
  local c = H.canvas(1)
  local pct = H.val('mBattPct', 0)
  local ac = H.val('mAC', 0) > 0
  local limit = H.num('ChargeLimit', 80)
  local status
  if ac then
    if pct >= limit - 1 then status = 'HELD ' .. limit .. '%'; samples = {}
    else local t = timeToLimit(pct, limit); status = t and (H.duration(t) .. ' TO ' .. limit .. '%') or ('CHG TO ' .. limit .. '%') end
  else
    samples = {}
    local life = H.val('mLifetime', -1)
    status = (life and life > 0) and (H.duration(life) .. ' LEFT') or 'ON BATT'
  end
  -- mirror image of the power bar: label on the right, rail filling from the right toward the centre
  local y = z.h * 0.62
  local x0, x1 = 26, z.w - 48
  H.text(1, 1, z.w, y, 'BAT', { size = 8.5, weight = 700, align = 'RightCenter', color = H.C.white })
  c:line(x0, y, x1, y, H.C.white, 1.3, 200)
  local low = (not ac) and pct <= H.num('WarnBattery', 20)
  c:line(x1, y, x1 - (x1 - x0) * pct / 100, y, low and H.C.alert or (ac and H.C.good or H.C.hi), 2.6)
  local lx = x1 - (x1 - x0) * limit / 100
  c:line(lx, y - 6, lx, y + 3, H.C.white, 1.2, 200)
  H.text(1, 2, 0, y, string.format('%d%%', pct), { size = 8.5, weight = 700, align = 'LeftCenter', color = H.C.white, font = H.fontNum })
  H.text(1, 3, (x0 + x1) / 2, 1, status, { size = 4.6, weight = 700, align = 'CenterTop', color = H.C.white, alpha = 200 })
  H.hit(1, 1, 0, 0, z.w, z.h, string.format('Battery %d%% - %s', pct, status))
  c:flush()
  return pct
end

function OnClick(z, k) SKIN:Bang('["ms-settings:batterysaver"]') end
function OnRightClick(z, k) end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
