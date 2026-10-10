-- Data sources shared by the graphs, HUD and strip.
-- get(H) -> value, text   (value nil = sensor not available)
-- frac(x) -> 0..1 position of a value on the graph (auto-scaled sources omit it)
-- axis = { lo, hi, unit caption } for the instrument scale; auto-scaled sources give unit only
local S = {}

local function pct(v) return string.format('%.0f%%', v) end
local function lin(lo, hi) return function(x) return (x - lo) / (hi - lo) end end

S.order = { 'cpu', 'ram', 'gpu', 'vram', 'cputemp', 'gputemp', 'power', 'disk', 'netdown', 'netup', 'battery' }

S.defs = {
  cpu = { label = 'CPU LOAD', axis = { 0, 100, 'PERCENT' }, frac = lin(0, 100), get = function(H) local v = H.val('mCPU', 0); return v, pct(v) end },
  ram = { label = 'MEMORY USED', axis = { 0, 100, 'PERCENT' }, frac = lin(0, 100), get = function(H)
    local u, t = H.val('mRamUsed', 0), math.max(1, H.val('mRamTotal', 1))
    return u / t * 100, string.format('%.1f / %.0f GB', u / 1073741824, t / 1073741824) end },
  gpu = { label = 'GPU LOAD', axis = { 0, 100, 'PERCENT' }, frac = lin(0, 100), get = function(H) local v = H.clamp(H.val('mGPU', 0), 0, 100); return v, pct(v) end },
  vram = { label = 'VIDEO MEMORY', axis = { 0, 12, 'GIGABYTES' }, frac = lin(0, 12 * 1073741824), get = function(H)
    local b = H.val('mVRAM', 0); return b, string.format('%.1f GB', b / 1073741824) end },
  cputemp = { label = 'CPU TEMP', axis = { 30, 100, 'DEGREES C' }, frac = lin(30, 100), get = function(H)
    local v = H.hw('mHwCpuTemp'); if not v then return nil end; return v, string.format('%.0f C', v) end },
  gputemp = { label = 'GPU TEMP', axis = { 30, 90, 'DEGREES C' }, frac = lin(30, 90), get = function(H)
    local v = H.hw('mHwGpuTemp'); if not v then return nil end; return v, string.format('%.0f C', v) end },
  power = { label = 'POWER DRAW', axis = { 0, 160, 'WATTS' }, frac = lin(0, 160), get = function(H)
    local c, g = H.hw('mHwCpuPower'), H.hw('mHwGpuPower'); if not (c or g) then return nil end
    local v = (c or 0) + (g or 0); return v, string.format('%.0f W', v) end },
  disk = { label = 'DISK I/O', unit = 'PER SEC', get = function(H) local v = H.val('mDiskRead', 0) + H.val('mDiskWrite', 0); return v, H.rate(v) end },
  netdown = { label = 'NET DOWN', unit = 'MBPS', get = function(H) local v = H.val('mNetIn', 0); return v, H.mbps(v) end },
  netup = { label = 'NET UP', unit = 'MBPS', get = function(H) local v = H.val('mNetOut', 0); return v, H.mbps(v) end },
  battery = { label = 'BATTERY LEVEL', axis = { 0, 100, 'PERCENT' }, frac = lin(0, 100), get = function(H) local v = H.val('mBattPct', 0); return v, pct(v) end },
}

function S.next(id, dir)
  for i, k in ipairs(S.order) do
    if k == id then return S.order[(i - 1 + dir) % #S.order + 1] end
  end
  return S.order[1]
end

-- normalise a history list for drawing (auto-scales sources without frac)
function S.normalise(def, hist, H)
  local out = {}
  if def.frac then
    for i, x in ipairs(hist) do out[i] = H.clamp(def.frac(x), 0, 1) end
  else
    local peak = 1
    for _, x in ipairs(hist) do if x > peak then peak = x end end
    for i, x in ipairs(hist) do out[i] = x / (peak * 1.1) end
  end
  return out
end

return S
