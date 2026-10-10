-- Spaceship HUD shared drawing library (Lua 5.1, Rainmeter).
-- Every module script does:   H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
-- Coordinates passed to the canvas are zone-local, in base-canvas pixels (2560x1600 design);
-- the library applies the zone origin and #Scale#. The curve is applied by Rainmeter
-- through each meter's TransformationMatrix (see Geometry.inc), so nothing here bends.

local H = {}
H.cache = {}

local fmt = string.format
local floor, max, min, sqrt, cos, sin, pi = math.floor, math.max, math.min, math.sqrt, math.cos, math.sin, math.pi

local function num(name, default)
  local v = tonumber(SKIN:GetVariable(name, ''))
  if v == nil then return default end
  return v
end
H.num = num

local function str(name, default)
  local v = SKIN:GetVariable(name, '')
  if v == nil or v == '' then return default end
  return v
end
H.str = str

local function parseColor(s, fallback)
  local r, g, b, a = string.match(s or '', '^%s*(%d+)%s*,%s*(%d+)%s*,%s*(%d+)%s*,?%s*(%d*)')
  if not r then return fallback end
  return { tonumber(r), tonumber(g), tonumber(b), tonumber(a) or 255 }
end

-- Theme + runtime state; call at Initialize and whenever variables may have changed.
function H.init()
  H.S = num('Scale', 1)
  H.res = SKIN:GetVariable('@')
  H.tier = num('PerfTier', 0)
  H.hudA = num('HudAlpha', 255)
  H.glowA = num('GlowAlpha', 46)
  H.glowW = num('GlowWidth', 3.2)
  H.coreWhite = num('CoreWhite', 0.3)
  H.textGlow = num('TextGlow', 4)
  H.textGlowA = num('TextGlowAlpha', 150)
  H.textSmall = num('TextScaleSmall', 1.85)
  H.textLarge = num('TextScaleLarge', 1.45)
  H.edit = num('EditMode', 0)
  H.C = {
    accent = parseColor(str('ColorAccent', '0,210,255'), { 0, 210, 255, 255 }),
    dim = parseColor(str('ColorDim', '0,110,150'), { 0, 110, 150, 255 }),
    text = parseColor(str('ColorText', '170,235,255'), { 170, 235, 255, 255 }),
    warn = parseColor(str('ColorWarn', '255,130,40'), { 255, 130, 40, 255 }),
    alert = parseColor(str('ColorAlert', '255,60,70'), { 255, 60, 70, 255 }),
    good = parseColor(str('ColorGood', '60,255,170'), { 60, 255, 170, 255 }),
    hi = parseColor(str('ColorHighlight', '255,105,135'), { 255, 105, 135, 255 }),
    white = parseColor(str('ColorWhite', '215,240,255'), { 215, 240, 255, 255 }),
    panel = parseColor(str('ColorPanel', '0,30,45,90'), { 0, 30, 45, 90 }),
  }
  H.fontText = str('FontText', 'Oxanium')
  H.fontNum = str('FontNum', 'B612 Mono')
  H.fontTitle = str('FontTitle', 'Michroma')
  -- zones of this module
  H.zones = {}
  local n = num('ZoneCount', 0)
  for i = 1, n do
    H.zones[i] = {
      id = str('Z' .. i, 'Z' .. i),
      x = num('Z' .. i .. '_X', 0), y = num('Z' .. i .. '_Y', 0),
      w = num('Z' .. i .. '_W', 0), h = num('Z' .. i .. '_H', 0),
    }
    -- the zone's TransformationMatrix (a;b;c;d;e;f, may hold formulas): click areas are drawn already
    -- transformed (see H.hit), because Rainmeter hit-tests a meter without its matrix
    local tm, raw = {}, SKIN:ReplaceVariables(str('Z' .. i .. '_TM', '1;0;0;1;0;0'))
    for part in string.gmatch(raw .. ';', '([^;]*);') do
      local v = tonumber(part) or tonumber(SKIN:ParseFormula(part)) or 0
      tm[#tm + 1] = v
    end
    if #tm == 6 and not (tm[1] == 1 and tm[2] == 0 and tm[3] == 0 and tm[4] == 1 and tm[5] == 0 and tm[6] == 0) then
      H.zones[i].tm = tm
    end
  end
  H.capStyle = num('CaptionStyle', 1)
  local env = getfenv and getfenv(2) or _G
  H.hookCaptions(env)
  H.guard(env)
end

-- error guard: a bug or unexpected data (a missing sensor, an odd app name, a file that vanished) must not
-- freeze a module. Update and the mouse handlers of the calling script run protected: an error is written
-- to the Rainmeter log once per message (Manage > Log, "Spaceship error in ...") and the module keeps
-- running. The offline simulator sets SpaceshipStrict=1 so errors still fail the audits.
local seenErr = {}
function H.guard(env)
  if str('SpaceshipStrict', '0') == '1' or type(env) ~= 'table' then return end
  for _, name in ipairs({ 'Update', 'OnClick', 'OnRightClick', 'OnScroll', 'OnHover' }) do
    local f = rawget(env, name)
    if type(f) == 'function' then
      env[name] = function(...)
        local ok, r = pcall(f, ...)
        if ok then return r end
        local msg = tostring(r)
        if not seenErr[msg] then
          seenErr[msg] = true
          print('Spaceship error in ' .. str('CURRENTCONFIG', '?') .. ' ' .. name .. ': ' .. msg)
        end
        return 0
      end
    end
  end
end

function H.refreshTier()
  H.tier = num('PerfTier', 0)
  H.edit = num('EditMode', 0)
end

-- colour helpers -----------------------------------------------------------
function H.rgba(c, a)
  -- HudAlpha (Settings.inc) scales every widget colour: one knob for the whole HUD's transparency
  return fmt('%d,%d,%d,%d', c[1], c[2], c[3], floor((a or c[4] or 255) * (H.hudA or 255) / 255))
end

function H.mix(c1, c2, t)
  t = max(0, min(1, t))
  return { floor(c1[1] + (c2[1] - c1[1]) * t), floor(c1[2] + (c2[2] - c1[2]) * t),
           floor(c1[3] + (c2[3] - c1[3]) * t), 255 }
end

-- accent -> warn -> alert ramp for 0..1 load values
function H.ramp(v)
  if v < 0.7 then return H.C.accent end
  if v < 0.9 then return H.mix(H.C.accent, H.C.warn, (v - 0.7) / 0.2) end
  return H.mix(H.C.warn, H.C.alert, (v - 0.9) / 0.1)
end

function H.clamp(v, a, b) return max(a, min(b, v)) end

-- option setter with change cache (keeps bang traffic low)
function H.set(meter, option, value)
  local k = meter .. '\1' .. option
  if H.cache[k] ~= value then
    H.cache[k] = value
    SKIN:Bang('!SetOption', meter, option, value)
  end
end

-- Canvas -------------------------------------------------------------------
local Canvas = {}
Canvas.__index = Canvas

function H.canvas(zoneIndex)
  local z = H.zones[zoneIndex]
  local c = setmetatable({ meter = 'Draw' .. zoneIndex, z = z, ox = z.x, oy = z.y, s = H.S,
    base = {}, glow = {}, core = {}, top = {}, paths = {}, np = 0 }, Canvas)
  return c
end

function Canvas:px(x) return fmt('%.2f', (self.ox + x) * self.s) end
function Canvas:py(y) return fmt('%.2f', (self.oy + y) * self.s) end
function Canvas:pw(w) return fmt('%.2f', w * self.s) end

local function strokeMods(col, a, w, s)
  return fmt('| Fill Color 0,0,0,0 | Stroke Color %s | StrokeWidth %.2f | StrokeStartCap Round | StrokeEndCap Round | StrokeLineJoin Round',
    H.rgba(col, a), w * s)
end

-- neon bloom (reference look): wide faint halo + medium glow + bright core pulled toward white.
-- FULL tier draws all three, LITE drops the outer halo, LOW and STEALTH draw the core only.
function Canvas:neon(geom, col, w, alpha, layer)
  w = w or 1.6
  local a = alpha or col[4] or 255
  if H.tier < 2 and H.glowA > 0 then
    if H.tier == 0 then
      table.insert(self.glow, geom .. ' ' .. strokeMods(col, floor(H.glowA * 0.38 * a / 255), w * H.glowW * 2.1, self.s))
    end
    table.insert(self.glow, geom .. ' ' .. strokeMods(col, floor(H.glowA * a / 255), w * H.glowW, self.s))
  end
  local core = H.coreWhite > 0 and H.mix(col, H.C.white, H.coreWhite) or col
  table.insert(layer or self.core, geom .. ' ' .. strokeMods(core, a, w, self.s))
end

-- soft round halo for dots and lights (stacked translucent discs)
function Canvas:halo(cx, cy, r, col, alpha)
  if H.tier >= 2 then return end
  local a = alpha or 60
  for i = 3, 1, -1 do
    table.insert(self.glow, fmt('Ellipse %s,%s,%s | Fill Color %s | StrokeWidth 0',
      self:px(cx), self:py(cy), self:pw(r * (1 + i * 0.9)), H.rgba(col, floor(a / (i + 1)))))
  end
end

function Canvas:line(x1, y1, x2, y2, col, w, alpha)
  self:neon(fmt('Line %s,%s,%s,%s', self:px(x1), self:py(y1), self:px(x2), self:py(y2)), col, w, alpha)
end

-- plain (no glow) thin line, for grids and ticks
function Canvas:hair(x1, y1, x2, y2, col, w, alpha)
  table.insert(self.base, fmt('Line %s,%s,%s,%s ', self:px(x1), self:py(y1), self:px(x2), self:py(y2)) ..
    strokeMods(col, alpha or 120, w or 1, self.s))
end

function Canvas:pathDef(pts, closed)
  self.np = self.np + 1
  local name = 'P' .. self.np
  local parts = { self:px(pts[1][1]) .. ',' .. self:py(pts[1][2]) }
  for i = 2, #pts do
    parts[#parts + 1] = 'LineTo ' .. self:px(pts[i][1]) .. ',' .. self:py(pts[i][2])
  end
  if closed then parts[#parts + 1] = 'ClosePath 1' end
  self.paths[name] = table.concat(parts, ' | ')
  return name
end

function Canvas:poly(pts, col, w, alpha, closed)
  if #pts < 2 then return end
  self:neon('Path ' .. self:pathDef(pts, closed), col, w, alpha)
end

-- thin polyline without glow (back faces, grids)
function Canvas:hairPoly(pts, col, alpha, w)
  if #pts < 2 then return end
  table.insert(self.base, 'Path ' .. self:pathDef(pts, false) .. ' ' .. strokeMods(col, alpha or 120, w or 1, self.s))
end

-- filled polygon (no stroke), drawn under everything
function Canvas:fillPoly(pts, col, alpha)
  if #pts < 3 then return end
  table.insert(self.base, 'Path ' .. self:pathDef(pts, true) ..
    fmt(' | Fill Color %s | StrokeWidth 0', H.rgba(col, alpha)))
end

function Canvas:fillRect(x, y, w, h, col, alpha, r)
  table.insert(self.base, fmt('Rectangle %s,%s,%s,%s,%s | Fill Color %s | StrokeWidth 0',
    self:px(x), self:py(y), self:pw(w), self:pw(h), self:pw(r or 0), H.rgba(col, alpha)))
end

function Canvas:rect(x, y, w, h, col, lw, alpha, r)
  self:neon(fmt('Rectangle %s,%s,%s,%s,%s', self:px(x), self:py(y), self:pw(w), self:pw(h), self:pw(r or 0)), col, lw, alpha)
end

function Canvas:circle(cx, cy, r, col, lw, alpha)
  self:neon(fmt('Ellipse %s,%s,%s', self:px(cx), self:py(cy), self:pw(r)), col, lw, alpha)
end

function Canvas:dot(cx, cy, r, col, alpha)
  if (alpha or 255) > 150 then self:halo(cx, cy, r, col, 70) end
  table.insert(self.core, fmt('Ellipse %s,%s,%s | Fill Color %s | StrokeWidth 0',
    self:px(cx), self:py(cy), self:pw(r), H.rgba(col, alpha)))
end

function Canvas:fillCircle(cx, cy, r, col, alpha)
  table.insert(self.base, fmt('Ellipse %s,%s,%s | Fill Color %s | StrokeWidth 0',
    self:px(cx), self:py(cy), self:pw(r), H.rgba(col, alpha)))
end

-- arc as a polyline; angles in degrees, 0 = right, clockwise (screen coords)
-- ellipse rotated by rot degrees
function H.ellipsePts(cx, cy, rx, ry, rot, a0, a1, segs)
  local pts = {}
  local cr, sr = cos(rot * pi / 180), sin(rot * pi / 180)
  a0, a1, segs = a0 or 0, a1 or 360, segs or 40
  for i = 0, segs do
    local a = (a0 + (a1 - a0) * i / segs) * pi / 180
    local x, y = rx * cos(a), ry * sin(a)
    pts[#pts + 1] = { cx + x * cr - y * sr, cy + x * sr + y * cr }
  end
  return pts
end

function H.arcPts(cx, cy, rx, ry, a0, a1, segs)
  segs = segs or max(6, floor(math.abs(a1 - a0) / 6))
  local pts = {}
  for i = 0, segs do
    local a = (a0 + (a1 - a0) * i / segs) * pi / 180
    pts[#pts + 1] = { cx + rx * cos(a), cy + ry * sin(a) }
  end
  return pts
end

function Canvas:arc(cx, cy, r, a0, a1, col, lw, alpha, ry)
  self:poly(H.arcPts(cx, cy, r, ry or r, a0, a1), col, lw, alpha)
end

-- segmented (dashed) arc: dash / gap are absolute lengths in zone units. Rainmeter's StrokeDashes are
-- multiples of the stroke width, so each glow layer gets its own factors and the dashes stay aligned.
-- Two arcs with the same start angle and pattern line up segment for segment (track + lit part).
function Canvas:dashArc(cx, cy, r, a0, a1, col, lw, alpha, dash, gap, noGlow)
  local name = self:pathDef(H.arcPts(cx, cy, r, r, a0, a1, max(12, floor(math.abs(a1 - a0) / 3))), false)
  local function mods(c, a, w)
    return fmt('| Fill Color 0,0,0,0 | Stroke Color %s | StrokeWidth %.2f | StrokeDashCap Flat | StrokeDashes %.3f,%.3f',
      H.rgba(c, a), w * self.s, dash / w, gap / w)
  end
  local a = alpha or 255
  if not noGlow and H.tier < 2 and H.glowA > 0 then
    table.insert(self.glow, 'Path ' .. name .. ' ' .. mods(col, floor(H.glowA * a / 255), lw * 1.8))
  end
  local core = H.coreWhite > 0 and H.mix(col, H.C.white, H.coreWhite) or col
  table.insert(self.core, 'Path ' .. name .. ' ' .. mods(core, a, lw))
end

-- filled ring sector (annular wedge) a0..a1 between radii r0 and r1
function Canvas:sector(cx, cy, r0, r1, a0, a1, col, fillAlpha, strokeAlpha)
  local pts = H.arcPts(cx, cy, r1, r1, a0, a1, 10)
  local inner = H.arcPts(cx, cy, r0, r0, a1, a0, 10)
  for _, p in ipairs(inner) do pts[#pts + 1] = p end
  self:fillPoly(pts, col, fillAlpha or 40)
  if strokeAlpha and strokeAlpha > 0 then self:poly(pts, col, 1, strokeAlpha, true) end
end

-- segmented bar (visual, not numbers): n segments filled to fraction v
function Canvas:segBar(x, y, w, h, v, n, col, gap)
  gap = gap or 3
  local sw = (w - gap * (n - 1)) / n
  local lit = floor(H.clamp(v, 0, 1) * n + 0.5)
  for i = 0, n - 1 do
    local sx = x + i * (sw + gap)
    if i < lit then
      self:fillRect(sx, y, sw, h, col or H.ramp((i + 1) / n), 230)
    else
      self:fillRect(sx, y, sw, h, H.C.dim, 60)
    end
  end
end

-- history graph from a list of 0..1 values
function Canvas:graph(x, y, w, h, hist, col, fillAlpha)
  local n = #hist
  if n < 2 then return end
  local pts = {}
  for i = 1, n do
    pts[i] = { x + (i - 1) * w / (n - 1), y + h - H.clamp(hist[i], 0, 1) * h }
  end
  local area = { { x, y + h } }
  for i = 1, n do area[#area + 1] = pts[i] end
  area[#area + 1] = { x + w, y + h }
  self:fillPoly(area, col, fillAlpha or 40)
  self:poly(pts, col, 1.4)
end

-- corner brackets around a box (reference-style panel frame)
function Canvas:brackets(x, y, w, h, len, col, lw, alpha)
  len = len or 14
  self:poly({ { x, y + len }, { x, y }, { x + len, y } }, col, lw, alpha)
  self:poly({ { x + w - len, y }, { x + w, y }, { x + w, y + len } }, col, lw, alpha)
  self:poly({ { x + w, y + h - len }, { x + w, y + h }, { x + w - len, y + h } }, col, lw, alpha)
  self:poly({ { x + len, y + h }, { x, y + h }, { x, y + h - len } }, col, lw, alpha)
end

-- angled panel outline (chamfered corners)
function Canvas:chamfer(x, y, w, h, c, col, lw, alpha, fillAlpha)
  local pts = { { x + c, y }, { x + w, y }, { x + w, y + h - c }, { x + w - c, y + h }, { x, y + h }, { x, y + c } }
  if fillAlpha and fillAlpha > 0 then self:fillPoly(pts, H.C.panel, fillAlpha) end
  self:poly(pts, col, lw, alpha, true)
end

function Canvas:flush()
  local list = {}
  for _, s in ipairs(self.base) do list[#list + 1] = s end
  for _, s in ipairs(self.glow) do list[#list + 1] = s end
  for _, s in ipairs(self.core) do list[#list + 1] = s end
  for _, s in ipairs(self.top) do list[#list + 1] = s end
  if H.edit == 1 then
    -- edit mode: zone outline + id so modules can be lined up
    local z = self.z
    list[#list + 1] = fmt('Rectangle %s,%s,%s,%s | Fill Color 255,200,0,18 | Stroke Color 255,200,0,200 | StrokeWidth 2',
      self:px(0), self:py(0), self:pw(z.w), self:pw(z.h))
  end
  for name, def in pairs(self.paths) do H.set(self.meter, name, def) end
  local m = self.meter
  local prev = H.cache[m .. '\1#count'] or 0
  for i, s in ipairs(list) do
    H.set(m, i == 1 and 'Shape' or ('Shape' .. i), s)
  end
  local empty = 'Rectangle 0,0,0,0 | Fill Color 0,0,0,0 | StrokeWidth 0'
  for i = #list + 1, prev do
    H.set(m, i == 1 and 'Shape' or ('Shape' .. i), empty)
  end
  if #list == 0 then H.set(m, 'Shape', empty) end
  H.cache[m .. '\1#count'] = max(#list, 1)
end

-- Text -----------------------------------------------------------------------
-- opts: size, color, alpha, align ('Left','Center','Right' + 'Top','Center','Bottom'), font, weight
function H.text(zoneIndex, k, x, y, txt, opts)
  opts = opts or {}
  local z = H.zones[zoneIndex]
  local m = 'T' .. zoneIndex .. '_' .. k
  H.set(m, 'X', fmt('%.2f', (z.x + x) * H.S))
  H.set(m, 'Y', fmt('%.2f', (z.y + y) * H.S))
  H.set(m, 'Text', txt or '')
  -- small HUD text is drawn larger so it matches the reference's cap heights on the 2560x1600 canvas
  local sz = opts.size or 11
  sz = sz * (sz < 9.5 and H.textSmall or H.textLarge)
  H.set(m, 'FontSize', fmt('%.2f', sz * H.S))
  local tc = opts.color or H.C.text
  H.set(m, 'FontColor', H.rgba(H.coreWhite > 0 and H.mix(tc, H.C.white, H.coreWhite * 0.5) or tc, opts.alpha))
  -- text glow: zero-offset blurred shadow in the text's own colour (off on LOW / STEALTH)
  if H.tier < 2 and H.textGlow > 0 and opts.glow ~= false then
    H.set(m, 'InlineSetting', fmt('Shadow | 0 | 0 | %.1f | %s', H.textGlow * H.S, H.rgba(tc, floor(H.textGlowA * (opts.alpha or 255) / 255))))
  else
    H.set(m, 'InlineSetting', 'Shadow | 0 | 0 | 0 | 0,0,0,0')
  end
  H.set(m, 'StringAlign', opts.align or 'LeftTop')
  H.set(m, 'FontFace', opts.font or H.fontText)
  H.set(m, 'FontWeight', tostring(opts.weight or 600))
  if opts.clip then
    H.set(m, 'W', fmt('%.0f', opts.clip * H.S))
    H.set(m, 'ClipString', '1')
  end
  H.set(m, 'Hidden', '0')
end

function H.hideText(zoneIndex, k)
  H.set('T' .. zoneIndex .. '_' .. k, 'Hidden', '1')
end

-- Hit areas ---------------------------------------------------------------------
-- App icon from @Resources\Icons (made by Scripts\app-icons.ps1): the greyscale icon recoloured from the theme
-- colour (dark parts) to white (bright parts) with a ColorMatrix, over a blurred glow tinted in the theme colour.
-- Returns false when there is no icon file, so the caller can draw its line icon instead.
local iconCache = {}
function H.hasIcon(id)
  if not id then return false end
  if iconCache[id] == nil then
    local f = io.open(H.res .. 'Icons\\' .. id .. '.png', 'rb')
    iconCache[id] = f ~= nil
    if f then f:close() end
  end
  return iconCache[id]
end

function H.image(zoneIndex, k, cx, cy, size, id, alpha)
  local gm, im = 'G' .. zoneIndex .. '_' .. k, 'I' .. zoneIndex .. '_' .. k
  if not H.hasIcon(id) then H.set(gm, 'Hidden', '1'); H.set(im, 'Hidden', '1'); return false end
  local z = H.zones[zoneIndex]
  local base = H.res .. 'Icons\\' .. id
  local a = floor((alpha or 255) * (H.hudA or 255) / 255)
  local A1 = H.C.accent
  local function place(m, s)
    H.set(m, 'X', fmt('%.2f', (z.x + cx - s / 2) * H.S))
    H.set(m, 'Y', fmt('%.2f', (z.y + cy - s / 2) * H.S))
    H.set(m, 'W', fmt('%.2f', s * H.S)); H.set(m, 'H', fmt('%.2f', s * H.S))
    H.set(m, 'Hidden', '0')
  end
  H.set(gm, 'ImageName', base .. '_glow.png')
  H.set(gm, 'ImageTint', fmt('%d,%d,%d', A1[1], A1[2], A1[3]))
  H.set(gm, 'ImageAlpha', tostring(H.tier < 2 and floor(a * 0.8) or 0))
  place(gm, size * 1.25)
  local r, g, b = A1[1] / 255, A1[2] / 255, A1[3] / 255
  H.set(im, 'ImageName', base .. '.png')
  H.set(im, 'ColorMatrix1', fmt('%.3f;%.3f;%.3f;0;0', 1 - r, 1 - g, 1 - b))
  H.set(im, 'ColorMatrix2', '0;0;0;0;0')
  H.set(im, 'ColorMatrix3', '0;0;0;0;0')
  H.set(im, 'ColorMatrix4', '0;0;0;1;0')
  H.set(im, 'ColorMatrix5', fmt('%.3f;%.3f;%.3f;0;1', r, g, b))
  H.set(im, 'ImageAlpha', tostring(a))
  place(im, size)
  return true
end

-- soft light sprite from @Resources\Images (pre-blurred, white + alpha) tinted at runtime; drawn behind the
-- zone's shapes. cx, cy = centre in zone units, w, h = size.
function H.sprite(zoneIndex, k, cx, cy, w, h, file, col, alpha)
  local z = H.zones[zoneIndex]
  local m = 'S' .. zoneIndex .. '_' .. k
  H.set(m, 'ImageName', H.res .. 'Images\\' .. file)
  H.set(m, 'ImageTint', fmt('%d,%d,%d', col[1], col[2], col[3]))
  H.set(m, 'ImageAlpha', tostring(floor((alpha or 255) * (H.hudA or 255) / 255)))
  H.set(m, 'X', fmt('%.2f', (z.x + cx - w / 2) * H.S))
  H.set(m, 'Y', fmt('%.2f', (z.y + cy - h / 2) * H.S))
  H.set(m, 'W', fmt('%.2f', w * H.S)); H.set(m, 'H', fmt('%.2f', h * H.S))
  H.set(m, 'Hidden', '0')
end

function H.hideSprite(zoneIndex, k) H.set('S' .. zoneIndex .. '_' .. k, 'Hidden', '1') end

function H.hideImage(zoneIndex, k)
  H.set('G' .. zoneIndex .. '_' .. k, 'Hidden', '1'); H.set('I' .. zoneIndex .. '_' .. k, 'Hidden', '1')
end

-- HUD captions --------------------------------------------------------------------
-- Hover hints are drawn by the HUD itself (Caption.inc, included after each module's meters) instead of
-- Windows tooltips: themed, placed beside the thing you point at, and hidden on mouse-leave with a
-- failsafe timeout (a skin under another full-screen layer can miss its mouse-leave, which is what left
-- Windows tooltips stuck). CaptionStyle=0 in Settings.inc brings the Windows tooltips back.
H.tips = {}
local cap = { key = nil, t = 0 }
local CAP_TIMEOUT = 6

local function capFormat(tip)
  -- "Launch RASAero II   scroll: next app" -> "LAUNCH RASAERO II  ▸  SCROLL: NEXT APP"
  local s = string.upper(tip or '')
  s = string.gsub(s, '%s%s+%-%s+', '  \226\150\184  ')
  s = string.gsub(s, '%s%s%s*', '  \226\150\184  ')
  return s
end

function H.caption(zi, k, on)
  if H.capStyle == 0 then return end
  local key = zi .. '_' .. k
  if on == 1 then
    local t = H.tips[key]
    if not t or t.tip == '' then return end
    local txt = capFormat(t.tip)
    local fs = 6.4 * H.textSmall
    local fpx = fs * H.S * 96 / 72
    local tw = (string.len(string.gsub(txt, '[\128-\191]', ''))) * fpx * 0.65 + 2 * 7 * H.S
    local th = fpx * 1.35 + 2 * 3.5 * H.S
    local W, Hs = num('WW', 400) * H.S, num('WH', 300) * H.S
    local x = H.clamp(t.x0 + (t.x1 - t.x0) / 2 - tw / 2, 2, math.max(2, W - tw - 2))
    local y = t.y1 + 4 * H.S
    if y + th > Hs - 2 then y = t.y0 - th - 4 * H.S end
    if y < 2 then y = H.clamp(t.y0 + 4 * H.S, 2, math.max(2, Hs - th - 2)) end
    local c = 6 * H.S
    H.set('CaptionBox', 'Box', fmt('%.1f,%.1f | LineTo %.1f,%.1f | LineTo %.1f,%.1f | LineTo %.1f,%.1f | LineTo %.1f,%.1f | ClosePath 1',
      x + c, y, x + tw, y, x + tw, y + th - c, x + tw - c, y + th, x, y + th) .. fmt(' | LineTo %.1f,%.1f', x, y + c))
    H.set('CaptionBox', 'Shape', fmt('Path Box | Fill Color %s | Stroke Color %s | StrokeWidth %.2f',
      H.rgba({ 2, 14, 22 }, 215), H.rgba(H.C.accent, 200), 1.2 * H.S))
    H.set('Caption', 'X', fmt('%.1f', x + 7 * H.S)); H.set('Caption', 'Y', fmt('%.1f', y + th / 2))
    H.set('Caption', 'Text', txt)
    H.set('Caption', 'FontSize', fmt('%.2f', fs * H.S))
    H.set('Caption', 'FontFace', H.fontNum)
    H.set('Caption', 'FontColor', H.rgba(H.mix(H.C.text, H.C.white, 0.4), 255))
    H.set('Caption', 'InlineSetting', H.tier < 2 and fmt('Shadow | 0 | 0 | %.1f | %s', 3 * H.S, H.rgba(H.C.accent, 140)) or 'Shadow | 0 | 0 | 0 | 0,0,0,0')
    H.set('CaptionBox', 'Hidden', '0'); H.set('Caption', 'Hidden', '0')
    cap.key, cap.t = key, os.time()
    SKIN:Bang('!UpdateMeter', 'CaptionBox'); SKIN:Bang('!UpdateMeter', 'Caption'); SKIN:Bang('!Redraw')
  elseif cap.key == key then
    H.hideCaption()
  end
end

function H.hideCaption()
  if not cap.key then return end
  cap.key = nil
  H.set('CaptionBox', 'Hidden', '1'); H.set('Caption', 'Hidden', '1')
  SKIN:Bang('!UpdateMeter', 'CaptionBox'); SKIN:Bang('!UpdateMeter', 'Caption'); SKIN:Bang('!Redraw')
end

-- wraps the module's OnHover / Update so every module gets captions without changing its script
function H.hookCaptions(env)
  if type(env) ~= 'table' or rawget(env, '__capHooked') then return end
  env.__capHooked = true
  local hover, update = rawget(env, 'OnHover'), rawget(env, 'Update')
  env.OnHover = function(zi, k, on)
    H.caption(zi, k, on)
    if hover then return hover(zi, k, on) end
  end
  if update then
    env.Update = function(...)
      if cap.key and os.time() - cap.t > CAP_TIMEOUT then H.hideCaption() end
      return update(...)
    end
  end
end

-- measured width (zone units) of text meter T<zi>_<k> as Rainmeter last drew it; estimate until it has
function H.textWidth(zi, k, txt, size)
  local m = SKIN:GetMeter('T' .. zi .. '_' .. k)
  local w = m and m:GetW() or 0
  local sz = size * (size < 9.5 and H.textSmall or H.textLarge)
  local est = string.len(txt or '') * sz * 96 / 72 * 0.65
  if w and w > 0 and H.cache['T' .. zi .. '_' .. k .. '\1Text'] == txt then
    return w / H.S
  end
  return est
end

-- bounding box of an icons.lua drawing, in its 100x100 authoring box: x0, y0, x1, y1
local boundsCache = {}
function H.iconBounds(name)
  if boundsCache[name] then return unpack(boundsCache[name]) end
  local def = H.icons[name] or H.icons.gear
  local x0, y0, x1, y1 = 100, 100, 0, 0
  local function add(x, y) x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y) end
  for _, p in ipairs(def) do
    local t = p[1]
    if t == 'l' or t == 'p' then
      for i = 2, #p - 1, 2 do add(p[i], p[i + 1]) end
    elseif t == 'c' then add(p[2] - p[4], p[3] - p[4]); add(p[2] + p[4], p[3] + p[4])
    elseif t == 'a' then add(p[2] - p[4], p[3] - (p[7] or p[4])); add(p[2] + p[4], p[3] + (p[7] or p[4]))
    elseif t == 'e' then add(p[2] - p[4], p[3] - p[5]); add(p[2] + p[4], p[3] + p[5]) end
  end
  if x1 <= x0 then x0, y0, x1, y1 = 0, 0, 100, 100 end
  boundsCache[name] = { x0, y0, x1, y1 }
  return x0, y0, x1, y1
end

function H.hit(zoneIndex, k, x, y, w, h, tip)
  local z = H.zones[zoneIndex]
  local m = 'H' .. zoneIndex .. '_' .. k
  local tm = z.tm
  -- remember the hit's on-screen box for its caption
  do
    local function P(px, py)
      px, py = (z.x + px) * H.S, (z.y + py) * H.S
      if tm then return tm[1] * px + tm[3] * py + tm[5], tm[2] * px + tm[4] * py + tm[6] end
      return px, py
    end
    local ax, ay = P(x, y); local bx, by = P(x + w, y); local cx2, cy2 = P(x + w, y + h); local dx, dy = P(x, y + h)
    H.tips[zoneIndex .. '_' .. k] = { tip = tip or '', x0 = min(ax, bx, cx2, dx), y0 = min(ay, by, cy2, dy),
      x1 = max(ax, bx, cx2, dx), y1 = max(ay, by, cy2, dy) }
  end
  if tm then
    -- slanted zone: the click area is the tilted quad itself, in skin coordinates, with no matrix
    local function T(px, py)
      px, py = (z.x + px) * H.S, (z.y + py) * H.S
      return fmt('%.2f,%.2f', tm[1] * px + tm[3] * py + tm[5], tm[2] * px + tm[4] * py + tm[6])
    end
    H.set(m, 'TransformationMatrix', '1;0;0;1;0;0')
    H.set(m, 'X', '0'); H.set(m, 'Y', '0')
    H.set(m, 'Quad', T(x, y) .. ' | LineTo ' .. T(x + w, y) .. ' | LineTo ' .. T(x + w, y + h) .. ' | LineTo ' .. T(x, y + h) .. ' | ClosePath 1')
    H.set(m, 'Shape', 'Path Quad | Fill Color 0,0,0,1 | StrokeWidth 0')
  else
    H.set(m, 'X', fmt('%.2f', (z.x + x) * H.S))
    H.set(m, 'Y', fmt('%.2f', (z.y + y) * H.S))
    H.set(m, 'Shape', fmt('Rectangle 0,0,%.2f,%.2f | Fill Color 0,0,0,1 | StrokeWidth 0', w * H.S, h * H.S))
  end
  H.set(m, 'ToolTipText', H.capStyle == 0 and (tip or '') or '')
  H.set(m, 'Hidden', '0')
end

function H.hideHit(zoneIndex, k)
  H.set('H' .. zoneIndex .. '_' .. k, 'Hidden', '1')
end

-- Measures ------------------------------------------------------------------------
function H.val(name, default)
  local m = SKIN:GetMeasure(name)
  if not m then return default end
  return m:GetValue()
end

function H.sval(name, default)
  local m = SKIN:GetMeasure(name)
  if not m then return default end
  return m:GetStringValue()
end

-- App state from the ShipCore helper (Data\windows.txt): 2 = has an open window, 1 = running in the
-- background only (tray / service / background browser), 0 = not running. nil = helper not running or its
-- file is stale - callers then fall back to the old process check.
local win = { t = -100, wins = {}, procs = {}, beat = 0 }
function H.appState(proc)
  if not proc or proc == '' then return 0 end
  local now = os.time()                  -- wall clock (os.clock is CPU time and barely moves)
  if now ~= win.t then
    win.t = now
    local f = io.open(H.res .. 'Data\\windows.txt', 'r')
    if f then
      local wins, procs, beat = {}, {}, 0
      for line in f:lines() do
        local k, v = string.match(line, '^(%u) (.+)$')
        if k == 'W' then wins[v] = true elseif k == 'P' then procs[v] = true elseif k == 'T' then beat = tonumber(v) or 0 end
      end
      f:close()
      win.wins, win.procs, win.beat = wins, procs, beat
    end
  end
  if os.time() - win.beat > 15 then return nil end
  local p = string.lower(proc)
  if win.wins[p] then return 2 end
  if win.procs[p] then return 1 end
  return 0
end

-- Legion Toolkit state shared by the top console (Data\llt_state.txt): { hybrid=, power=, refresh=, battery= }
function H.llt()
  local t = {}
  local f = io.open(H.res .. 'Data\\llt_state.txt', 'r')
  if not f then return t end
  for line in f:lines() do
    local k, v = string.match(line, '^(%w+) ?(.*)$')
    if k then t[k] = v end
  end
  f:close()
  return t
end

-- HWiNFO value through the registry gadget; nil when not mapped / not running
function H.hw(name)
  if num('HW_' .. string.sub(name, 4), -1) < 0 then return nil end
  local m = SKIN:GetMeasure(name)
  if not m then return nil end
  local s = m:GetStringValue()
  local v = tonumber(s and string.match(s, '-?[%d%.]+'))
  return v
end

-- Formatting -------------------------------------------------------------------------
function H.bytes(b)
  local u = { 'B', 'KB', 'MB', 'GB', 'TB' }
  local i = 1
  while b >= 1024 and i < #u do b = b / 1024; i = i + 1 end
  if b >= 100 or i == 1 then return fmt('%.0f %s', b, u[i]) end
  return fmt('%.1f %s', b, u[i])
end

function H.rate(bps)
  return H.bytes(bps) .. '/s'
end

-- network speed in megabits per second (bps = bytes per second, as Rainmeter's NetIn / NetOut report)
-- compact: no space and whole numbers from 10 up ("212Mbps", "4.2Mbps") for tight cells
function H.mbps(bps, compact)
  local m = (bps or 0) * 8 / 1000000
  if compact then
    if m >= 9.95 then return fmt('%.0fMbps', m) end
    return fmt('%.1fMbps', m)
  end
  if m >= 99.5 then return fmt('%.0f Mbps', m) end
  return fmt('%.1f Mbps', m)
end

function H.duration(sec)
  if not sec or sec < 0 then return '--:--' end
  local h = floor(sec / 3600)
  local m = floor((sec % 3600) / 60)
  return fmt('%d:%02d', h, m)
end

-- persist a variable for this session and in a file
function H.save(var, value, file)
  SKIN:Bang('!SetVariable', var, value)
  SKIN:Bang('!WriteKeyValue', 'Variables', var, value, file or (SKIN:GetVariable('@') .. 'Settings.inc'))
end

function H.broadcast(var, value)
  SKIN:Bang('!SetVariableGroup', var, value, 'Spaceship')
end

-- Icons ---------------------------------------------------------------------------
H.icons = dofile(SKIN:GetVariable('@') .. 'Scripts\\icons.lua')

-- draw icon `name` centred at cx,cy with size `sz` (icons are authored in a 100x100 box)
function Canvas:icon(name, cx, cy, sz, col, lw, alpha)
  local def = H.icons[name] or H.icons.gear
  local k = sz / 100
  local function P(x, y) return { cx + (x - 50) * k, cy + (y - 50) * k } end
  for _, p in ipairs(def) do
    local t = p[1]
    if t == 'l' then
      local pts = {}
      for i = 2, #p, 2 do pts[#pts + 1] = P(p[i], p[i + 1]) end
      self:poly(pts, col, lw, alpha, false)
    elseif t == 'p' then
      local pts = {}
      for i = 2, #p, 2 do pts[#pts + 1] = P(p[i], p[i + 1]) end
      self:poly(pts, col, lw, alpha, true)
    elseif t == 'c' then
      self:circle(cx + (p[2] - 50) * k, cy + (p[3] - 50) * k, p[4] * k, col, lw, alpha)
    elseif t == 'a' then
      self:poly(H.arcPts(cx + (p[2] - 50) * k, cy + (p[3] - 50) * k, p[4] * k, (p[7] or p[4]) * k, p[5], p[6]), col, lw, alpha)
    elseif t == 'e' then
      self:poly(H.arcPts(cx + (p[2] - 50) * k, cy + (p[3] - 50) * k, p[4] * k, p[5] * k, 0, 360, 36), col, lw, alpha)
    end
  end
end

return H
