-- Target lock (reference: the reticle with [2] 567m), in bright red. Two modes:
--   TO-DO  (ReticleTodo=1 and your Obsidian note has open items): locks onto the next item due - [n] = open
--          items, readout = countdown, the task name under the rings, the next few items as blips that sit
--          closer to the centre the sooner they're due.
--          Note format:  - [ ] Statics HW 4 📅 2026-10-14 @17:00   (time optional = 23:59; Tasks plugin
--          dates and Dataview [due:: 2026-10-14] both work). Set the note in Control Center > DATA.
--   USAGE  (otherwise): the busiest processes, as before.
-- It roams the upper windscreen: it glides
-- in a straight line to a new spot (slow start, faster in the middle, slow finish), settles there for one
-- second with a lock pulse, then moves on. Every destination is checked so the whole reticle - rings, box
-- and readout - stays fully inside the windscreen glass. Outer arcs rotate one way, the inner ring the other.
-- 20 fps on the FULL tier, 10 fps on LITE, parked in place on LOW / STEALTH.
local H
local rank, frame = 1, 0
local lastName, lockAnim = '', 0
local name, cpu, ram = '', 0, 0
local SXR, SYR = 2560 / 1260, 1600 / 709
-- zone origin in reference px (ref_layout C_target) and the windscreen's slanted sides
local ZX, ZY = 412, 108
local WIN_TOP, WIN_LX0, WIN_RX0, SLOPE = 104, 342.3, 917.7, (500.8 - 342.3) / (365.5 - 104)
-- reticle extents from its centre, zone px (box + readout on the left)
local EXT_L, EXT_R, EXT_U, EXT_D = 126, 102, 102, 102
local pos, from, to = nil, nil, nil
local t0, dur, dwellUntil = 0, 1, 0
local rot = 0

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
  math.randomseed(os.time())
end

-- ---------------------------------------------------------------- Obsidian to-do note
local todos, todoAt, todoPath = {}, -100, ''
local CAL = '\240\159\147\133'                      -- 📅
local ALARM = '\226\143\176'                        -- ⏰

