-- App slot: one app or a category. Styles copy the reference blocks:
--   row      all eight slots (default): a button - icon, name, status / app count, OPEN or LAUNCH hint,
--            stepped underline; categories open a pop-up app list. Mirror=1 flips it for the right column
--   compact  left 3   : icon, bracket, small box, number
--   ship     4 / 8    : ship-style icon over an underline with number
--   card     right 5  : right-aligned title / subtitle / RN RV rows, icon at right
--   rcompact right 6-7: diamond + slashes, icon, bracket underline, number
local H, A
local slot, style, mirror = 1, 'row', false
local entry, sel, first = nil, 1, 1
local MAXTABS = 3

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  A = dofile(SKIN:GetVariable('@') .. 'Scripts\\apps.lua')
  H.init()
  A.load()
  slot = tonumber(SELF:GetOption('Slot', '1')) or 1
  style = SELF:GetOption('Style', 'row')
  mirror = SELF:GetOption('Mirror', '0') == '1'
  entry = A.entry(A.layout['Slot' .. slot] or '')
  if entry and entry.kind == 'cat' then sel = tonumber(A.getState('Sel_' .. entry.cat.id, '1')) or 1 end
end

local function apps() return (entry and entry.kind == 'cat') and entry.cat.apps or nil end

local function current()
  if not entry then return nil end
  if entry.kind == 'app' then return entry.app end
  local list = entry.cat.apps
  if #list == 0 then return nil end
  if sel > #list then sel = 1 end
  return list[sel]
end

local function choose(i)
  local list = apps()
  if not list or #list == 0 then return end
  sel = (i - 1) % #list + 1
  if sel < first then first = sel end
  if sel >= first + MAXTABS then first = sel - MAXTABS + 1 end
  A.setState('Sel_' .. entry.cat.id, sel)
end

local function running(app)
  if not app or app.proc == '' then return false end
  H.set('mProc', 'ProcessName', app.proc)
  return H.val('mProc', -1) > 0
end

local function status(app)
  if not app then return 'EMPTY', H.C.dim end
  if app.missing then return 'NOT FOUND', H.C.warn end
  if running(app) then return 'RUNNING', H.C.good end
  return 'READY', H.C.white
end

local function hideAll(from, to) for k = from, to do H.hideText(1, k) end end

