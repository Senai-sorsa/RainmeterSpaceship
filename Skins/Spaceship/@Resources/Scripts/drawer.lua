-- CARGO drawer (O_drawer, 560 x 560): ALL INSTALLED APPS (every app in the Start menu) plus an accordion of
-- every category; opened from a side slot it shows just that folder's apps (slot.lua calls Focus(id)).
local H, A
local open = {}
local scroll = 0
local rows = {}
local idle = 0
local focus = nil
local ROWS, RH, TOP = 19, 26, 50

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  A = dofile(SKIN:GetVariable('@') .. 'Scripts\\apps.lua')
  H.init()
  A.load()
end

-- called by a side slot right after it opens the drawer
function Focus(id)
  focus = A.cats[id] and id or nil
  scroll, idle = 0, 0
  Update()
end

local function build()
  rows = {}
  if focus then
    for _, app in ipairs(A.cats[focus].apps) do rows[#rows + 1] = { kind = 'app', app = app } end
    rows[#rows + 1] = { kind = 'all' }
    return
  end
  rows[#rows + 1] = { kind = 'cat', cat = A.cats.all, jump = true }
  for _, id in ipairs(A.catOrder) do
    local cat = A.cats[id]
    rows[#rows + 1] = { kind = 'cat', cat = cat }
    if open[id] then
      for _, app in ipairs(cat.apps) do rows[#rows + 1] = { kind = 'app', app = app } end
    end
  end
  local maxScroll = math.max(0, #rows - ROWS)
  if scroll > maxScroll then scroll = maxScroll end
end

function Update()
  H.refreshTier()
  idle = idle + 1
  if idle > 20 then SKIN:Bang('!DeactivateConfig'); return 0 end
  build()
  local z = H.zones[1]
  local c = H.canvas(1)
  local A1, D, T = H.C.accent, H.C.dim, H.C.text
  -- panel
  c:chamfer(0, 0, z.w, z.h, 18, A1, 1.6, 255, 230)
  c:fillRect(0, 0, z.w, z.h, { 2, 8, 14 }, 170, 0)
  local title = focus and string.upper(A.cats[focus].name) or 'CARGO HOLD'
  H.text(1, 1, 20, 12, title, { size = #title > 14 and 9.5 or 13, font = H.fontTitle, weight = 700, color = A1, clip = z.w - 190 })
  H.text(1, 2, z.w - 50, 15, focus and (#A.cats[focus].apps .. ' APPS') or (#A.cats.all.apps .. ' APPS INSTALLED'), { size = 9, align = 'RightTop', color = D })
  c:line(20, 42, z.w - 20, 42, D, 1, 200)
  c:line(z.w - 34, 14, z.w - 18, 30, A1, 1.6); c:line(z.w - 18, 14, z.w - 34, 30, A1, 1.6)
  H.hit(1, 1, z.w - 40, 8, 30, 30, 'Close')
  for r = 1, ROWS do
    local row = rows[r + scroll]
    local y = TOP + (r - 1) * RH
    local ti = 2 + r * 2 - 1
    if row then
      if row.kind ~= 'app' then H.hideImage(1, r) end
      if row.kind == 'all' then
        c:hair(20, y + 2, z.w - 40, y + 2, D, 1, 80)
        H.text(1, ti, 54, y + 6, 'BACK TO ALL FOLDERS', { size = 9.5, weight = 700, color = A1 })
        H.hideText(1, ti + 1)
        H.hit(1, 1 + r, 20, y, z.w - 40, RH - 3, 'Show every category')
      elseif row.kind == 'cat' then
        local isOpen = open[row.cat.id]
        c:fillRect(20, y, z.w - 40, RH - 3, H.C.panel, 150)
        c:icon(row.cat.icon, 36, y + RH / 2 - 1, 18, A1, 1.2)
        c:poly(isOpen and { { z.w - 40, y + 8 }, { z.w - 34, y + 15 }, { z.w - 28, y + 8 } } or { { z.w - 37, y + 6 }, { z.w - 30, y + 12 }, { z.w - 37, y + 18 } }, A1, 1.4)
        H.text(1, ti, 54, y + 3, row.cat.name, { size = 10.5, font = H.fontText, weight = 700, color = T, clip = 330 })
        H.text(1, ti + 1, z.w - 50, y + 4, #row.cat.apps .. ' APPS', { size = 9, align = 'RightTop', color = D })
        H.hit(1, 1 + r, 20, y, z.w - 40, RH - 3, row.jump and 'Show every installed app' or (isOpen and 'Collapse' or 'Expand'))
      else
        local app = row.app
        if app.missing or not H.image(1, r, 68, y + RH / 2 - 1, 24, app.id) then
          H.hideImage(1, r)
          c:icon(app.icon, 68, y + RH / 2 - 1, 16, app.missing and D or A1, 1.1)
        end
        H.text(1, ti, 86, y + 4, app.name, { size = 10, color = app.missing and D or T, clip = 280 })
        H.text(1, ti + 1, z.w - 50, y + 5, app.missing and 'NOT FOUND' or app.short, { size = 8.5, align = 'RightTop', color = app.missing and H.C.warn or D })
        c:hair(60, y + RH - 2, z.w - 40, y + RH - 2, D, 1, 50)
        H.hit(1, 1 + r, 50, y, z.w - 90, RH - 2, 'Launch ' .. app.name)
      end
    else
      H.hideText(1, ti); H.hideText(1, ti + 1); H.hideHit(1, 1 + r); H.hideImage(1, r)
    end
  end
  if #rows > ROWS then
    local frac = scroll / (#rows - ROWS)
    c:line(z.w - 12, TOP, z.w - 12, TOP + ROWS * RH, D, 1, 120)
    c:fillRect(z.w - 15, TOP + frac * (ROWS * RH - 40), 6, 40, A1, 200)
  end
  c:flush()
  return 0
end

function OnClick(zi, k)
  idle = 0
  if k == 1 then SKIN:Bang('!DeactivateConfig'); return end
  local row = rows[k - 1 + scroll]
  if not row then return end
  if row.kind == 'all' then focus = nil; scroll = 0; Update()
  elseif row.kind == 'cat' and row.jump then focus = row.cat.id; scroll = 0; Update()
  elseif row.kind == 'cat' then open[row.cat.id] = not open[row.cat.id]; Update()
  else A.launch(row.app); SKIN:Bang('!DeactivateConfig') end
end
function OnRightClick(zi, k) end
function OnScroll(zi, k, d) idle = 0; scroll = math.max(0, scroll + d * 3); Update() end
function OnHover(zi, k, on) idle = 0 end
