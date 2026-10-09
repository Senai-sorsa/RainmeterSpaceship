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
  local z = H.zones[1]
  local c = H.canvas(1)
  local def = SRC.defs[src]
  local v, txt = def.get(H)
  if v ~= nil then
    hist[#hist + 1] = v
    if #hist > N then table.remove(hist, 1) end
  end
  local norm = SRC.normalise(def, hist, H)
  local col = H.ramp(norm[#norm] or 0)
  -- title plate (reference: "OXYGEN LEVEL" plates)
  local title = def.label
  c:fillPoly({ { 0, 0 }, { 150, 0 }, { 140, 18 }, { 0, 18 } }, H.C.panel, 140)
  c:poly({ { 0, 18 }, { 0, 0 }, { 150, 0 }, { 140, 18 } }, H.C.dim, 1, 200)
  H.text(1, 1, 6, 1, title, { size = 9.5, color = H.C.accent, font = H.fontTitle, weight = 700 })
  if mode == 'select' then
    H.text(1, 4, 156, 3, '< >', { size = 8, color = H.C.dim, font = H.fontNum })
  else H.hideText(1, 4) end
  H.text(1, 2, z.w, 0, txt or '--', { size = 11, align = 'RightTop', font = H.fontNum, color = v and H.C.text or H.C.dim })
  -- graph body
  local gx, gy, gw, gh = 0, 24, z.w, z.h - 26
  c:fillRect(gx, gy, gw, gh, H.C.panel, 70)
  for i = 1, 3 do c:hair(gx, gy + gh * i / 4, gx + gw, gy + gh * i / 4, H.C.dim, 1, 60) end
  for i = 1, 7 do c:hair(gx + gw * i / 8, gy, gx + gw * i / 8, gy + gh, H.C.dim, 1, 40) end
  c:brackets(gx, gy, gw, gh, 8, H.C.accent, 1.2, 200)
  if #norm >= 2 then
    local pad = {}
    for i = 1, N - #norm do pad[i] = 0 end
    for _, x in ipairs(norm) do pad[#pad + 1] = x end
    c:graph(gx + 2, gy + 2, gw - 4, gh - 4, pad, col, 46)
  end
  if v == nil then
    H.text(1, 3, gw / 2, gy + gh / 2, 'NO SENSOR - MAP HWINFO IN CONTROL CENTER', { size = 8, align = 'CenterCenter', color = H.C.dim })
  else H.hideText(1, 3) end
  H.hit(1, 1, 0, 0, z.w, 20, mode == 'select' and 'Click: next source   Right-click: previous' or def.label)
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
