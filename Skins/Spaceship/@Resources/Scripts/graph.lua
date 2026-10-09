-- Top console history graph. Zone 280/300 x 80.
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
  local col = H.ramp(norm[#norm] or 0)
  local w1, w2 = string.match(def.label, '^(%S+)%s+(.+)$')
  local faint = H.C.dim
  -- faint history behind the label
  if #norm >= 2 then
    local pad = {}
    for i = 1, N - #norm do pad[i] = 0 end
    for _, x in ipairs(norm) do pad[#pad + 1] = x end
    local pts = {}
    for i = 1, #pad do pts[i] = { 6 + (i - 1) * (z.w - 12) / (#pad - 1), z.h - 4 - pad[i] * (z.h - 10) } end
    local area = { { 6, z.h - 4 } }
    for _, p in ipairs(pts) do area[#area + 1] = p end
    area[#area + 1] = { z.w - 6, z.h - 4 }
    c:fillPoly(area, col, 26)
    c:hairPoly(pts, col, 110, 1.2)
  end
  H.text(1, 1, z.w / 2, z.h * 0.12, w1 or def.label, { size = 10, weight = 700, align = 'CenterCenter', color = faint, alpha = 200 })
  H.text(1, 2, z.w / 2, z.h * 0.45, w2 or '', { size = 10, weight = 700, align = 'CenterCenter', color = faint, alpha = 200 })
  H.text(1, 3, z.w - 4, z.h - 2, txt or '--', { size = 5.4, weight = 700, align = 'RightBottom', color = v and H.C.white or H.C.dim })
  H.hideText(1, 4)
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
