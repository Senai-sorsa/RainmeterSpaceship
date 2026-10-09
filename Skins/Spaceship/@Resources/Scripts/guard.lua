-- Layout guard: the Lua twin of tools/check_layout.py, used by the Control Center before any move.
local G = {}

local function sep(a, b, gap)
  for _, poly in ipairs({ a, b }) do
    for i = 1, #poly do
      local p1, p2 = poly[i], poly[i % #poly + 1]
      local nx, ny = p2[2] - p1[2], p1[1] - p2[1]
      local len = math.sqrt(nx * nx + ny * ny)
      if len > 0 then
        local amin, amax, bmin, bmax = math.huge, -math.huge, math.huge, -math.huge
        for _, p in ipairs(a) do local d = nx * p[1] + ny * p[2]; amin = math.min(amin, d); amax = math.max(amax, d) end
        for _, p in ipairs(b) do local d = nx * p[1] + ny * p[2]; bmin = math.min(bmin, d); bmax = math.max(bmax, d) end
        if amax + gap * len <= bmin or bmax + gap * len <= amin then return true end
      end
    end
  end
  return false
end
G.separated = sep

local function moved(poly, dx, dy)
  local out = {}
  for i, p in ipairs(poly) do out[i] = { p[1] + dx, p[2] + dy } end
  return out
end

local function inSafe(poly, Z)
  local inset, r = Z.safe.inset, Z.safe.r
  local L, T, R, B = inset, inset, Z.canvas.w - inset, Z.bottom - Z.gap
  for _, p in ipairs(poly) do
    local x, y = p[1], p[2]
    if x < L or x > R or y < T or y > B then return false end
    local cx = (x < L + r) and (L + r) or ((x > R - r) and (R - r) or nil)
    local cy = (y < T + r) and (T + r) or nil
    if cx and cy and math.sqrt((x - cx) ^ 2 + (y - cy) ^ 2) > r then return false end
  end
  return true
end

-- offsets: table key -> {dx, dy}; returns ok, reason
function G.check(Z, key, offsets)
  local mod
  for _, m in ipairs(Z.modules) do if m.key == key then mod = m end end
  if not mod then return true end
  local o = offsets[key] or { 0, 0 }
  for _, zp in ipairs(mod.zones) do
    local p = moved(zp, o[1], o[2])
    if not inSafe(p, Z) then return false, 'OFF THE SAFE AREA / INTO THE TASKBAR' end
    for ki, k in ipairs(Z.keepouts) do
      if not sep(p, k, Z.gap) then return false, 'HITS A COCKPIT STRUT' end
    end
    for _, other in ipairs(Z.modules) do
      if other.key ~= key then
        local oo = offsets[other.key] or { 0, 0 }
        for _, zq in ipairs(other.zones) do
          if not sep(p, moved(zq, oo[1], oo[2]), Z.gap) then return false, 'OVERLAPS ' .. other.name end
        end
      end
    end
  end
  return true
end

function G.checkAll(Z, offsets)
  local bad = {}
  for _, m in ipairs(Z.modules) do
    local ok, why = G.check(Z, m.key, offsets)
    if not ok then bad[#bad + 1] = m.name .. ': ' .. why end
  end
  return bad
end

return G
