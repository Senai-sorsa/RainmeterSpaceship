-- Storage screen (B_storage, 260 x 168).
local H
local peak = 50 * 1048576

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

function Update()
  H.refreshTier()
  local z = H.zones[1]
  local c = H.canvas(1)
  local A1, D, T = H.C.accent, H.C.dim, H.C.text
  local tot, free = H.val('mD1Total', 0), H.val('mD1Free', 0)
  local used = tot > 0 and (tot - free) / tot or 0
  -- header
  c:fillPoly({ { 0, 0 }, { 110, 0 }, { 100, 18 }, { 0, 18 } }, H.C.panel, 160)
  H.text(1, 1, 6, 1, 'STORAGE', { size = 9.5, font = H.fontTitle, weight = 700, color = A1 })
  H.text(1, 2, z.w - 4, 2, H.str('Drive1', 'C:'), { size = 10, font = H.fontNum, align = 'RightTop', color = T })
  -- segmented fill ring (270 degree sweep)
  local cx, cy, r = 60, 92, 48
  local segs = 27
  for i = 0, segs - 1 do
    local a0 = 135 + i * 10
    local lit = (i + 1) / segs <= used + 0.001
    c:arc(cx, cy, r, a0 + 1, a0 + 8, lit and H.ramp((i + 1) / segs * 0.95) or D, lit and 5 or 3, lit and 255 or 90)
  end
  c:circle(cx, cy, r - 12, D, 1, 120)
  H.text(1, 3, cx, cy - 2, string.format('%d%%', used * 100), { size = 14, font = H.fontNum, align = 'CenterCenter', color = T })
  H.text(1, 4, cx, cy + 18, 'USED', { size = 8, weight = 700, align = 'CenterCenter', color = D })
  -- text column
  local x0 = 126
  H.text(1, 5, x0, 26, string.format('%.0f / %.0f GB', (tot - free) / 1073741824, tot / 1073741824), { size = 10, font = H.fontNum, color = T })
  -- read / write bars
  local rd, wr = H.val('mRead', 0), H.val('mWrite', 0)
  peak = math.max(peak * 0.98, rd, wr, 1048576)
  local bw = z.w - x0 - 4
  for i, v in ipairs({ { 'R', rd }, { 'W', wr } }) do
    local y = 52 + (i - 1) * 30
    H.text(1, 5 + i, x0, y, v[1] .. '  ' .. H.rate(v[2]), { size = 9, font = H.fontNum, color = D })
    c:fillRect(x0, y + 17, bw, 5, D, 60)
    c:fillRect(x0, y + 17, bw * H.clamp(v[2] / peak, 0, 1), 5, A1, 230)
  end
  local ssd = H.hw('mHwSsdTemp')
  H.text(1, 8, x0, 112, 'SSD ' .. (ssd and string.format('%.0f C', ssd) or '--'), { size = 9, font = H.fontNum, color = D })
  -- second drive
  local t2, f2 = H.val('mD2Total', 0), H.val('mD2Free', 0)
  if t2 > 0 then
    local u2 = (t2 - f2) / t2
    H.text(1, 9, 6, 146, H.str('Drive2', 'D:') .. string.format('  %d%%', u2 * 100), { size = 9, font = H.fontNum, color = D })
    c:segBar(70, 150, z.w - 74, 7, u2, 20, nil, 2)
  else
    H.text(1, 9, 6, 146, 'NO SECOND DRIVE', { size = 8.5, color = D })
  end
  H.text(1, 10, x0, 128, string.format('FREE %.0f GB', free / 1073741824), { size = 9, font = H.fontNum, color = A1 })
  H.hit(1, 1, cx - r, cy - r, 2 * r, 2 * r, 'Open ' .. H.str('Drive1', 'C:') .. '   (right-click: WinDirStat)')
  H.hit(1, 2, 0, 140, z.w, 26, 'Open ' .. H.str('Drive2', 'D:'))
  c:flush()
  return used
end

function OnClick(z, k)
  local d = k == 1 and H.str('Drive1', 'C:') or H.str('Drive2', 'D:')
  SKIN:Bang('["' .. d .. '\\"]')
end
function OnRightClick(z, k)
  local A = dofile(SKIN:GetVariable('@') .. 'Scripts\\apps.lua')
  A.load()
  if A.apps.windirstat then A.launch(A.apps.windirstat) end
end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
