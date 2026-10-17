-- Jarvis log (Overlay\Jarvis, 1200 x 616): the conversation, newest at the bottom, Jarvis's reply streaming in
-- live. Reads Data\jarvis_log.txt (U|unix|text = you, J|unix|text = Jarvis) and Data\jarvis_live.txt (the reply
-- being written right now). Scroll to read back; closes with X, when Jarvis is asked to, or after 3 idle minutes.
local H
local scroll = 0             -- lines scrolled up from the bottom
local lines = {}             -- wrapped display lines { who, text, first }
local lastSig = ''
local idle = 0
local ROWS, RH, TOP = 20, 26, 66
local LX, TX, RM = 40, 150, 90       -- label column, text column, right margin (clear of the scroll bar)
local SIZE = 8.6

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function readAll(name)
  local f = io.open(H.res .. 'Data\\' .. name, 'r')
  if not f then return '' end
  local s = f:read('*a') or ''
  f:close()
  return s
end

-- monospace font: wrap by character count
local function wrap(text, width)
  local out, line = {}, ''
  for word in string.gmatch(text, '%S+') do
    while string.len(word) > width do
      if line ~= '' then out[#out + 1] = line; line = '' end
      out[#out + 1] = string.sub(word, 1, width); word = string.sub(word, width + 1)
    end
    if line == '' then line = word
    elseif string.len(line) + 1 + string.len(word) <= width then line = line .. ' ' .. word
    else out[#out + 1] = line; line = word end
  end
  if line ~= '' then out[#out + 1] = line end
  if #out == 0 then out[1] = '' end
  return out
end

local function build(z)
  local log, live = readAll('jarvis_log.txt'), readAll('jarvis_live.txt')
  local sig = string.len(log) .. ':' .. string.sub(log, -40) .. ':' .. live
  if sig == lastSig then return false end
  lastSig = sig
  local cw = SIZE * H.textSmall * 96 / 72 * 0.6           -- one character's width in zone units
  local width = math.max(20, math.floor((z.w - TX - RM) / cw))
  lines = {}
  local function add(who, text)
    for i, l in ipairs(wrap(text, width)) do lines[#lines + 1] = { who = who, text = l, first = i == 1 } end
    lines[#lines + 1] = { who = '', text = '', first = false }
  end
  for who, t, text in string.gmatch(log, '([UJS])|(%d+)|([^\n]*)') do add(who, text) end
  local lw, lt, ltext = string.match(live, '([UJ])|(%d+)|([^\n]*)')
  if ltext and ltext ~= '' then add('L', ltext .. ' _') end
  return true
end

function Update()
  H.refreshTier()
  local z = H.zones[1]
  if build(z) then idle = 0; scroll = 0 else idle = idle + 1 end
  if idle > 720 then SKIN:Bang('!DeactivateConfig'); return 0 end      -- 3 minutes with nothing new
  local c = H.canvas(1)
  local A1, D, T, W = H.C.accent, H.C.dim, H.C.text, H.C.white
  c:chamfer(0, 0, z.w, z.h, 18, A1, 1.6, 255, 230)
  c:fillRect(0, 0, z.w, z.h, { 2, 8, 14 }, 175, 0)
  H.text(1, 1, LX, 14, 'J.A.R.V.I.S', { size = 13, font = H.fontTitle, weight = 700, color = A1 })
  local muted = string.match(readAll('jarvis_env.txt'), 'MUTED 1') ~= nil
  H.text(1, 2, z.w - 64, 18, muted and 'SPEAKERS MUTED - TEXT ONLY' or 'CONVERSATION LOG', { size = 7.5, align = 'RightTop', color = muted and A1 or D })
  c:line(LX - 10, 50, z.w - 30, 50, D, 1, 200)
  c:line(z.w - 36, 16, z.w - 20, 32, A1, 1.6); c:line(z.w - 20, 16, z.w - 36, 32, A1, 1.6)
  -- the visible window of lines, newest at the bottom
  local n = #lines
  local maxScroll = math.max(0, n - ROWS)
  scroll = H.clamp(scroll, 0, maxScroll)
  local first = math.max(1, n - ROWS + 1 - scroll)
  local k = 3
  for r = 0, ROWS - 1 do
    local L = lines[first + r]
    local y = TOP + r * RH
    if L and L.text ~= '' then
      if L.first and L.who ~= '' then
        local tag = L.who == 'U' and 'YOU' or (L.who == 'S' and 'SYSTEM' or 'CLOVER')
        H.text(1, k, LX, y, tag, { size = 7.2, weight = 700, color = L.who == 'U' and D or (L.who == 'S' and H.C.warn or A1), glow = false }); k = k + 1
      end
      H.text(1, k, TX, y, L.text, { size = SIZE, color = L.who == 'U' and T or (L.who == 'S' and H.C.warn or W), font = H.fontNum, glow = false }); k = k + 1
    end
    if k > 42 then break end
  end
  if n == 0 then H.text(1, k, z.w / 2, z.h / 2, 'Nothing said yet - click the hologram and talk', { size = 8, align = 'CenterCenter', color = D }); k = k + 1 end
  if maxScroll > 0 then
    -- scroll bar on the right
    local barH = (z.h - TOP - 24) * ROWS / n
    local pos = (z.h - TOP - 24 - barH) * (1 - scroll / maxScroll)
    c:line(z.w - 30, TOP, z.w - 30, z.h - 24, D, 1, 120)
    c:line(z.w - 30, TOP + pos, z.w - 30, TOP + pos + barH, A1, 3, 230)
  end
  for i = k, 44 do H.hideText(1, i) end
  H.hit(1, 1, 0, 0, z.w, z.h, 'Scroll: read back   right-click: open the log file')
  H.hit(1, 2, z.w - 44, 8, 32, 32, 'Close')
  c:flush()
  return n
end

function OnClick(z, k) if k == 2 then SKIN:Bang('!DeactivateConfig') end end
function OnRightClick(z, k) SKIN:Bang('["notepad.exe" "' .. H.res .. 'Data\\jarvis_log.txt"]') end
function OnScroll(z, k, d) scroll = scroll - d * 3; idle = 0; Update() end
function OnHover(z, k, on) idle = 0 end
