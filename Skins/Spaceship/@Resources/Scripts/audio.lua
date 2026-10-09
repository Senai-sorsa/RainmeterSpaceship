-- Audio screen (B_audio, 260 x 168). Reference: the "TARGET SAR" waveform screen.
local H
local frame, disabled = 0, false

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function media(key)
  SKIN:Bang('!SetOption', 'mMedia', 'Parameter', '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' .. SKIN:GetVariable('@') .. 'Scripts\\media.ps1" -Key ' .. key)
  SKIN:Bang('!UpdateMeasure', 'mMedia')
  SKIN:Bang('!CommandMeasure', 'mMedia', 'Run')
end

function Update()
  frame = frame + 1
  if frame % 20 == 1 then H.refreshTier() end
  -- waveform cost control: 20 fps at FULL, 5 fps LITE, frozen at LOW/STEALTH
  local every = ({ [0] = 1, [1] = 4 })[H.tier] or 20
  if H.tier >= 2 and not disabled then SKIN:Bang('!DisableMeasureGroup', 'Audio'); disabled = true
  elseif H.tier < 2 and disabled then SKIN:Bang('!EnableMeasureGroup', 'Audio'); disabled = false end
  if frame > 1 and frame % every ~= 0 and every > 1 then return 0 end
  local c = H.canvas(1)
  local A1, W, D = H.C.accent, H.C.white, H.C.dim
  local SXR, SYR = 2560 / 1260, 1600 / 709
  local function X(rx) return (rx - 778) * SXR end
  local function Y(ry) return (ry - 568) * SYR end
  local vol = H.val('mVol', 0)
  local muted = vol < 0
  if muted then vol = 0 end
  -- title + dot row (reference: TARGET SNR and the red dots) -> AUDIO OUT + volume dots
  H.text(1, 1, X(786), Y(584), 'AUDIO OUT', { size = 4.8, weight = 700, align = 'LeftCenter', color = W })
  for i = 0, 4 do
    local on = (not muted) and vol >= (i + 1) * 20 - 10
    c:dot(X(846 + i * 5), Y(577), 2.4, on and H.C.hi or D, on and 255 or 120)
  end
  -- waveform line (reference: thin trace with a pink spike)
  local n = 24
  local pts = {}
  local peakI, peakV = 1, 0
  for i = 0, n - 1 do
    local v = disabled and 0 or H.clamp(H.val('mBand' .. i, 0), 0, 1)
    if v > peakV then peakI, peakV = i, v end
    local x = X(786) + (X(866) - X(786)) * i / (n - 1)
    pts[#pts + 1] = { x, Y(597) + ((i % 2 == 0) and -1 or 1) * v * 16 }
  end
  c:hairPoly({ { X(786), Y(597) }, { X(866), Y(597) } }, W, 90, 1)
  c:poly(pts, W, 1.2, 220)
  local px = X(786) + (X(866) - X(786)) * peakI / (n - 1)
  c:line(px, Y(597) - peakV * 20 - 3, px, Y(597) + peakV * 20 + 3, H.C.hi, 2)
  -- rows (reference: CROSS-SECTION / INFRARED / EM with values)
  local dev = string.upper(H.sval('mVol', 'NO DEVICE'))
  dev = string.gsub(dev, '%s*%b()', '')
  H.text(1, 2, X(786), Y(615), 'OUTPUT', { size = 4.4, weight = 700, align = 'LeftCenter', color = D })
  H.text(1, 3, X(840), Y(615), dev, { size = 4.4, weight = 700, align = 'RightCenter', color = D, clip = X(840) - X(806) })
  H.text(1, 4, X(786), Y(622), 'VOLUME', { size = 4.4, weight = 700, align = 'LeftCenter', color = W })
  H.text(1, 5, X(840), Y(622), muted and 'MUTE' or string.format('%d', vol), { size = 4.4, weight = 700, align = 'RightCenter', color = muted and H.C.hi or W })
  H.text(1, 6, X(786), Y(629), 'MEDIA', { size = 4.4, weight = 700, align = 'LeftCenter', color = D })
  local my = Y(629)
  c:poly({ { X(812), my - 4 }, { X(808), my }, { X(812), my + 4 } }, A1, 1.3, 255, true); c:line(X(807.5), my - 4, X(807.5), my + 4, A1, 1.3)
  c:poly({ { X(820), my - 4 }, { X(825), my }, { X(820), my + 4 } }, A1, 1.3, 255, true)
  c:poly({ { X(832), my - 4 }, { X(836), my }, { X(832), my + 4 } }, A1, 1.3, 255, true); c:line(X(837), my - 4, X(837), my + 4, A1, 1.3)
  -- small box (reference) -> mute toggle with a speaker glyph
  local bx0, by0, bx1, by1 = X(843), Y(616), X(866), Y(634)
  c:rect(bx0, by0, bx1 - bx0, by1 - by0, W, 1.2, 200)
  local sx, sy = (bx0 + bx1) / 2 - 6, (by0 + by1) / 2
  c:poly({ { sx - 6, sy - 4 }, { sx - 2, sy - 4 }, { sx + 4, sy - 9 }, { sx + 4, sy + 9 }, { sx - 2, sy + 4 }, { sx - 6, sy + 4 } }, muted and H.C.hi or W, 1.2, 255, true)
  if muted then c:line(sx + 9, sy - 6, sx + 19, sy + 6, H.C.hi, 1.6); c:line(sx + 19, sy - 6, sx + 9, sy + 6, H.C.hi, 1.6)
  else c:arc(sx + 6, sy, 8, -40, 40, W, 1.2); c:arc(sx + 6, sy, 13, -40, 40, W, 1.2, 160) end
  for k = 7, 12 do H.hideText(1, k) end
  if frame < 3 or frame % 20 == 0 then
    H.hit(1, 1, X(786), Y(611), X(842) - X(786), Y(619) - Y(611), 'Output: ' .. dev .. ' - click: next device')
    H.hit(1, 2, X(786), Y(619), X(842) - X(786), Y(625) - Y(619), 'Volume - scroll to change, click to mute')
    H.hit(1, 3, X(805), Y(625), X(814) - X(805), Y(633) - Y(625), 'Previous')
    H.hit(1, 4, X(816), Y(625), X(828) - X(816), Y(633) - Y(625), 'Play / pause')
    H.hit(1, 5, X(829), Y(625), X(840) - X(829), Y(633) - Y(625), 'Next')
    H.hit(1, 6, bx0, by0, bx1 - bx0, by1 - by0, 'Mute toggle   (scroll: volume)')
  end
  c:flush()
  return vol
end

function OnClick(z, k)
  if k == 1 then SKIN:Bang('!CommandMeasure', 'mVol', 'ToggleNext')
  elseif k == 2 or k == 6 then SKIN:Bang('!CommandMeasure', 'mVol', 'ToggleMute')
  elseif k == 3 then media('prev') elseif k == 4 then media('playpause') elseif k == 5 then media('next') end
end
function OnRightClick(z, k) SKIN:Bang('["ms-settings:sound"]') end
function OnScroll(z, k, d)
  if k == 2 or k == 6 then SKIN:Bang('!CommandMeasure', 'mVol', 'ChangeVolume ' .. (-5 * d)) end
end
function OnHover(z, k, on) end
