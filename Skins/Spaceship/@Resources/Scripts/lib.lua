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

function H.hideImage(zoneIndex, k)
  H.set('G' .. zoneIndex .. '_' .. k, 'Hidden', '1'); H.set('I' .. zoneIndex .. '_' .. k, 'Hidden', '1')
end

function H.hit(zoneIndex, k, x, y, w, h, tip)
  local z = H.zones[zoneIndex]
  local m = 'H' .. zoneIndex .. '_' .. k
  H.set(m, 'X', fmt('%.2f', (z.x + x) * H.S))
  H.set(m, 'Y', fmt('%.2f', (z.y + y) * H.S))
  H.set(m, 'Shape', fmt('Rectangle 0,0,%.2f,%.2f | Fill Color 0,0,0,1 | StrokeWidth 0', w * H.S, h * H.S))
  H.set(m, 'ToolTipText', tip or '')
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