function Update()
  H.refreshTier()
  local z = H.zones[1]
  local c = H.canvas(1)
  local A1, W, D = H.C.accent, H.C.white, H.C.dim
  local w, h = z.w, z.h
  local function X(f) return f * w end
  local function Y(f) return f * h end
  local app = current()
  local list = apps()
  local st, scol = status(app)
  local isCat = list ~= nil
  local icol = (app and not app.missing) and A1 or D
  for k = 1, 7 do H.hideHit(1, k) end

  if style == 'row' then
    -- every slot is one button (no numbering): a single app launches, a category opens its pop-up app list.
    -- Same layout for all eight; Mirror=1 flips it for the right column. Icons are the apps' own icons in
    -- neon (theme colour -> white, with glow) when Scripts\app-icons.ps1 has extracted them, else line icons.
    local function MX(f) return mirror and (1 - f) * w or f * w end
    local LA, RA = mirror and 'RightCenter' or 'LeftCenter', mirror and 'LeftCenter' or 'RightCenter'
    local iconApp = isCat and app or app
    if not (iconApp and H.image(1, 1, MX(0.14), Y(0.46), h * 0.66, iconApp.id)) then
      H.hideImage(1, 1)
      if isCat then c:icon(entry.cat.icon, MX(0.14), Y(0.46), h * 0.6, A1, 1.7)
      elseif app then c:icon(app.icon, MX(0.14), Y(0.46), h * 0.6, icol, 1.7) end
    end
    local title = isCat and entry.cat.name or (app and app.name or 'UNASSIGNED')
    H.text(1, 8, MX(0.30), Y(0.24), title, { size = 8, weight = 700, align = LA, color = W, clip = X(0.62) })
    local sub
    if isCat then
      sub = #list .. ' APPS' .. (app and ('   LAST  ' .. app.short) or '')
      H.text(1, 9, MX(0.30), Y(0.50), sub, { size = 5.6, weight = 700, align = LA, color = { 160, 178, 190 }, clip = X(0.62) })
    else
      H.text(1, 9, MX(0.30), Y(0.50), st, { size = 5.6, weight = 700, align = LA, color = scol, clip = X(0.62) })
      c:dot(MX(0.30) + (mirror and 6 or -6), Y(0.50), 2.6, scol)
    end
    -- action hint on the outer end of the underline: OPEN (category) / LAUNCH (app), with a chevron
    local hx = MX(0.95)
    H.text(1, 10, hx + (mirror and 18 or -18), Y(0.72), isCat and 'OPEN' or 'LAUNCH', { size = 5, weight = 700, align = RA, color = A1, alpha = 220 })
    local cd = mirror and -1 or 1
    c:poly({ { hx - 6 * cd, Y(0.72) - 6 }, { hx, Y(0.72) }, { hx - 6 * cd, Y(0.72) + 6 } }, A1, 1.5)
    if isCat then c:poly({ { hx - 12 * cd, Y(0.72) - 6 }, { hx - 6 * cd, Y(0.72) }, { hx - 12 * cd, Y(0.72) + 6 } }, A1, 1.2, 160) end
    hideAll(1, 7); H.hideText(1, 11); H.hideText(1, 12)
    -- stepped underline (reference weapon rows)
    c:poly({ { MX(0.005), Y(0.98) }, { MX(0.327), Y(0.935) }, { MX(0.362), Y(0.84) }, { MX(0.96), Y(0.83) } }, A1, 1.4)
    for k = 1, 7 do H.hideHit(1, k) end
    H.hit(1, 8, 0, 0, w, h, isCat and (entry.cat.name .. ' - click: choose an app   right-click: launch ' .. (app and app.name or '') .. '   scroll: change it')
      or (app and ('Launch ' .. app.name) or 'Unassigned slot'))

  elseif style == 'card' then
    if app then c:icon(app.icon, X(0.81), Y(0.44), h * 0.62, icol, 1.7) end
    H.text(1, 8, X(0.585), Y(0.19), app and string.upper(app.name) or 'UNASSIGNED', { size = 8, weight = 700, align = 'RightCenter', color = W, clip = X(0.56) })
    H.text(1, 9, X(0.585), Y(0.33), isCat and entry.cat.name or (app and app.info or ''), { size = 6.5, weight = 700, align = 'RightCenter', color = W, alpha = 210, clip = X(0.56) })
    H.text(1, 10, X(0.385), Y(0.52), 'ST', { size = 6.5, weight = 700, align = 'RightCenter', color = W })
    H.text(1, 11, X(0.585), Y(0.52), st, { size = 6.5, weight = 700, align = 'RightCenter', color = scol })
    -- glyphs: dot, double chevron, diamond
    c:dot(X(0.045), Y(0.64), 3, A1)
    c:poly({ { X(0.085), Y(0.59) }, { X(0.07), Y(0.64) }, { X(0.085), Y(0.69) } }, A1, 1.4)
    c:poly({ { X(0.105), Y(0.59) }, { X(0.09), Y(0.64) }, { X(0.105), Y(0.69) } }, A1, 1.4)
    c:poly({ { X(0.18), Y(0.56) }, { X(0.20), Y(0.64) }, { X(0.18), Y(0.72) }, { X(0.16), Y(0.64) } }, W, 1.4, 255, true)
    if isCat then
      local vis = math.min(4, #list)
      local step = X(0.36) / 4
      for t = 1, 4 do
        local i = first + t - 1
        if t <= vis and list[i] then
          local x = X(0.23) + (t - 1) * step
          local on = i == sel
          H.text(1, t, x, Y(0.68), list[i].short, { size = 6, weight = 700, align = 'LeftCenter', color = on and A1 or { 160, 178, 190 }, clip = step - 3 })
          H.hit(1, t, x, Y(0.58), step, Y(0.2), list[i].name)
        else H.hideText(1, t) end
      end
      H.hideText(1, 5)
    else hideAll(1, 5) end
    c:line(X(0.04), Y(0.82), X(0.085), Y(0.82), W, 2.2)
    c:poly({ { X(0.61), Y(0.83) }, { X(0.65), Y(0.94) }, { X(0.96), Y(0.94) } }, A1, 1.4)
    H.text(1, 12, X(0.965), Y(0.84), tostring(slot - 4), { size = 7.5, weight = 700, align = 'CenterCenter', color = W })
    H.hit(1, 8, X(0.60), 0, X(0.40), Y(0.80), app and ('Launch ' .. app.name) or 'Unassigned slot')

  else
    -- compact / rcompact / ship: icon blocks with a selector for categories
    local ix, iy, isz, nx, ny, ul
    if style == 'compact' then
      ix, iy, isz = X(0.24), Y(0.40), h * 0.62
      c:poly({ { X(0.71), Y(0.02) }, { X(0.64), Y(0.14) }, { X(0.64), Y(0.66) } }, A1, 1.4)
      c:rect(X(0.72), Y(0.36), X(0.12), Y(0.19), W, 1.3)
      if app then c:icon(app.icon, X(0.78), Y(0.455), Y(0.15), W, 1) end
      nx, ny = X(0.05), Y(0.86)
      ul = { { X(0.05), Y(0.98) }, { X(0.59), Y(0.92) }, { X(0.64), Y(0.74) } }
    elseif style == 'rcompact' then
      ix, iy, isz = X(0.63), Y(0.33), h * 0.62
      c:poly({ { X(0.08), Y(0.07) }, { X(0.11), Y(0.17) }, { X(0.08), Y(0.27) }, { X(0.05), Y(0.17) } }, W, 1.4, 255, true)
      c:line(X(0.15), Y(0.12), X(0.19), Y(0.0), W, 1.2); c:line(X(0.19), Y(0.12), X(0.23), Y(0.0), W, 1.2)
      nx, ny = X(0.88), Y(0.78)
      ul = { { X(0.25), Y(0.45) }, { X(0.25), Y(0.90) }, { X(0.89), Y(0.93) } }
    else -- ship
      ix, iy, isz = X(0.45), Y(0.33), h * 0.62
      nx, ny = slot > 4 and X(0.78) or X(0.12), Y(0.86)
      ul = slot > 4 and { { X(0.0), Y(0.86) }, { X(0.70), Y(0.86) } } or { { X(0.18), Y(0.94) }, { X(0.98), Y(0.85) } }
    end
    if app then c:icon(app.icon, ix, iy, isz, icol, 1.6) end
    c:poly(ul, A1, 1.4)
    H.text(1, 12, nx, ny, tostring(slot > 4 and slot - 4 or slot), { size = 7.5, weight = 700, align = 'CenterCenter', color = W })
    local label = app and app.short or 'EMPTY'
    if isCat and #list > 1 then label = label .. ' ' .. sel .. '/' .. #list end
    local lx = style == 'compact' and X(0.70) or (style == 'rcompact' and X(0.27) or ix)
    local ly = style == 'compact' and Y(0.74) or (style == 'rcompact' and Y(0.72) or Y(0.70))
    H.text(1, 8, lx, ly, label, { size = 6, weight = 700, align = style == 'ship' and 'CenterCenter' or 'LeftCenter', color = scol, clip = X(0.62) })
    hideAll(1, 5); H.hideText(1, 9); H.hideText(1, 10); H.hideText(1, 11)
    if isCat and #list > 1 then
      H.hit(1, 6, 0, 0, X(0.15), h, 'Previous app'); H.hit(1, 7, X(0.85), 0, X(0.15), Y(0.6), 'Next app')
    end
    H.hit(1, 8, ix - isz / 2, iy - isz / 2, isz, isz, app and ('Launch ' .. app.name .. (isCat and '  (scroll to switch)' or '')) or 'Unassigned slot')
  end
  c:flush()
  return 0
end

local function openPopup()
  -- the CARGO drawer opens focused on this category (it reads and clears DrawerFocus)
  A.setState('DrawerFocus', entry.cat.id)
  SKIN:Bang('!ActivateConfig', 'Spaceship\\Overlay\\Drawer', 'Drawer.ini')
  SKIN:Bang('!Refresh', 'Spaceship\\Overlay\\Drawer')
end

function OnClick(zi, k)
  if style == 'row' and k == 8 then
    if apps() then openPopup() else local app = current(); if app then A.launch(app) end end
    return
  end
  if k <= 5 then choose(first + k - 1)
  elseif k == 6 then choose(sel - 1)
  elseif k == 7 then choose(sel + 1)
  elseif k == 8 then local app = current(); if app then A.launch(app) end end
  Update()
end
function OnRightClick(zi, k)
  local list = apps()
  if style == 'row' and k == 8 then local app = current(); if app then A.launch(app) end; return end
  if k <= 5 and list and list[first + k - 1] then A.launch(list[first + k - 1]) end
end
function OnScroll(zi, k, d) choose(sel + d); Update() end
function OnHover(zi, k, on) end
