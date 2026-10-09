-- Big category panel (L_category / R_category, 440 x 400) + page dots (160 x 20).
local H, A
local panel, mirror = 1, false
local cat, sel, first = nil, 1, 1
local spin = 0
local MAXTABS = 6

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

function Update()
  H.refreshTier()
  local z = H.zones[1]
  local c = H.canvas(1)
  local A1, D, T = H.C.accent, H.C.dim, H.C.text
  local app = current()
  if H.tier == 0 then spin = (spin + 9) % 360 end
  -- tab strip (reference: OVR WEAP AVI PWR SHLD COMM)
  local n = cat and #cat.apps or 0
  local vis = math.min(MAXTABS, n)
  local arrows = n > MAXTABS
  local x0, x1 = arrows and 18 or 0, z.w - (arrows and 18 or 0)
  local tw = vis > 0 and (x1 - x0) / vis or 0
  c:line(0, 30, z.w, 30, D, 1, 200)
  for t = 1, MAXTABS do
    local i = first + t - 1
    if t <= vis and cat.apps[i] then
      local x = x0 + (t - 1) * tw
      local on = (i == sel)
      if on then
        c:fillPoly({ { x + 4, 4 }, { x + tw - 4, 4 }, { x + tw, 30 }, { x, 30 } }, A1, 34)
        c:line(x + 2, 30, x + tw - 2, 30, A1, 2.2)
      end
      H.text(1, t, x + tw / 2, 17, cat.apps[i].short, { size = 9, align = 'CenterCenter', weight = 700, color = on and T or D, clip = tw - 2 })
      H.hit(1, t, x, 0, tw, 32, cat.apps[i].name)
    else
      H.hideText(1, t); H.hideHit(1, t)
    end
  end
  if arrows then
    c:poly({ { 12, 9 }, { 4, 17 }, { 12, 25 } }, A1, 1.6)
    c:poly({ { z.w - 12, 9 }, { z.w - 4, 17 }, { z.w - 12, 25 } }, A1, 1.6)
    H.hit(1, 7, 0, 0, 18, 32, 'Previous'); H.hit(1, 8, z.w - 18, 0, 18, 32, 'Next')
  else H.hideHit(1, 7); H.hideHit(1, 8) end
  -- wireframe display
  local gx = mirror and 304 or 136
  local gy = 182
  c:circle(gx, gy, 116, D, 1, 150)
  c:arc(gx, gy, 102, spin, spin + 70, A1, 2)
  c:arc(gx, gy, 102, spin + 180, spin + 250, A1, 2)
  c:circle(gx, gy, 86, D, 1, 90)
  for a = 0, 330, 30 do
    local r1, r2 = 116, (a % 90 == 0) and 128 or 122
    local ca, sa = math.cos(math.rad(a)), math.sin(math.rad(a))
    c:hair(gx + r1 * ca, gy + r1 * sa, gx + r2 * ca, gy + r2 * sa, A1, 1.2, 200)
  end
  c:hair(gx - 128, gy, gx - 92, gy, D, 1, 160); c:hair(gx + 92, gy, gx + 128, gy, D, 1, 160)
  if app then
    c:icon(app.icon, gx, gy, 136, app.missing and D or A1, 2)
  else
    H.text(1, 9, gx, gy, 'NO APPS', { size = 12, align = 'CenterCenter', color = D, font = H.fontTitle })
  end
  -- info column
  local cx = mirror and 4 or 272
  local cw = 160
  local al = mirror and 'LeftTop' or 'LeftTop'
  if app then
    local running = false
    if app.proc ~= '' then
      H.set('mProc', 'ProcessName', app.proc)
      running = H.val('mProc', -1) > 0
    end
    H.text(1, 9, cx, 60, string.upper(app.name), { size = (#app.name > 11) and 10 or 12, font = H.fontTitle, weight = 700, color = T, clip = cw, align = al })
    H.text(1, 10, cx, 88, app.info, { size = 9.5, color = D, clip = cw, align = al })
    local scol = app.missing and H.C.warn or (running and H.C.good or A1)
    c:dot(cx + 5, 124, 4, scol)
    H.text(1, 11, cx + 14, 116, app.missing and 'NOT FOUND' or (running and 'RUNNING' or 'READY'), { size = 9.5, weight = 700, color = scol })
    H.text(1, 12, cx, 140, string.format('%02d / %02d', sel, n), { size = 9, font = H.fontNum, color = D })
    -- launch button
    c:chamfer(cx, 266, cw, 36, 8, A1, 1.6, 255, 150)
    H.text(1, 13, cx + cw / 2, 284, 'LAUNCH', { size = 11, align = 'CenterCenter', font = H.fontTitle, weight = 700, color = A1 })
    H.hit(1, 9, cx, 266, cw, 36, 'Launch ' .. app.name)
    H.hit(1, 10, gx - 100, gy - 100, 200, 200, 'Launch ' .. app.name .. '  (scroll to switch app)')
  else
    for k = 10, 13 do H.hideText(1, k) end
    H.hideHit(1, 9); H.hideHit(1, 10)
  end
  -- category footer
  c:line(0, 350, z.w, 350, D, 1, 200)
  c:poly({ { 0, 350 }, { 10, 340 }, { 150, 340 }, { 160, 350 } }, A1, 1.4)
  H.text(1, 14, 0, 358, cat and cat.name or 'NO CATEGORY', { size = 11, font = H.fontTitle, weight = 700, color = A1, clip = z.w - 80 })
  c:dot(z.w - 6, 368, 3, A1)
  c:flush()
  -- page dots (zone 2)
  local d = H.canvas(2)
  local zz = H.zones[2]
  local count = math.min(#A.catOrder, 8)
  local step = zz.w / math.max(count, 1)
  for i = 1, count do
    local id = A.catOrder[i]
    local x = step * (i - 0.5)
    if cat and id == cat.id then d:dot(x, 10, 5, A1) else d:circle(x, 10, 4, D, 1.2) end
    H.hit(2, i, x - step / 2, 0, step, 20, A.cats[id].name)
  end
  for i = count + 1, 8 do H.hideHit(2, i) end
  d:flush()
  return 0
end

local function launch()
  local app = current()
  if app then A.launch(app) end
end

function OnClick(zi, k)
  if zi == 2 then
    local id = A.catOrder[k]
    if id then cat = A.cats[id]; first = 1; sel = tonumber(A.getState('Sel_' .. id, '1')) or 1; A.setState('TopCat' .. panel, id) end
  elseif k <= 6 then choose(first + k - 1)
  elseif k == 7 then choose(sel - 1)
  elseif k == 8 then choose(sel + 1)
  else launch() end
  Update()
end

function OnRightClick(zi, k)
  if zi == 1 and k <= 6 and cat and cat.apps[first + k - 1] then A.launch(cat.apps[first + k - 1]) end
end

function OnScroll(zi, k, dir)
  if zi == 1 then choose(sel + dir); Update() end
end

function OnHover(zi, k, on) end
