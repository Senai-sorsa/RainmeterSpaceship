-- Jarvis core (the centre screen, where the globe used to be).
-- Layers, back to front:
--   plasma orb      your animation (Images\Jarvis\Idle, 210 frames, seamless loop), tinted per state
--   voice echo      the same orb half a loop ahead, swelling outward while Jarvis speaks (or Images\Jarvis\Active)
--   3D plexus       a rotating network of nodes and links on a sphere around the orb - links behind the orb are
--                   hidden by it, the front ones glow, so it reads as a real 3D shell
--   orbit rings     two tilted rings in 3D with satellites, crossing in front of and behind the orb
--   HUD dial        segmented / tick rings and side data bars that move with his voice (and your mic)
-- Driven by the Jarvis service (@Resources\Jarvis\jarvis.py) through Data\jarvis.txt (T | STATE | LEVEL | SAY |
-- ERR | POP) and Data\jarvis_cmd.txt (WAKE / CANCEL, written on click).
-- States: STANDBY cyan, LISTENING deeper blue, THINKING fast spin + sweep, SPEAKING the echo and the shell swell
-- with his voice, OFFLINE (service not running) dim.
-- Cost: orb frames 30 fps / 3D layers 15 fps on FULL, half on LITE, quarter on LOW, hidden on STEALTH.
local H
local frame = 0
local CX, CY = (746 - 514) / 2 * (2560 / 1260), (491 - 407) * (1600 / 709)   -- same centre as the old globe
local ORB_D = 330             -- orb frame size (zone units); its own bright ring sits at ~0.45 x this
local OCC = ORB_D * 0.40      -- anything behind the orb and inside this radius is hidden by it
local RP = 168                -- plexus shell radius
local seq = { idle = nil, active = nil }   -- { dir, pattern, n, first }
local fIdle, fAct = 0, 0
local rot1, rot2, rot3, yaw, sweep = 0, 0, 0, 0, 0
local js = { state = 'offline', level = 0, t = 0, say = '', err = '', pop = nil }
local hudSeen = nil                          -- last HUD setting request handled (HUD <n> <name>); only names in HUD_OK are obeyed
local HUD_OK = { stealth = function() SKIN:Bang('!CommandMeasure', 'mScript', 'SetOverride(3)', 'Spaceship\\Controller') end,
                 mic = function(v) H.save('JarvisMic', (v:gsub('%c', ''))) end }
local popSeen = nil                         -- last pop-up request handled (POP <n> open|close)
local mutedSent = nil
local lvl, act = 0, 0                        -- smoothed voice / mic level, echo opacity
local bars = {}                              -- side data bars (smoothed heights)
local lastCmd = 0
local note = nil                             -- short caption override: { text, until }
local startedAt = nil                        -- when we last launched the service (to spot a failed start)
local autoTried = false                      -- JarvisAutoStart is tried once per HUD load

-- Control Center > JARVIS settings (read live)
local function colorSetting(key, default)
  local v = H.str(key, '')
  local r, g, b = string.match(v, '(%d+)%s*,%s*(%d+)%s*,%s*(%d+)')
  if r then return { tonumber(r), tonumber(g), tonumber(b) } end
  return default
end
local function on(key) return H.num(key, 1) == 1 end
local sin, cos, sqrt, rad, floor = math.sin, math.cos, math.sqrt, math.rad, math.floor

local function exists(p) local f = io.open(p, 'rb'); if f then f:close(); return true end; return false end

-- find the frame files in a folder: 001.png, frame-001.png, ezgif-frame-001.png, frame_001.png, frame001.png (0- or 1-based)
local PATTERNS = { '%03d.png', 'frame-%03d.png', 'ezgif-frame-%03d.png', 'frame_%03d.png', 'frame%03d.png', '%04d.png', 'frame_%04d.png', 'frame-%04d.png' }
local function scan(dir)
  for _, pat in ipairs(PATTERNS) do
    for _, first in ipairs({ 1, 0 }) do
      if exists(dir .. string.format(pat, first)) then
        local n = 0
        while n < 600 and exists(dir .. string.format(pat, first + n)) do n = n + 1 end
        return { dir = dir, pat = pat, n = n, first = first }
      end
    end
  end
  return nil
end

local function frameFile(s, f) return s.dir .. string.format(s.pat, s.first + (floor(f) % s.n)) end

