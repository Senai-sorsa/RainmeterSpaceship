-- Top console history graph instrument.
-- Script options: Mode=fixed|select, Source=<source id> (fixed) or <variable name> (select)
local H, SRC
local hist, mode, srcVar, src = {}, 'fixed', nil, 'cpu'
local N = 48

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  SRC = dofile(SKIN:GetVariable('@') .. 'Scripts\\sources.lua')
  H.init()
  mode = SELF:GetOption('Mode', 'fixed')
  if mode == 'select' then
    srcVar = SELF:GetOption('Source', 'GraphA_Source')
    src = H.str(srcVar, 'gpu')
  else
    src = SELF:GetOption('Source', 'cpu')
  end
  if not SRC.defs[src] then src = 'cpu' end
end

local function setSource(id)
  src, hist = id, {}
  H.save(srcVar, id)
end

local function fmtAxis(x)
  if x >= 1e9 then return string.format('%.0fG', x / 1e9) end
  if x >= 1e6 then return string.format('%.0fM', x / 1e6) end
  if x >= 1e3 then return string.format('%.0fK', x / 1e3) end
  return string.format('%.0f', x)
end

-- Instrument layout (Hornet gauge language): label + readout header, a ticked scale with numerals on the
-- left, gridlines, the history trace with an area fill, a pointer on the scale at the current value, and
-- the unit caption underneath.
function Update()
  H.refreshTier()
  local c = H.canvas(1)
  local def = SRC.defs[src]
  local v, txt = def.get(H)
  if v ~= nil then
    hist[#hist + 1] = v
    if #hist > N then table.remove(hist, 1) end
  end
  local norm = SRC.normalise(def, hist, H)
  local z = H.zones[1]
  local cur = norm[#norm] or 0
  local col = H.ramp(cur)
  local gx0, gx1, gy0, gy1 = 38, z.w - 8, 22, z.h - 14
  local gh = gy1 - gy0
  -- scale: spine, major / minor ticks, faint gridlines
  c:hair(gx0 - 5, gy0, gx0 - 5, gy1, H.C.text, 1, 150)
  for i = 0, 4 do
    local y = gy1 - gh * i / 4
    local major = i % 2 == 0
    c:hair(gx0 - (major and 11 or 8), y, gx0 - 5, y, H.C.text, major and 1.6 or 1, major and 220 or 140)
    if i > 0 and i < 4 then c:hair(gx0, y, gx1, y, H.C.dim, 1, i == 2 and 46 or 26) end
  end
  c:hair(gx0, gy1, gx1, gy1, H.C.dim, 1, 90)
  -- history trace
  if #norm >= 2 then
    local pad = {}
    for i = 1, N - #norm do pad[i] = 0 end
    for _, x in ipairs(norm) do pad[#pad + 1] = x end
    local pts = {}
    for i = 1, #pad do pts[i] = { gx0 + (i - 1) * (gx1 - gx0) / (#pad - 1), gy1 - H.clamp(pad[i], 0, 1) * gh } end
    local area = { { gx0, gy1 } }
    for _, p in ipairs(pts) do area[#area + 1] = p end
    area[#area + 1] = { gx1, gy1 }
    c:fillPoly(area, col, 34)
    c:poly(pts, col, 1.3)
    c:dot(pts[#pts][1], pts[#pts][2], 2.2, col, 255)
  end
  -- pointer on the scale at the current value
  local py = gy1 - H.clamp(cur, 0, 1) * gh
  c:fillPoly({ { gx0 - 4, py }, { gx0 - 11, py - 4 }, { gx0 - 11, py + 4 } }, col, 255)
  -- scale numerals and captions
  local lo, hi, unit
  if def.axis then
    lo, hi, unit = def.axis[1], def.axis[2], def.axis[3]
  else
    local peak = 1
    for _, x in ipairs(hist) do if x > peak then peak = x end end
    lo, hi, unit = 0, peak * 1.1, (def.unit or '') .. '  AUTO'
  end
  H.text(1, 1, 8, 10, def.label, { size = 4.4, weight = 700, align = 'LeftCenter', color = H.C.text, alpha = 230 })
  H.text(1, 2, z.w - 8, 10, txt or '--', { size = 5.2, weight = 700, align = 'RightCenter', font = H.fontNum, color = v and H.C.white or H.C.dim })
  H.text(1, 3, gx0 - 13, gy0, fmtAxis(hi), { size = 3.9, weight = 600, align = 'RightCenter', font = H.fontNum, color = H.C.text, alpha = 200, glow = false })
  H.text(1, 4, gx0 - 13, (gy0 + gy1) / 2, fmtAxis((lo + hi) / 2), { size = 3.9, weight = 600, align = 'RightCenter', font = H.fontNum, color = H.C.text, alpha = 160, glow = false })
  H.text(1, 5, gx0 - 13, gy1, fmtAxis(lo), { size = 3.9, weight = 600, align = 'RightCenter', font = H.fontNum, color = H.C.text, alpha = 200, glow = false })
  H.text(1, 6, gx0, z.h - 5, unit .. '   60 S', { size = 3.5, weight = 600, align = 'LeftCenter', color = H.C.dim, alpha = 220, glow = false })
  if mode == 'select' then
    -- selectable source: small chevrons bottom-right
    c:poly({ { z.w - 22, z.h - 8 }, { z.w - 18, z.h - 5 }, { z.w - 22, z.h - 2 } }, H.C.accent, 1.2, 200)
    c:poly({ { z.w - 14, z.h - 8 }, { z.w - 10, z.h - 5 }, { z.w - 14, z.h - 2 } }, H.C.accent, 1.2, 200)
  end
  H.hit(1, 1, 0, 0, z.w, z.h, def.label .. (mode == 'select' and '  - click: next source, right-click: previous' or ''))
  c:flush()
  return v or 0
end

function OnClick(zi, k)
  if mode == 'select' then setSource(SRC.next(src, 1)); Update() end
end
function OnRightClick(zi, k)
  if mode == 'select' then setSource(SRC.next(src, -1)); Update() end
end
function OnScroll(zi, k, d)
  if mode == 'select' then setSource(SRC.next(src, d)); Update() end
end
function OnHover(zi, k, on) end
