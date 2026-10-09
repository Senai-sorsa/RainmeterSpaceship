-- Storage screen (reference: ENG / ATMOS / DMG rows + two vertical bars "TH FU").
local H
local peak = 50 * 1048576
local SXR, SYR = 2560 / 1260, 1600 / 709
local function X(rx) return (rx - 395) * SXR end
local function Y(ry) return (ry - 565) * SYR end

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function short(b)
  local s = H.bytes(b)
  return (string.gsub(s, ' ', ''))
end

function Update()
  H.refreshTier()
  local c = H.canvas(1)
  local A1, W, D = H.C.accent, H.C.white, H.C.dim
  local tot, free = H.val('mD1Total', 0), H.val('mD1Free', 0)
  local used = tot > 0 and (tot - free) / tot or 0
  local t2, f2 = H.val('mD2Total', 0), H.val('mD2Free', 0)
  local used2 = t2 > 0 and (t2 - f2) / t2 or 0
  local rd, wr = H.val('mRead', 0), H.val('mWrite', 0)
  peak = math.max(peak * 0.98, rd, wr, 1048576)
  local ssd = H.hw('mHwSsdTemp')
  local rows = {
    { 584, H.str('Drive1', 'C:'), string.format('%.0f/%.0fG', (tot - free) / 1073741824, tot / 1073741824), W },
    { 600, 'READ', short(rd), W },
    { 616, 'WRITE', short(wr), W },
    { 627, 'SSD', ssd and string.format('%.0fC', ssd) or '--', D },
  }
  for i, r in ipairs(rows) do
    local y = Y(r[1])
    c:line(X(402), y, X(405), y, r[4], 1.4)
    c:dot(X(407), y, 2.2, r[4])
    H.text(1, i * 2 - 1, X(410), y, r[2] .. '  ' .. r[3], { size = 4.4, weight = 700, align = 'LeftCenter', color = r[4], clip = X(455) - X(410) })
    H.hideText(1, i * 2)
  end
  -- two vertical bars (C, D) with values beside them
  local top, bot = Y(578), Y(620)
  for i, v in ipairs({ { 462, used, H.str('Drive1', 'C:') }, { 471, used2, t2 > 0 and H.str('Drive2', 'D:') or '--' } }) do
    local x = X(v[1])
    c:hair(x, top, x, bot, D, 3, 140)
    c:line(x, bot, x, bot - (bot - top) * v[2], A1, 3.4)
    H.text(1, 8 + i, x, Y(625), string.sub(v[3], 1, 1), { size = 4.6, weight = 700, align = 'CenterCenter', color = W })
  end
  H.text(1, 11, X(458), Y(596), string.format('%d', used * 100), { size = 4.6, weight = 700, align = 'RightCenter', color = W })
  H.text(1, 12, X(458), Y(604), t2 > 0 and string.format('%d', used2 * 100) or '', { size = 4.6, weight = 700, align = 'RightCenter', color = D })
  H.hit(1, 1, 0, 0, X(450), Y(638), 'Open ' .. H.str('Drive1', 'C:') .. '  (right-click: WinDirStat)')
  H.hit(1, 2, X(456), 0, X(488) - X(456), Y(638), 'Drive fill: ' .. H.str('Drive1', 'C:') .. ' ' .. math.floor(used * 100) .. '%' .. (t2 > 0 and ('   ' .. H.str('Drive2', 'D:') .. ' ' .. math.floor(used2 * 100) .. '%') or ''))
  c:flush()
  return used
end

function OnClick(z, k)
  SKIN:Bang('["' .. H.str('Drive1', 'C:') .. '\\"]')
end
function OnRightClick(z, k)
  local A = dofile(SKIN:GetVariable('@') .. 'Scripts\\apps.lua')
  A.load()
  if A.apps.windirstat then A.launch(A.apps.windirstat) end
end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
