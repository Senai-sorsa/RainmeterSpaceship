-- The two tilted screens at the bottom of the dash (reference: the small angled list screens). The zones are
-- the upper part of each pane, sheared with it, so the text sits on the screen at the screen's angle.
-- Left: pilot (Windows user), date, time. Right: host, Windows, display.
local H

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function rows(zi, list)
  local z = H.zones[zi]
  local c = H.canvas(zi)
  local A1, W = H.C.accent, H.C.white
  local rh = z.h / (#list + 0.6)
  for i, r in ipairs(list) do
    local y = rh * (i - 0.2)
    c:hair(6, y + rh * 0.42, z.w - 6, y + rh * 0.42, A1, 1, 60)
    H.text(zi, i * 2 - 1, 7, y, r[1], { size = 3.4, weight = 700, align = 'LeftCenter', color = A1, alpha = 220, glow = false })
    H.text(zi, i * 2, z.w - 6, y, r[2], { size = 3.6, weight = 700, align = 'RightCenter', color = r[3] or W, font = H.fontNum, clip = z.w * 0.62 })
  end
  c:flush()
end

function Update()
  H.refreshTier()
  rows(1, {
    { 'PILOT', string.upper(H.sval('mUser', '--')) },
    { 'DATE', string.upper(os.date('%a %d %b')) },
    { 'TIME', os.date('%H:%M:%S'), H.C.hi },
  })
  rows(2, {
    { 'HOST', string.upper(H.sval('mHost', '--')) },
    { 'OS', string.upper(H.str('OsName', 'WINDOWS')) },
    { 'DISP', H.str('SCREENAREAWIDTH', '?') .. 'x' .. H.str('SCREENAREAHEIGHT', '?') },
  })
  H.hit(1, 1, 0, 0, H.zones[1].w, H.zones[1].h, 'Pilot, date and time - click: Calendar')
  H.hit(2, 1, 0, 0, H.zones[2].w, H.zones[2].h, 'Host, Windows and display - click: Display settings')
  return 0
end

function OnClick(z, k) SKIN:Bang(z == 1 and '["outlookcal:"]' or '["ms-settings:display"]') end
function OnRightClick(z, k) end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