-- plexus: points spread evenly on a sphere (slightly jittered so it looks organic), each linked to its nearest
local NODES, EDGES = {}, {}
local function buildPlexus()
  local n = 56
  local seed = 7
  local function rnd() seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648 end
  for i = 0, n - 1 do
    local y = 1 - 2 * (i + 0.5) / n
    local r = sqrt(1 - y * y)
    local th = math.pi * (3 - sqrt(5)) * i
    local j = 0.9 + 0.2 * rnd()
    NODES[#NODES + 1] = { cos(th) * r * j, y * j, sin(th) * r * j }
  end
  local seen = {}
  for i, a in ipairs(NODES) do
    local d = {}
    for k, b in ipairs(NODES) do
      if k ~= i then d[#d + 1] = { k, (a[1] - b[1]) ^ 2 + (a[2] - b[2]) ^ 2 + (a[3] - b[3]) ^ 2 } end
    end
    table.sort(d, function(p, q) return p[2] < q[2] end)
    for m = 1, 3 do
      local k = d[m][1]
      local key = math.min(i, k) .. ':' .. math.max(i, k)
      if not seen[key] then seen[key] = true; EDGES[#EDGES + 1] = { i, k } end
    end
  end
end

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
  seq.idle = scan(H.res .. 'Images\\Jarvis\\Idle\\')
  seq.active = scan(H.res .. 'Images\\Jarvis\\Active\\')
  buildPlexus()
end

local function readState()
  local f = io.open(H.res .. 'Data\\jarvis.txt', 'r')
  if not f then js.state = 'offline'; return end
  local s = { state = 'idle', level = 0, t = 0, say = '', err = '', pop = nil }
  for line in f:lines() do
    local k, v = string.match(line, '^(%u+) ?(.*)$')
    if k == 'T' then s.t = tonumber(v) or 0
    elseif k == 'STATE' then s.state = v
    elseif k == 'LEVEL' then s.level = tonumber(v) or 0
    elseif k == 'SAY' then s.say = v
    elseif k == 'ERR' then s.err = v
    elseif k == 'POP' then s.pop = v
    elseif k == 'HUD' then s.hud = v end
  end
  f:close()
  if os.time() - s.t > 8 then s.state = 'offline'; s.level = 0 end
  js = s
end

-- colour matrix. Frames with transparency (default): lightly tinted toward the state colour. Frames on a black
-- background (JarvisBlackBackground=1): black keyed out (alpha = brightness).
local function matrix(m, col, k, tint)
  local tr, tg, tb = col[1] / 255 * tint, col[2] / 255 * tint, col[3] / 255 * tint
  local key = H.num('JarvisBlackBackground', 0) == 1
  local a = key and 0.6 or 0
  H.set(m, 'ColorMatrix1', string.format('%.2f;0;0;%.1f;0', k, a))
  H.set(m, 'ColorMatrix2', string.format('0;%.2f;0;%.1f;0', k, a))
  H.set(m, 'ColorMatrix3', string.format('0;0;%.2f;%.1f;0', k, a))
  H.set(m, 'ColorMatrix4', key and '0;0;0;0;0' or '0;0;0;1;0')
  H.set(m, 'ColorMatrix5', string.format('%.3f;%.3f;%.3f;0;1', tr, tg, tb))
end

local function sprite(m, s, f, d, col, alpha, k, tint)
  local z = H.zones[1]
  H.set(m, 'ImageName', frameFile(s, f))
  H.set(m, 'ImageTint', '')
  matrix(m, col, k, tint)
  H.set(m, 'ImageAlpha', tostring(floor(H.clamp(alpha, 0, 255) * (H.hudA or 255) / 255)))
  H.set(m, 'X', string.format('%.2f', (z.x + CX - d / 2) * H.S))
  H.set(m, 'Y', string.format('%.2f', (z.y + CY - d / 2) * H.S))
  H.set(m, 'W', string.format('%.2f', d * H.S)); H.set(m, 'H', string.format('%.2f', d * H.S))
  H.set(m, 'Hidden', alpha < 3 and '1' or '0')
end

-- 3D -> screen: rotate (yaw about Y, then tilt about X), light perspective. Returns x, y, depth (-1 back .. 1 front)
local function proj(p, r, yw, tilt)
  local x, y, z = p[1], p[2], p[3]
  local cy, sy = cos(yw), sin(yw)
  x, z = x * cy + z * sy, -x * sy + z * cy
  local ct, st = cos(tilt), sin(tilt)
  y, z = y * ct - z * st, y * st + z * ct
  local f = 1 / (1 - z * 0.18)
  return CX + x * r * f, CY - y * r * f, z
end

local function hidden(x, y, z) return z < 0 and ((x - CX) ^ 2 + (y - CY) ^ 2) < OCC * OCC end

local LABEL = { idle = 'STANDBY', listening = 'LISTENING', thinking = 'THINKING', speaking = 'SPEAKING', offline = 'OFFLINE' }

local function drawScene(c, st, col, W, D)
  local dim = st == 'offline'
  local showShell, showOrbits, showDial, showBars = on('JarvisShell'), on('JarvisOrbits'), on('JarvisDial'), on('JarvisBars')
  local rc = dim and D or col
  local hot = H.mix(rc, W, 0.45)
  -- 3D plexus shell
  if showShell then
  local r = RP * (1 + 0.07 * lvl)
  local tilt = 0.38 + 0.08 * sin(frame * 0.006)
  local P = {}
  for i, n in ipairs(NODES) do
    local x, y, z = proj(n, r, yaw, tilt)
    P[i] = { x, y, z, hidden(x, y, z) }
  end
  local ea = dim and 0.6 or (1 + 0.8 * lvl)
  for _, e in ipairs(EDGES) do
    local a, b = P[e[1]], P[e[2]]
    if not a[4] and not b[4] then
      local z = (a[3] + b[3]) / 2
      local alpha = z >= 0 and (70 + 110 * z) or (22 + 30 * (1 + z))
      -- links crossing the orb's face stay faint so the plasma shows through
      local mx, my = (a[1] + b[1]) / 2 - CX, (a[2] + b[2]) / 2 - CY
      if mx * mx + my * my < OCC * OCC * 0.8 then alpha = alpha * 0.4 end
      c:hair(a[1], a[2], b[1], b[2], z >= 0 and hot or rc, z >= 0 and 1.1 or 0.8, floor(H.clamp(alpha * ea, 0, 235)))
    end
  end
  for _, p in ipairs(P) do
    if not p[4] and p[3] > -0.35 then
      c:dot(p[1], p[2], p[3] > 0.3 and (1.5 + 1.2 * lvl) or 1, p[3] > 0.3 and W or hot, floor(H.clamp((120 + 120 * p[3]) * ea, 30, 255)))
    end
  end
  end
  -- two tilted orbit rings in 3D with satellites; the part behind the orb is hidden, the front part glows
  if showOrbits then
  local rings = { { 200, rad(13), rot1 * 0.9, rad(16) }, { 184, rad(24), -rot2 * 0.7, rad(-24) } }
  for ri, R in ipairs(rings) do
    local rr, inc, ph, roll = R[1] * (1 + 0.04 * lvl), R[2], rad(R[3]), R[4]
    local runs, cur, curFront = {}, nil, nil
    for s = 0, 64 do
      local a = s / 64 * 2 * math.pi
      local p = { cos(a), 0, sin(a) }
      -- tilt the ring plane, then roll it, then spin it about the view axis
      local x, y, z = p[1], p[3] * sin(inc), p[3] * cos(inc)
      x, y = x * cos(roll) - y * sin(roll), x * sin(roll) + y * cos(roll)
      local sx, sy, sz = proj({ x, y, z }, rr, 0, 0)
      local front = sz >= 0
      if hidden(sx, sy, sz) then front = nil end
      if front ~= curFront or not cur then
        if cur and #cur > 1 then runs[#runs + 1] = { cur, curFront } end
        cur = cur and { cur[#cur] } or {}
        curFront = front
      end
      cur[#cur + 1] = { sx, sy }
    end
    if cur and #cur > 1 then runs[#runs + 1] = { cur, curFront } end
    for _, run in ipairs(runs) do
      if run[2] == true then c:poly(run[1], hot, 1.4, dim and 130 or 210)
      elseif run[2] == false then c:hairPoly(run[1], rc, dim and 45 or 70, 1) end
    end
    -- satellites riding the ring
    for k = 0, 1 do
      local a = ph + k * math.pi
      local x, y, z = cos(a), sin(a) * sin(inc), sin(a) * cos(inc)
      x, y = x * cos(roll) - y * sin(roll), x * sin(roll) + y * cos(roll)
      local sx, sy, sz = proj({ x, y, z }, rr, 0, 0)
      if not hidden(sx, sy, sz) then c:dot(sx, sy, sz >= 0 and 3 or 1.8, sz >= 0 and W or rc, sz >= 0 and 255 or 110) end
    end
  end
  end
  -- HUD dial: outer hairline, segmented arcs, tick ring
  if showDial then
  c:circle(CX, CY, 203, rc, 1, dim and 70 or 90)
  for q = 0, 2 do c:arc(CX, CY, 196, q * 120 + rot1, q * 120 + rot1 + 52, rc, 3.6 + 1.5 * lvl, dim and 160 or 230) end
  for q = 0, 5 do c:arc(CX, CY, 196, q * 60 + rot1 + 70, q * 60 + rot1 + 74, hot, 3.6, dim and 130 or 200) end
  local seg = 189 * 2 * math.pi / 120
  c:dashArc(CX, CY, 189, rot3, rot3 + 360, rc, 4, dim and 75 or 110, seg * 0.12, seg * 0.88, true)
  end
  if st == 'thinking' then c:arc(CX, CY, 196, sweep, sweep + 80, W, 3, 250) end
  -- side data bars (left and right), heights from his voice / your mic with a little life of their own
  if not showBars then return end
  local nb = 11
  for side = 0, 1 do
    for i = 1, nb do
      local key = side * nb + i
      local a = (side == 0 and 180 or 0) + (i - (nb + 1) / 2) * 5.2
      local wob = 0.5 + 0.5 * sin(frame * 0.11 + key * 1.7)
      local want = 3 + (dim and 0 or (4 * wob + 22 * lvl * (0.5 + 0.5 * sin(frame * 0.35 + key * 2.3))))
      bars[key] = (bars[key] or 3) + (want - (bars[key] or 3)) * 0.35
      local ar = rad(a)
      local r0 = 212
      c:hair(CX + r0 * cos(ar), CY + r0 * sin(ar), CX + (r0 + bars[key]) * cos(ar), CY + (r0 + bars[key]) * sin(ar),
        i == (nb + 1) / 2 and W or rc, 2.6, dim and 110 or 200)
    end
  end
end

local function pollState()
  readState()
  -- Jarvis asked for the log pop-up (muted speakers, STEALTH, or "show me what you've said")
  if js.pop and js.pop ~= popSeen then
    if popSeen ~= nil then
      local act = string.match(js.pop, '%S+$')
      if act == 'open' then SKIN:Bang('!ActivateConfig', 'Spaceship\\Overlay\\Jarvis', 'Jarvis.ini')
      elseif act == 'close' then SKIN:Bang('!DeactivateConfig', 'Spaceship\\Overlay\\Jarvis') end
    end
    popSeen = js.pop
  end
  -- Jarvis asked for a HUD setting by voice (7-A6): the first value read after a (re)load is only remembered, never obeyed
  if js.hud and js.hud ~= hudSeen then
    if hudSeen ~= nil then
      local name, val = string.match(js.hud, '^%d+ (%S+) ?(.*)$')
      local run = HUD_OK[name or '']
      if run then run(val or '') end
    end
    hudSeen = js.hud
  end
end

function Update()
  frame = frame + 1
  if frame % 20 == 1 then H.refreshTier() end
  if H.tier >= 3 then
    if frame % 40 == 1 then local c = H.canvas(1); for k = 1, 8 do H.hideText(1, k) end; H.hideSprite(1, 1); H.hideSprite(1, 2); c:flush() end
    if frame % 30 == 1 then pollState() end      -- STEALTH: replies and reminders come as the pop-up only, so keep reading
    return 0
  end
  local every = ({ [0] = 1, [1] = 2, [2] = 4 })[H.tier] or 4
  if frame % 3 == 1 then pollState() end
  -- tell Jarvis whether the speakers are muted (or at 0 %): then he answers in the pop-up instead
  if frame % 30 == 2 then
    local v = H.val('mVol', 50)
    local m = (v <= 0) and 1 or 0
    if m ~= mutedSent then
      local f = io.open(H.res .. 'Data\\jarvis_env.txt', 'w')
      if f then f:write('MUTED ', m, '\n'); f:close(); mutedSent = m end
    end
  end
  -- JarvisAutoStart=1: start the service ~5 s after the HUD loads if it isn't already running
  -- once, from ~5 s in (or when the HUD first leaves STEALTH)
  if frame >= 150 and not autoTried then
    autoTried = true
    if H.num('JarvisAutoStart', 1) == 1 and H.num('JarvisEnabled', 1) == 1 and js.state == 'offline' then StartService() end
  end
  if frame > 1 and frame % every ~= 0 then return 0 end
  local st = js.state
  if H.num('JarvisEnabled', 1) ~= 1 then st = 'idle' end
  local A1, W, D = H.C.accent, H.C.white, H.C.dim
  local IDLE = colorSetting('JarvisColorIdle', A1)
  local DEEP = colorSetting('JarvisColorListen', H.mix(A1, { 0, 70, 210 }, 0.55))   -- listening: a deeper blue
  local SPEAK = colorSetting('JarvisColorSpeak', IDLE)
  local OFF = H.mix(D, IDLE, 0.45)                         -- offline: dimmed, but still readable
  local col = st == 'listening' and DEEP or (st == 'offline' and OFF or (st == 'speaking' and SPEAK or IDLE))
  -- smoothing: fast attack, slower release, so everything breathes with the voice instead of jittering
  local target = (st == 'speaking' or st == 'listening') and H.clamp(js.level, 0, 1) or 0
  lvl = lvl + (target - lvl) * (target > lvl and 0.55 or 0.18)
  local wantAct = st == 'speaking' and (0.55 + 0.45 * lvl) or (st == 'thinking' and 0.25 or 0)
  act = act + (wantAct - act) * 0.25
  -- motion (per update, scaled by how many updates are skipped on lighter tiers)
  local fps = H.clamp(H.num('JarvisFrameRate', 30), 6, 60)
  local mot = H.clamp(H.num('JarvisSpeed', 1), 0.25, 3)
  local step = fps * 0.033 * every
  local speed = ({ idle = 1, listening = 0.6, thinking = 1.5, speaking = 1 + 1.6 * lvl, offline = 0.35 })[st] or 1
  speed = speed * mot
  fIdle = fIdle + step * speed
  fAct = fAct + step * (1 + 1.2 * lvl)
  local spin = (({ idle = 1, listening = 0.7, thinking = 3, speaking = 1.4 + 2 * lvl, offline = 0.3 })[st] or 1) * mot
  yaw = (yaw + 0.006 * spin * every) % (2 * math.pi)
  rot1 = (rot1 + 0.5 * spin * every) % 360
  rot2 = (rot2 + 0.8 * spin * every) % 360
  rot3 = (rot3 - 0.25 * spin * every) % 360
  sweep = (sweep + 9 * every) % 360
  -- the orb (every update) and its voice echo
  if seq.idle then
    local bright = H.clamp(H.num('JarvisOrbBright', 1), 0.4, 1.6)
    local tintS = H.clamp(H.num('JarvisTint', 0.22), 0, 0.8)
    local size = H.clamp(H.num('JarvisOrbSize', 1), 0.8, 1.15)
    local k, tint, a = 0.9, tintS, 245
    if st == 'listening' then k, tint = 0.8, tintS * 0.5 elseif st == 'speaking' then k, tint = 1.0 + 0.2 * lvl, tintS * 0.8
    elseif st == 'offline' then k, tint, a = 0.7, tintS * 0.3, 190 end
    sprite('S1_1', seq.idle, fIdle, ORB_D * size * (1 + 0.1 * lvl), col, a, k * bright, tint)
    local echo = seq.active or seq.idle
    local off = seq.active and 0 or floor(seq.idle.n / 2)
    if act * 255 >= 3 then
      sprite('S1_2', echo, (seq.active and fAct or fIdle) + off, ORB_D * H.clamp(H.num('JarvisOrbSize', 1), 0.8, 1.15) * (1.12 + 0.28 * lvl),
        H.mix(col, W, 0.4), act * 150, 1.1 * H.clamp(H.num('JarvisOrbBright', 1), 0.4, 1.6), 0.3)
    else H.hideSprite(1, 2) end
  else
    H.hideSprite(1, 1); H.hideSprite(1, 2)
  end
  -- the drawn layers at half the orb's rate (they move slowly, and that halves their cost)
  if frame % (2 * every) ~= 0 and frame > 2 then return lvl end
  local c = H.canvas(1)
  if not seq.idle then
    for k = 3, 1, -1 do c:fillCircle(CX, CY, 40 + k * 22 * (1 + 0.15 * lvl), H.mix(col, W, 0.4), floor((25 + 50 * lvl) / k)) end
    c:dot(CX, CY, 6 + 6 * lvl, W)
  end
  drawScene(c, st, col, W, D)
  -- label, bottom left of the screen
  local z = H.zones[1]
  local label = LABEL[st] or 'STANDBY'         -- status only; problems live in Control Center > JARVIS and the log
  -- launched but never came online: say so (the log usually says why)
  if startedAt and st ~= 'offline' then startedAt = nil end
  if startedAt and os.time() - startedAt > 25 then
    startedAt = nil
    note = { 'START FAILED', os.time() + 30 }
    print('Clover: the service did not start - open Control Center > CLOVER > LOG (or run SETUP)')
  end
  if note and os.time() <= note[2] then label = note[1] elseif note then note = nil end
  H.text(1, 1, 8, z.h - 26, 'J.A.R.V.I.S', { size = 5, weight = 700, align = 'LeftBottom', color = H.mix(A1, W, 0.3) })
  H.text(1, 2, 8, z.h - 12, label, { size = 4.4, weight = 700, align = 'LeftBottom', color = label == 'START FAILED' and H.C.warn or (st == 'listening' and H.mix(DEEP, W, 0.35) or (st == 'offline' and H.mix(OFF, W, 0.2) or W)), glow = false })
  for k = 3, 8 do H.hideText(1, k) end
  if frame < 6 or frame % 30 == 0 then
    local tip
    if H.num('JarvisEnabled', 1) ~= 1 then tip = 'Clover is off (JarvisEnabled=0 in Settings.inc)'
    elseif st == 'offline' then tip = 'Clover service not running   click: start it   right-click: conversation log'
    elseif st == 'idle' then tip = 'Clover running   click: talk to Clover   right-click: conversation log'
    else tip = 'Clover ' .. string.lower(LABEL[st] or '') .. '   click: stop' end
    local RR = 206
    H.hit(1, 1, CX - RR, CY - RR, RR * 2, RR * 2, tip)
    H.set('H1_1', 'Shape', string.format('Ellipse %.2f,%.2f,%.2f | Fill Color 0,0,0,1 | StrokeWidth 0', RR * H.S, RR * H.S, RR * H.S))
  end
  c:flush()
  return lvl
end

-- python launcher: JarvisPython (full path), else Setup's private copy (the pinned packages: the global Python can hold
-- other versions, and an old kokoro-onnx there drops him to the Windows voice), else the python.org py launcher
local function pythonw()
  local p = H.str('JarvisPython', '')
  if p ~= '' then return exists(p) and p or nil end
  local cands = { (os.getenv('LOCALAPPDATA') or '') .. '\\SpaceshipHUD\\venv\\Scripts\\pythonw.exe',
    (os.getenv('WINDIR') or 'C:\\Windows') .. '\\pyw.exe',
    (os.getenv('LOCALAPPDATA') or '') .. '\\Programs\\Python\\Launcher\\pyw.exe' }
  for _, c in ipairs(cands) do if exists(c) then return c end end
  return nil
end

function StartService()
  local py = pythonw()
  local script = H.res .. 'Jarvis\\jarvis.py'
  if not py then note = { 'NO PYTHON', os.time() + 6 }; print('Jarvis: Python not found - install it from python.org or set JarvisPython in Settings.inc'); return false end
  if not exists(script) then note = { 'NO SCRIPT', os.time() + 6 }; return false end
  SKIN:Bang('["' .. py .. '" "' .. script .. '" "' .. H.res .. '"]')
  note = { 'STARTING', os.time() + 10 }
  startedAt = os.time()
  return true
end

local function command(s) H.cmd(s) end

function OnClick(z, k)
  if H.num('JarvisEnabled', 1) ~= 1 then return end
  if os.time() - lastCmd < 1 then return end
  lastCmd = os.time()
  if js.state == 'offline' then StartService(); return end
  if js.state == 'idle' then command('WAKE ' .. os.time() .. ' ' .. H.tier); js.state = 'listening'
  else command('CANCEL ' .. os.time()) end
end

function OnRightClick(z, k)
  SKIN:Bang('!ToggleConfig', 'Spaceship\\Overlay\\Jarvis', 'Jarvis.ini')
end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end


-- Control Center > JARVIS
function StopService()
  command('QUIT ' .. os.time())
  note = { 'STOPPED', os.time() + 6 }
end
function Forget()
  command('FORGET ' .. os.time())
  local f = io.open(H.res .. 'Data\\jarvis_log.txt', 'w')
  if f then f:close() end
end
