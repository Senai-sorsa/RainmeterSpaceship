-- App slot (420 x 104): a single app, or a category with a tab line.
local H, A
local slot, mirror = 1, false
local entry, sel, first = nil, 1, 1
local MAXTABS = 5

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  A = dofile(SKIN:GetVariable('@') .. 'Scripts\\apps.lua')
  H.init()
  A.load()
  slot = tonumber(SELF:GetOption('Slot', '1')) or 1
  mirror = SELF:GetOption('Mirror', '0') == '1'
  entry = A.entry(A.layout['Slot' .. slot] or '')
  if entry and entry.kind == 'cat' then
    sel = tonumber(A.getState('Sel_' .. entry.cat.id, '1')) or 1
  end
end

local function current()
  if not entry then return nil end
  if entry.kind == 'app' then return entry.app end
  local apps = entry.cat.apps
  if #apps == 0 then return nil end
  if sel > #apps then sel = 1 end
  return apps[sel]
end

local function choose(i)
  if not entry or entry.kind ~= 'cat' or #entry.cat.apps == 0 then return end
  local n = #entry.cat.apps
  sel = (i - 1) % n + 1
  if sel < first then first = sel end
  if sel >= first + MAXTABS then first = sel - MAXTABS + 1 end
  A.setState('Sel_' .. entry.cat.id, sel)
end

function Update()
  H.refreshTier()
  local z = H.zones[1]
  local c = H.canvas(1)
  local A1, D, T = H.C.accent, H.C.dim, H.C.text
  local app = current()
  local isCat = entry and entry.kind == 'cat'
  local top = isCat and 26 or 0
  -- panel outline: chamfered card + slot number (reference weapon/target cards)
  local pts
  if mirror then
    pts = { { 0, top }, { z.w - 14, top }, { z.w, top + 14 }, { z.w, z.h }, { 14, z.h }, { 0, z.h - 14 } }
  else
    pts = { { 14, top }, { z.w, top }, { z.w, z.h - 14 }, { z.w - 14, z.h }, { 0, z.h }, { 0, top + 14 } }
  end
  c:fillPoly(pts, H.C.panel, 120)
  c:poly(pts, D, 1.2, 230, true)
  local nx = mirror and z.w - 10 or 10
  H.text(1, 12, nx, z.h - 4, tostring(slot), { size = 12, font = H.fontNum, align = mirror and 'RightBottom' or 'LeftBottom', color = A1 })
  -- tab line for categories
  if isCat then
    local apps = entry.cat.apps
    local n = #apps
    local vis = math.min(MAXTABS, n)
    local arrows = n > MAXTABS
    local x0, x1 = arrows and 16 or 0, z.w - (arrows and 16 or 0)
    local tw = vis > 0 and (x1 - x0) / vis or 0
    c:line(0, 22, z.w, 22, D, 1, 200)
    for t = 1, MAXTABS do
      local i = first + t - 1
      if t <= vis and apps[i] then
        local x = x0 + (t - 1) * tw
        local on = i == sel
        if on then c:line(x + 2, 22, x + tw - 2, 22, A1, 2) end
        H.text(1, t, x + tw / 2, 11, apps[i].short, { size = 8.5, align = 'CenterCenter', weight = 700, color = on and T or D, clip = tw - 2 })
        H.hit(1, t, x, 0, tw, 24, apps[i].name)
      else H.hideText(1, t); H.hideHit(1, t) end
    end
    if arrows then
      c:poly({ { 10, 5 }, { 3, 11 }, { 10, 17 } }, A1, 1.4)
      c:poly({ { z.w - 10, 5 }, { z.w - 3, 11 }, { z.w - 10, 17 } }, A1, 1.4)
      H.hit(1, 6, 0, 0, 16, 24, 'Previous'); H.hit(1, 7, z.w - 16, 0, 16, 24, 'Next')
    else H.hideHit(1, 6); H.hideHit(1, 7) end
  else
    for t = 1, MAXTABS do H.hideText(1, t); H.hideHit(1, t) end
    H.hideHit(1, 6); H.hideHit(1, 7)
  end
  -- icon + text
  local bodyH = z.h - top
  local isz = isCat and 56 or 66
  local ix = mirror and (z.w - 18 - isz / 2) or (18 + isz / 2)
  local iy = top + bodyH / 2
  local tx = mirror and (z.w - 36 - isz) or (36 + isz)
  local al = mirror and 'RightTop' or 'LeftTop'
  if app then
    local running = false
    if app.proc ~= '' then
      H.set('mProc', 'ProcessName', app.proc)
      running = H.val('mProc', -1) > 0
    end
    c:icon(app.icon, ix, iy, isz, app.missing and D or A1, 1.8)
    H.text(1, 8, tx, top + (isCat and 6 or 12), string.upper(app.name), { size = isCat and 11 or 12.5, font = H.fontTitle, weight = 700, color = T, align = al, clip = z.w - isz - 60 })
    local sub = isCat and (entry.cat.name .. string.format('   %d/%d', sel, #entry.cat.apps)) or app.info
    H.text(1, 9, tx, top + (isCat and 30 or 40), sub, { size = 9, color = D, align = al, clip = z.w - isz - 60 })
    local scol = app.missing and H.C.warn or (running and H.C.good or A1)
    local sy = top + (isCat and 56 or 70)
    local sx = mirror and tx - 6 or tx + 6
    c:dot(sx, sy, 4, scol)
    H.text(1, 10, mirror and tx - 16 or tx + 16, sy - 8, app.missing and 'NOT FOUND' or (running and 'RUNNING' or 'READY'),
      { size = 9, weight = 700, color = scol, align = al })
    H.hit(1, 8, 0, top, z.w, bodyH, 'Launch ' .. app.name .. (isCat and '  (scroll to switch)' or ''))
  else
    H.text(1, 8, tx, top + 20, entry and 'EMPTY CATEGORY' or 'UNASSIGNED', { size = 11, font = H.fontTitle, color = D, align = al })
    H.hideText(1, 9); H.hideText(1, 10); H.hideHit(1, 8)
  end
  c:flush()
  return 0
end

function OnClick(zi, k)
  if k <= 5 then choose(first + k - 1)
  elseif k == 6 then choose(sel - 1)
  elseif k == 7 then choose(sel + 1)
  elseif k == 8 then local app = current(); if app then A.launch(app) end end
  Update()
end
function OnRightClick(zi, k)
  if k <= 5 and entry and entry.kind == 'cat' and entry.cat.apps[first + k - 1] then A.launch(entry.cat.apps[first + k - 1]) end
end
function OnScroll(zi, k, d) choose(sel + d); Update() end
function OnHover(zi, k, on) end
