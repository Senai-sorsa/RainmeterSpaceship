-- Top-right "PWR ----" bar (reference): battery level + time to the charge limit / to empty.
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
  -- reference "PWR ----" bar: label on the left, rail rising to the right, fill from the left,
  -- percentage and time-to-limit small above the far end
  local y = z.h * 0.76
  local x0, x1 = 48, z.w
  H.text(1, 1, 0, y, 'PWR', { size = 8.5, weight = 700, align = 'LeftCenter', color = H.C.white })
  c:line(x0, y, x1, y, H.C.white, 1.3, 200)
  local low = (not ac) and pct <= H.num('WarnBattery', 20)
  c:line(x0, y, x0 + (x1 - x0) * pct / 100, y, low and H.C.alert or (ac and H.C.good or H.C.hi), 2.6)
  local lx = x0 + (x1 - x0) * limit / 100
  c:line(lx, y - 6, lx, y + 3, H.C.white, 1.2, 200)
  -- readout above the start of the rail, clear of the bar's far end and the limit tick
  H.text(1, 2, x0, 0, string.format('%d%%  %s', pct, status), { size = 4.8, weight = 700, align = 'LeftTop', color = H.C.white, alpha = 210, clip = (x1 - x0) * 0.7 })
  H.hideText(1, 3)
  H.hit(1, 1, 0, 0, z.w, z.h, string.format('Battery %d%% - %s', pct, status))
  c:flush()
  return pct
end

function OnClick(z, k) SKIN:Bang('["ms-settings:batterysaver"]') end
function OnRightClick(z, k) end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