local function parseTodos(path)
  local list = {}
  local f = io.open(path, 'r')
  if not f then return list, false end
  local order = 0
  for line in f:lines() do
    local box, rest = string.match(line, '^%s*[%-%*%+]%s+%[(.)%]%s+(.*)$')
    if box == ' ' and rest then
      order = order + 1
      local y, mo, d = string.match(rest, CAL .. '%s*(%d%d%d%d)%-(%d%d)%-(%d%d)')
      if not y then y, mo, d = string.match(rest, 'due::%s*(%d%d%d%d)%-(%d%d)%-(%d%d)') end
      local hh, mm = string.match(rest, '@(%d%d?):(%d%d)')
      if not hh then hh, mm = string.match(rest, ALARM .. '%s*(%d%d?):(%d%d)') end
      if not hh then hh, mm = string.match(rest, 'due::%s*%d%d%d%d%-%d%d%-%d%d[T ](%d%d):(%d%d)') end
      local due
      if y then
        due = os.time({ year = tonumber(y), month = tonumber(mo), day = tonumber(d), hour = tonumber(hh) or 23, min = tonumber(mm) or 59, sec = 0 })
      end
      -- display text: drop dates, times, task-plugin emoji, Dataview fields and tags
      local t = rest
      t = string.gsub(t, '%[[%w_%-]+::[^%]]*%]', '')
      t = string.gsub(t, '[\240-\244][\128-\191][\128-\191][\128-\191]%s*[%d%-]*', '')
      t = string.gsub(t, '\226[\140-\143][\128-\191]%s*[%d%-:]*', '')
      t = string.gsub(t, '@%d%d?:%d%d', '')
      t = string.gsub(t, '#[%w_/%-]+', '')
      t = string.gsub(string.gsub(t, '%s+', ' '), '^%s*(.-)%s*$', '%1')
      if t ~= '' then list[#list + 1] = { text = t, due = due, timed = hh ~= nil, order = order } end
    end
  end
  f:close()
  table.sort(list, function(a, b)
    if a.due and b.due then return a.due < b.due end
    if a.due or b.due then return a.due ~= nil end
    return a.order < b.order
  end)
  return list, true
end

local function refreshTodos()
  if os.time() - todoAt < 5 then return end
  todoAt = os.time()
  todoPath = H.str('ObsidianTodo', '')
  if todoPath == '' or H.num('ReticleTodo', 1) ~= 1 then todos = {}; return end
  todos = parseTodos(todoPath)
end

local function countdown(sec)
  if sec < 0 then return 'LATE' end
  if sec < 3600 then return string.format('%dM', math.floor(sec / 60)) end
  if sec < 86400 then return string.format('%dH%02d', math.floor(sec / 3600), math.floor(sec % 3600 / 60)) end
  return string.format('%dD', math.floor(sec / 86400))
end

local function urlencode(str)
  return (string.gsub(str, '[^%w%-%._~]', function(ch) return string.format('%%%02X', string.byte(ch)) end))
end

local function sample()
  local threads = math.max(1, H.val('mThreads', 20))
  name = string.gsub(H.sval('mTop' .. rank, ''), '#%d+$', '')
  cpu = H.val('mTop' .. rank, 0) / threads
  H.set('mTargetRam', 'Name', name ~= '' and name or 'explorer')
  ram = H.val('mTargetRam', 0)
  if name ~= lastName then lastName, lockAnim = name, 18 end
end

-- is the reticle centred at zone px (x, y) fully on the windscreen glass?
local function inside(x, y)
  local z = H.zones[1]
  if x - EXT_L < 0 or x + EXT_R > z.w or y - EXT_U < 0 or y + EXT_D > z.h then return false end
  local yr = ZY + (y + EXT_D) / SYR                       -- lowest point: the glass is narrowest there
  if yr < WIN_TOP then return false end
  local left = WIN_LX0 + (yr - WIN_TOP) * SLOPE
  local right = WIN_RX0 - (yr - WIN_TOP) * SLOPE
  return ZX + (x - EXT_L) / SXR >= left + 2 and ZX + (x + EXT_R) / SXR <= right - 2
end

local function pickNext()
  local z = H.zones[1]
  for _ = 1, 40 do
    local x = EXT_L + math.random() * (z.w - EXT_L - EXT_R)
    local y = EXT_U + math.random() * (z.h - EXT_U - EXT_D)
    if inside(x, y) and (not pos or math.abs(x - pos[1]) + math.abs(y - pos[2]) > 140) then return { x, y } end
  end
  return { z.w / 2, z.h / 2 }
end

local function smoother(t) return t * t * t * (t * (t * 6 - 15) + 10) end   -- ease in, speed up, ease out

function Update()
  frame = frame + 1
  if frame % 20 == 1 then H.refreshTier(); sample(); refreshTodos() end
  local tier = H.tier
  local step = tier == 0 and 1 or (tier == 1 and 2 or 0)
  if step == 0 and frame % 20 ~= 1 then return 0 end
  if step == 2 and frame % 2 == 0 then return 0 end
  local z = H.zones[1]
  local now = frame * 0.05
  if not pos then pos = { z.w / 2, z.h / 2 }; dwellUntil = now + 1 end
  -- motion: dwell 1 s, then glide to the next spot
  if step > 0 then
    if to then
      local k = math.min(1, (now - t0) / dur)
      local e = smoother(k)
      pos = { from[1] + (to[1] - from[1]) * e, from[2] + (to[2] - from[2]) * e }
      if k >= 1 then pos, to, dwellUntil, lockAnim = to, nil, now + 1, 12 end
    elseif now >= dwellUntil then
      from, to = { pos[1], pos[2] }, pickNext()
      local dist = math.sqrt((to[1] - from[1]) ^ 2 + (to[2] - from[2]) ^ 2)
      t0, dur = now, math.max(1.4, math.min(3.2, dist / 220))
    end
    rot = (rot + 1.6 * step) % 360
  end
  local c = H.canvas(1)
  local cx, cy = pos[1], pos[2]
  local todo = todos[1]
  local nowt = os.time()
  local dt = todo and todo.due and (todo.due - nowt) or nil
  -- the reference's bright red, in both modes
  local RED, HOT = { 255, 70, 52 }, { 255, 150, 130 }
  local zoom = 1
  if lockAnim > 0 then zoom = 1 + lockAnim / 18 * 0.08; lockAnim = lockAnim - step end
  local R = 86 * zoom
  -- haze (pre-blurred sprite, wide and horizontal like the reference)
  H.sprite(1, 1, cx, cy, R * 2.4, R * 1.5, 'haze.png', RED, tier < 2 and 235 or 140)
  -- four outer arcs, gaps on the diagonals, rotating
  for q = 0, 3 do
    local a0 = rot + q * 90 - 33
    c:arc(cx, cy, R, a0, a0 + 66, RED, 2.6, 250)
  end
  -- thick segmented inner ring, counter-rotating, breathing with the target's CPU share
  local pulse = step > 0 and math.sin(now * 4) * 0.05 or 0
  local r2 = 36 * (1 + pulse)
  local thick = 5 + 3 * H.clamp(cpu / 50, 0, 1)
  for q = 0, 2 do
    local a0 = -rot * 1.4 + q * 120 + 5
    c:arc(cx, cy, r2, a0, a0 + 116, HOT, thick, 250)   -- small notches, like the reference
  end
  c:fillCircle(cx, cy, r2 - thick - 2, { 20, 60, 140 }, 150)
  c:dot(cx, cy, 3.5, H.C.accent)
  -- [n] box + memory readout to the left (reference offsets)
  local bx0, by0 = cx + (604 - 657) * SXR, cy + (192 - 203) * SYR
  local bw, bh = 11 * SXR, 11 * SYR
  local flash = lockAnim > 0 and (lockAnim % 4 < 2)
  c:rect(bx0, by0, bw, bh, RED, 1.8, flash and 120 or 255)
  if todo then
    H.text(1, 1, bx0 + bw / 2, by0 + bh / 2, tostring(#todos), { size = 8, weight = 700, align = 'CenterCenter', color = RED })
    H.text(1, 2, bx0 + bw / 2 - 2, cy + 7 * SYR, dt and countdown(dt) or 'NO DUE', { size = 7.5, weight = 700, align = 'CenterCenter', color = RED })
    local label = string.upper(todo.text)
    if string.len(label) > 26 then label = string.sub(label, 1, 25) .. '.' end
    if todo.due then label = label .. '  |  ' .. string.upper(os.date(todo.timed and '%a %H:%M' or '%a %d %b', todo.due)) end
    H.text(1, 3, cx, cy + R + 12, label, { size = 6.2, weight = 700, align = 'CenterCenter', color = RED, font = H.fontNum })
    -- upcoming items: blips on the ring, closer to the centre the sooner they're due (within a week)
    for i = 2, math.min(4, #todos) do
      local it = todos[i]
      if it.due then
        local d = H.clamp((it.due - nowt) / (7 * 86400), 0, 1)
        local rr = r2 + 8 + (R - r2 - 8) * d
        local a = math.rad(rot * 0.3 + (i - 2) * 120 - 90)
        local x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        local bc = HOT
        c:poly({ { x, y - 5 }, { x + 5, y }, { x, y + 5 }, { x - 5, y } }, bc, 1.4, 230, true)
      end
    end
  else
    H.text(1, 1, bx0 + bw / 2, by0 + bh / 2, tostring(rank), { size = 8, weight = 700, align = 'CenterCenter', color = RED })
    H.text(1, 2, bx0 + bw / 2 - 2, cy + 7 * SYR, ram > 0 and string.format('%.0fm', ram / 1048576) or '--', { size = 7.5, weight = 700, align = 'CenterCenter', color = RED })
    H.hideText(1, 3)
  end
  if frame % 20 == 1 then
    local tip
    if todo then
      tip = string.format('Next: %s%s   %d open   click: open the note', todo.text,
        todo.due and ('   due ' .. os.date(todo.timed and '%a %d %b %H:%M' or '%a %d %b', todo.due)) or '', #todos)
    else
      tip = string.format('Target %d: %s  %.0f%% CPU  %.0f MB   click: next target   right-click: Task Manager', rank, name, cpu, ram / 1048576)
    end
    H.hit(1, 1, cx - EXT_L, cy - EXT_U, EXT_L + EXT_R, EXT_U + EXT_D, tip)
  end
  c:flush()
  return cpu
end

function OnClick(z, k)
  if todos[1] and todoPath ~= '' then
    SKIN:Bang('["obsidian://open?path=' .. urlencode(todoPath) .. '"]')
  else rank = rank % 5 + 1; frame = 0; Update() end
end
function OnRightClick(z, k) SKIN:Bang('["taskmgr.exe"]') end
function OnScroll(z, k, d) rank = (rank - 1 + d) % 5 + 1; frame = 0; Update() end
function OnHover(z, k, on) end
