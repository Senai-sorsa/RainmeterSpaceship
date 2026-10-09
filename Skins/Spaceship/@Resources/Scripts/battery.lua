-- Top-right bar: battery level + time to charge limit / time to empty. Zone T_battery (240 x 40).
local H
local samples = {}   -- {t, pct} while charging, for the slope fallback

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function timeToLimit(pct, limit)
  -- 1) HWiNFO capacities + charge rate (most accurate)
  local rem, full, rate = H.hw('mHwRemainCap'), H.hw('mHwFullCap'), H.hw('mHwChargeRate')
  if rem and full and rate and rate > 0.5 then
    -- capacities in mWh, rate in W (HWiNFO defaults)
    local need = (limit / 100 * full - rem) / 1000
    if need <= 0 then return 0 end
    return need / rate * 3600
  end
  -- 2) slope of the last ~10 minutes of % readings
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
  local status, col
  if ac then
    if pct >= limit - 1 then
      status = 'HELD AT ' .. limit .. '%'
      samples = {}
    else
      local t = timeToLimit(pct, limit)
      status = t and (H.duration(t) .. ' TO ' .. limit .. '%') or ('CHARGING TO ' .. limit .. '%')
    end
    col = H.C.good
  else
    samples = {}
    local life = H.val('mLifetime', -1)
    status = (life and life > 0) and (H.duration(life) .. ' LEFT') or 'ON BATTERY'
    col = pct <= H.num('WarnBattery', 20) and H.C.alert or H.C.accent
  end
  H.text(1, 1, 0, 0, 'BATT', { size = 10, color = H.C.accent, font = H.fontTitle, weight = 700 })
  H.text(1, 2, 52, 0, string.format('%d%%', pct), { size = 11, font = H.fontNum })
  H.text(1, 3, z.w, 1, status, { size = 9.5, align = 'RightTop', color = col })
  c:line(0, 33, z.w, 33, H.C.dim, 1, 160)
  c:line(0, 28, 0, 38, H.C.accent, 1.4)
  c:line(z.w, 28, z.w, 38, H.C.accent, 1.4)
  c:segBar(4, 22, z.w - 8, 8, pct / 100, 24, col, 2)
  -- charge-limit tick
  local lx = 4 + (z.w - 8) * limit / 100
  c:line(lx, 18, lx, 34, H.C.warn, 1.4)
  H.hit(1, 1, 0, 0, z.w, z.h, ac and 'Plugged in' or 'On battery')
  c:flush()
  return pct
end

function OnClick(z, k) SKIN:Bang('["ms-settings:batterysaver"]') end
function OnRightClick(z, k) end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
