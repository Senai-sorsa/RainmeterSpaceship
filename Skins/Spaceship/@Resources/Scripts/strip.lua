-- Bottom info strip (B_strip, 960 x 72), drawn along the dash arc. Reference: "1500 . 7 . 0% . 443 ... 20 . 20".
local H

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function fmt(v, f) if v == nil then return '--' end; return string.format(f, v) end

function Update()
  H.refreshTier()
  local z = H.zones[1]
  local c = H.canvas(1)
  local A1, D, T = H.C.accent, H.C.dim, H.C.text
  local cells = {
    { 'gauge', 'CPU', fmt(H.hw('mHwCpuTemp'), '%.0fC'), H.hw('mHwCpuTemp') and H.hw('mHwCpuTemp') >= H.num('WarnCpuTemp', 92) },
    { 'gpu', 'GPU', fmt(H.hw('mHwGpuTemp'), '%.0fC'), H.hw('mHwGpuTemp') and H.hw('mHwGpuTemp') >= H.num('WarnGpuTemp', 85) },
    { 'gear', 'FAN L', fmt(H.hw('mHwFan1'), '%.0f') },
    { 'gear', 'FAN R', fmt(H.hw('mHwFan2'), '%.0f') },
    { 'wave', 'LOAD', string.format('%d%%', H.val('mCPU', 0)) },
    { 'cloud', 'DOWN', H.rate(H.val('mNetIn', 0)) },
    { 'nodes', 'UP', H.rate(H.val('mNetOut', 0)) },
    { 'globe', 'PING', string.format('%dms', H.val('mPing', 0)) },
    { 'satellite', 'WIFI', string.format('%d%%', H.val('mWifi', 0)) },
    { 'shield', 'WEAR', fmt(H.hw('mHwWear'), '%.1f%%') },
  }
  local n = #cells
  local cw = z.w / n
  local function arcY(x) local u = (x - z.w / 2) / (z.w / 2); return -10 * u * u end
  -- strip body: angled ends + separators following the arc
  local top, bot = {}, {}
  for i = 0, 20 do
    local x = z.w * i / 20
    top[#top + 1] = { x, 16 + arcY(x) }
    bot[#bot + 1] = { x, 66 + arcY(x) }
  end
  local body = {}
  for _, p in ipairs(top) do body[#body + 1] = p end
  for i = #bot, 1, -1 do body[#body + 1] = bot[i] end
  c:fillPoly(body, H.C.panel, 120)
  c:poly(top, D, 1.2, 220)
  c:poly(bot, D, 1.2, 220)
  for i, cell in ipairs(cells) do
    local x = (i - 0.5) * cw
    local y = 41 + arcY(x)
    if i > 1 then c:hair((i - 1) * cw, 20 + arcY((i - 1) * cw), (i - 1) * cw, 62 + arcY((i - 1) * cw), D, 1, 160) end
    local col = cell[4] and H.C.warn or A1
    c:icon(cell[1], x - cw / 2 + 18, y, 22, col, 1.3)
    H.text(1, i * 2 - 1, x - cw / 2 + 34, y - 15, cell[2], { size = 7.5, weight = 700, color = D })
    H.text(1, i * 2, x - cw / 2 + 34, y - 3, cell[3], { size = 10, font = H.fontNum, color = cell[4] and H.C.warn or T, clip = cw - 38 })
  end
  H.hit(1, 1, 0, 10, z.w, 60, 'System telemetry (temps and fans need HWiNFO - Control Center > SENSORS)')
  c:flush()
  return 0
end

function OnClick(z, k) SKIN:Bang('["taskmgr.exe" "/7"]') end
function OnRightClick(z, k) end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
