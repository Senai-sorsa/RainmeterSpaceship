-- Network block (right side, mirror image of the mission clock on the left - same rails and rows).
-- PING latency, LAN (this PC's address), WAN (public address, or OFFLINE), live down / up in Mbps.
-- Emblem: Wi-Fi rings with the last speed test (Mbps) in the box - click it to run a new speed test.
-- Click the LAN / WAN rows to mask the addresses (kept across refreshes: IpMask in Settings.inc).
local H
local SXR, SYR = 2560 / 1260, 1600 / 709
local wan, wanOk = '', nil
local tick = 0
local speed = { state = '', down = nil, up = nil, t = 0 }

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

function OnWan(ok)
  if ok == 1 then
    local s = string.match(H.sval('mWAN', ''), '(%d+%.%d+%.%d+%.%d+)')
    if s then wan, wanOk = s, true else wanOk = false end
  else wanOk = false end
end

local function readSpeed()
  local f = io.open(H.res .. 'Data\\speed.txt', 'r')
  if not f then return end
  local s = { state = '', t = 0 }
  for line in f:lines() do
    local k, v = string.match(line, '^(%u+) (.+)$')
    if k == 'STATE' then s.state = v elseif k == 'DOWN' then s.down = tonumber(v)
    elseif k == 'UP' then s.up = tonumber(v) elseif k == 'T' then s.t = tonumber(v) or 0
    elseif k == 'ERR' then s.err = v end
  end
  f:close()
  -- a test that never finished (closed mid-way) shouldn't spin forever
  if s.state == 'testing' and os.time() - s.t > 180 then s.state = 'error'; s.err = 'timed out' end
  speed = s
end

local function mask(ip)
  if H.num('IpMask', 0) == 1 then return (string.gsub(ip, '%d', 'X')) end
  return ip
end

function Update()
  H.refreshTier()
  tick = tick + 1
  if tick % 2 == 1 then readSpeed() end
  local z = H.zones[1]
  local c = H.canvas(1)
  local A1, W, D = H.C.accent, H.C.white, H.C.dim
  local function X(rx) return z.w - (rx - 34) * SXR end
  local function Y(ry) return (ry - 220) * SYR end
  c:line(X(40), Y(228), X(226), Y(228), A1, 1.3, 220)
  c:dot(X(40), Y(228), 3, A1); c:dot(X(226), Y(228), 3, A1)
  -- emblem: ring + Wi-Fi arcs, box = last speed test download (click to test)
  local gx, gy = X(100), Y(256)
  local wifi = H.val('mWifi', 0)
  c:circle(gx, gy, 40, W, 1, 90)
  for i = 1, 3 do
    local lit = wifi >= i * 30
    c:arc(gx, gy + 12, 9 + i * 8, 225, 315, lit and W or D, 1.6, lit and 255 or 120)
  end
  c:dot(gx, gy + 12, 2.6, W)
  local testing = speed.state == 'testing'
  local link = H.num('LinkDownMbps', 0)
  local boxTxt = testing and string.rep('.', tick % 4) or (link > 0 and string.format('%d', link) or 'TEST')
  local bw = 40
  c:rect(gx + 30, gy + 12, bw, 22, testing and H.C.warn or A1, 1.5)
  H.text(1, 9, gx + 30 + bw / 2, gy + 23, boxTxt, { size = 6.4, weight = 700, align = 'CenterCenter', color = testing and H.C.warn or A1, font = H.fontNum })
  -- rows: label (inner side) + value (outer side)
  local ping = H.val('mPing', 0)
  local lost = ping <= 0 or ping >= 2999
  local pcol = lost and H.C.alert or (ping >= 150 and H.C.warn or W)
  local lan = H.sval('mIP', '')
  if lan == '' or lan == '0.0.0.0' then lan = nil end
  local online = (not lost) or wanOk
  local down, up = H.val('mNetIn', 0), H.val('mNetOut', 0)
  local function m(b) local v = b * 8 / 1000000; return v >= 99.5 and string.format('%.0f', v) or string.format('%.1f', v) end
  local rows = {
    { 'PING', lost and 'LOST' or string.format('%d MS', ping), pcol },
    { 'LAN', lan and mask(lan) or 'NONE', lan and W or H.C.warn },
    { 'WAN', online and (wan ~= '' and mask(wan) or '...') or 'OFFLINE', online and W or H.C.alert },
    { 'MBPS', m(down), W },
  }
  -- four rows spaced evenly between the top rail and the bottom rails, with clear space to both
  for i, r in ipairs(rows) do
    local y = Y(({ 243.5, 252.5, 261.5, 270.5 })[i])
    H.text(1, i * 2 - 1, X(151), y, r[1], { size = 6.2, weight = 700, align = 'LeftCenter', color = i == 4 and H.mix(A1, W, 0.3) or r[3] })
    if i < 4 then
      H.text(1, i * 2, X(157), y, r[2], { size = 5.6, weight = 700, align = 'RightCenter', color = r[3], font = H.fontNum, clip = X(157) - X(224) })
    else
      -- down / up speeds with drawn arrows (plain ASCII text: Rainmeter shows UTF-8 arrows from Lua as garbage)
      local us = m(up)
      local xu = X(157)
      H.text(1, 10, xu, y, us, { size = 5.6, weight = 700, align = 'RightCenter', color = W, font = H.fontNum })
      local xa = xu - H.textWidth(1, 10, us, 5.6) - 5
      c:fillPoly({ { xa - 3.5, y + 2.5 }, { xa + 3.5, y + 2.5 }, { xa, y - 3.5 } }, A1, 235)
      local xd = xa - 9
      H.text(1, 8, xd, y, r[2], { size = 5.6, weight = 700, align = 'RightCenter', color = W, font = H.fontNum })
      local xb = xd - H.textWidth(1, 8, r[2], 5.6) - 5
      c:fillPoly({ { xb - 3.5, y - 2.5 }, { xb + 3.5, y - 2.5 }, { xb, y + 3.5 } }, A1, 235)
    end
  end
  local function ly(rx, base) return base - (10 / 196 - 4 / 187) * (rx - 34) * SYR end
  c:line(X(35), ly(35, z.h - 9), X(222), ly(222, z.h - 9), A1, 1.3, 220)
  c:line(X(35), ly(35, z.h - 2.5), X(222), ly(222, z.h - 2.5), A1, 1, 160)
  if tick < 3 or tick % 5 == 0 then
    local masked = H.num('IpMask', 0) == 1
    H.hit(1, 1, 0, 0, z.w, z.h, string.format('Network   ping %s   down %s   up %s', lost and 'lost' or (ping .. ' ms'), H.mbps(down), H.mbps(up)))
    H.hit(1, 2, X(224), Y(248), X(140) - X(224), Y(266) - Y(248), masked and 'Show IP addresses' or 'Hide IP addresses')
    local st = testing and 'Speed test running...' or (speed.state == 'error' and ('Speed test failed: ' .. (speed.err or '?')) or
      (link > 0 and string.format('Last speed test %d / %d Mbps  %s   click: test again', link, H.num('LinkUpMbps', 0), H.str('LastSpeedTest', '')) or 'Click: run a speed test'))
    H.hit(1, 3, gx - 42, gy - 42, 116, 84, st)
  end
  c:flush()
  return ping
end

function OnClick(z, k)
  if k == 2 then
    H.save('IpMask', H.num('IpMask', 0) == 1 and 0 or 1)
    Update()
  elseif k == 3 then
    if speed.state ~= 'testing' then
      SKIN:Bang('["' .. H.res .. 'Bin\\ShipCore.exe" speedtest "' .. H.res .. '"]')
      speed.state = 'testing'; speed.t = os.time()
    end
  else
    SKIN:Bang('["ms-settings:network-status"]')
  end
end
function OnRightClick(z, k) SKIN:Bang('["ms-settings:network-wifi"]') end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
