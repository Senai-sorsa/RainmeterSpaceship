-- Category panel: tab rail (zone 1), wireframe schematic (zone 2), page selector (zone 3).
-- Reference: OVR WEAP AVI PWR SHLD COMM rail over the ship schematic (left); SUBSYS CARGO MAIL over
-- the ship with the small triangle/number glyph (right).
local H, A
local panel, mirror = 1, false
local cat, sel, first = nil, 1, 1
local frame, scan = 0, 0
local MAXTABS = 4

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  A = dofile(SKIN:GetVariable('@') .. 'Scripts\\apps.lua')
  H.init()
  A.load()
  panel = tonumber(SELF:GetOption('Panel', '1')) or 1
  mirror = SELF:GetOption('Mirror', '0') == '1'
  local id = A.getState('TopCat' .. panel, '')
  if id == '' or not A.cats[id] then id = A.layout['Top' .. panel] end
  cat = A.cats[id] or A.cats[A.catOrder[1]]
  sel = tonumber(A.getState('Sel_' .. (cat and cat.id or 'x'), '1')) or 1
end

local function current()
  if not cat or #cat.apps == 0 then return nil end
  if sel > #cat.apps then sel = 1 end
  return cat.apps[sel]
end

local function choose(i)
  if not cat or #cat.apps == 0 then return end
  sel = (i - 1) % #cat.apps + 1
  if sel < first then first = sel end
  if sel >= first + MAXTABS then first = sel - MAXTABS + 1 end
  A.setState('Sel_' .. cat.id, sel)
end

local function catIndex()
  for i, id in ipairs(A.catOrder) do if cat and id == cat.id then return i end end
  return 1
end

local function setCat(i)
  local n = #A.catOrder
  local id = A.catOrder[(i - 1) % n + 1]
  cat, first = A.cats[id], 1
  sel = tonumber(A.getState('Sel_' .. id, '1')) or 1
  A.setState('TopCat' .. panel, id)
end

local function drawTabs()
  local z = H.zones[1]
  local c = H.canvas(1)
  local A1 = H.C.accent
  -- two parallel rails with end dots
  c:line(10, 4, z.w - 4, 4, A1, 1.3, 220)
  c:line(4, z.h - 4, z.w - 8, z.h - 4, A1, 1.3, 220)
  c:dot(10, 4, 3, A1); c:dot(4, z.h - 4, 3, A1)
  c:dot(z.w - 4, 4, 3, A1); c:dot(z.w - 8, z.h - 4, 3, A1)
  local n = cat and #cat.apps or 0
  local vis = math.min(MAXTABS, n)
  local step = (z.w - 20) / MAXTABS
  for t = 1, 6 do
    local i = first + t - 1
    if t <= vis and cat.apps[i] then
      local on = i == sel
      local x = 14 + (t - 1) * step + (mirror and (MAXTABS - vis) * step or 0)
      H.text(1, t, x, z.h / 2, cat.apps[i].short, { size = 6.2, weight = 700, align = 'LeftCenter',
        color = on and H.C.accent or { 175, 190, 200 }, alpha = on and 255 or 210, clip = step - 4 })
      H.hit(1, t, x - 2, 6, step, z.h - 12, cat.apps[i].name)
    else H.hideText(1, t); H.hideHit(1, t) end
  end
  if n > MAXTABS then
    H.hit(1, 7, 0, 0, 12, z.h, 'Previous app'); H.hit(1, 8, z.w - 12, 0, 12, z.h, 'Next app')
  else H.hideHit(1, 7); H.hideHit(1, 8) end
  c:flush()
end

local function drawSchematic(app)
  local z = H.zones[2]
  local c = H.canvas(2)
  local A1, D = H.C.accent, H.C.dim
  local cx, cy = z.w / 2, z.h / 2
  local sz = math.min(z.w, z.h) * 0.94
  if app then
    H.hideText(2, 1)
    -- hologram colour: pale ice-cyan like the reference schematics (theme colour pulled toward white)
    local col = app.missing and D or H.mix(A1, H.C.white, 0.45)
    -- dense wireframe: outer shell, inner shell, offset ghost
    c:icon(app.icon, cx, cy, sz, col, 2.4)
    c:icon(app.icon, cx, cy, sz * 0.86, col, 1.2, 150)
    c:icon(app.icon, cx, cy, sz * 0.7, col, 1, 90)
    c:icon(app.icon, cx + 3, cy - 3, sz * 0.94, H.C.white, 0.8, 70)
    -- bracket marks at the extremities (reference [ ] marks on wing tips)
    local h2 = sz * 0.5
    for _, p in ipairs({ { -1, -1 }, { 1, -1 }, { 1, 1 }, { -1, 1 } }) do
      local x, y = cx + p[1] * h2, cy + p[2] * h2 * 0.92
      c:poly({ { x - p[1] * 10, y }, { x, y }, { x, y - p[2] * 10 } }, H.C.white, 1.4, 220)
    end
    -- running: red core like the reference's highlighted section
    if app.proc ~= '' then
      H.set('mProc', 'ProcessName', app.proc)
      if H.val('mProc', -1) > 0 then
        c:icon(app.icon, cx, cy, sz * 0.32, H.C.hi, 2.2)
        c:fillCircle(cx, cy, sz * 0.08, H.C.hi, 120)
      end
    end
    -- scan line (FULL tier only)
    if H.tier == 0 then
      local y = (scan % 100) / 100 * z.h
      c:hair(cx - h2, y, cx + h2, y, A1, 1.5, 90)
      c:hair(cx - h2, y - 6, cx + h2, y - 6, A1, 1, 35)
    end
    H.hit(2, 1, cx - h2, cy - h2, 2 * h2, 2 * h2, 'Launch ' .. app.name .. (app.missing and '  (not found - RESCAN in Control Center)' or '') .. '   scroll: next app')
  else
    H.text(2, 1, cx, cy, 'NO APPS', { size = 10, weight = 700, align = 'CenterCenter', color = D })
  end
  c:flush()
end

local function drawPager()
  local z = H.zones[3]
  local c = H.canvas(3)
  local A1, D = H.C.accent, { 170, 185, 195 }
  local idx = catIndex()
  local count = math.min(#A.catOrder, 8)
  local step = z.w / count
  for i = 1, count do
    local x = step * (i - 0.5)
    local dy = z.h * 0.21
    if i == idx then c:dot(x, dy, 4, A1) else c:dot(x, dy, 3, D, 150) end
    H.hit(3, i, x - step / 2, 0, step, z.h, A.cats[A.catOrder[i]].name)
  end
  c:flush()
end

function Update()
  frame = frame + 1
  if frame % 10 == 1 then H.refreshTier() end
  scan = scan + 1.5
  if frame % 10 == 1 then
    drawTabs()
    drawPager()
  end
  if H.tier == 0 or frame % 10 == 1 then drawSchematic(current()) end
  return 0
end

local function redraw() frame = 0; Update() end

function OnClick(zi, k)
  if zi == 3 then
    setCat(k)
  elseif zi == 2 then
    local app = current(); if app then A.launch(app) end
  elseif k <= 6 then choose(first + k - 1)
  elseif k == 7 then choose(sel - 1)
  elseif k == 8 then choose(sel + 1) end
  redraw()
end

function OnRightClick(zi, k)
  if zi == 1 and k <= 6 and cat and cat.apps[first + k - 1] then A.launch(cat.apps[first + k - 1]) end
end

function OnScroll(zi, k, dir)
  if zi == 3 then setCat(catIndex() + dir) else choose(sel + dir) end
  redraw()
end

function OnHover(zi, k, on) end
