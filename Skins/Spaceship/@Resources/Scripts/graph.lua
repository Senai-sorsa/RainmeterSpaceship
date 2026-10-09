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

-- Plate layout after the reference's OXYGEN LEVEL / INTERNAL PRESSURE plates: a big ghosted two-line label
-- centred on the plate, the history as a faint trace behind it, faint scale ticks on the left edge and a
-- small live readout bottom-right. Selectable plates show two small chevrons.
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
  local gx0, gx1, gy0, gy1 = 14, z.w - 8, 8, z.h - 8
  local gh = gy1 - gy0
  -- faint scale ticks on the left edge (major at 0 / 50 / 100 %)
  for i = 0, 4 do
    local y = gy1 - gh * i / 4
    c:hair(4, y, i % 2 == 0 and 11 or 8, y, H.C.dim, 1, i % 2 == 0 and 150 or 90)
  end
  -- history: faint area + thin line behind the label
  if #norm >= 2 then
    local pad = {}
    for i = 1, N - #norm do pad[i] = 0 end
    for _, x in ipairs(norm) do pad[#pad + 1] = x end
    local pts = {}
    for i = 1, #pad do pts[i] = { gx0 + (i - 1) * (gx1 - gx0) / (#pad - 1), gy1 - H.clamp(pad[i], 0, 1) * gh } end
    local area = { { gx0, gy1 } }
    for _, p in ipairs(pts) do area[#area + 1] = p end
    area[#area + 1] = { gx1, gy1 }
    c:fillPoly(area, col, 22)
    c:hairPoly(pts, col, 150, 1.3)
    c:dot(pts[#pts][1], pts[#pts][2], 2.2, col, 230)
  end
  -- ghosted label (reference plates: large faint blue capitals)
  local w1, w2 = string.match(def.label, '^(%S+)%s+(.+)$')
  local ghost = { 40, 82, 150 }
  H.text(1, 1, z.w / 2, z.h * 0.30, w1 or def.label, { size = 10, weight = 700, align = 'CenterCenter', color = ghost, alpha = 235, glow = false })
  H.text(1, 2, z.w / 2, z.h * 0.62, w2 or '', { size = 10, weight = 700, align = 'CenterCenter', color = ghost, alpha = 235, glow = false })
  H.text(1, 3, z.w - 6, z.h - 6, txt or '--', { size = 4.6, weight = 700, align = 'RightBottom', font = H.fontNum, color = v and H.C.white or H.C.dim })
  for t = 4, 6 do H.hideText(1, t) end
  if mode == 'select' then
    c:poly({ { 8, z.h - 9 }, { 12, z.h - 6 }, { 8, z.h - 3 } }, H.C.accent, 1.1, 200)
    c:poly({ { 14, z.h - 9 }, { 18, z.h - 6 }, { 14, z.h - 3 } }, H.C.accent, 1.1, 200)
  end
  H.hit(1, 1, 0, 0, z.w, z.h, def.label .. '  ' .. (txt or '') .. (mode == 'select' and '  - click: next source, right-click: previous' or ''))
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
