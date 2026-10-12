-- Top console: GPU mode tabs + quick settings. Zone T_settings (580 x 104).
local H, Z
local st = { hybrid = '', power = '', refresh = '', battery = '', dgpu = '', llt = '' }
local armed, armedAt = nil, 0
local tick, msg, msgAt = 0, '', 0
local hudHidden = false
local TABS = { { id = 'ECO', key = 'LltHybridECO', tip = 'Integrated GPU only (RTX 5070 powered off)' },
               { id = 'HYBRID', key = 'LltHybridHYBRID', tip = 'Both GPUs - the RTX wakes when an app needs it' },
               { id = 'AUTO', key = 'LltHybridAUTO', tip = 'Hybrid on AC, integrated only on battery' },
               { id = 'dGPU', key = 'LltHybridDGPU', tip = 'Discrete only (MUX) - needs a reboot, click twice' },
               { id = 'OFF', tip = 'Hide / show every HUD module (the console stays)' } }
local TIERS = { [-1] = 'AUTO', [0] = 'FULL', [1] = 'LITE', [2] = 'LOW', [3] = 'STEALTH' }

local function split(s, sep)
  local t = {}
  for p in string.gmatch((s or '') .. sep, '(.-)' .. sep) do t[#t + 1] = (string.gsub(p, '^%s*(.-)%s*$', '%1')) end
  return t
end

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  Z = dofile(SKIN:GetVariable('@') .. 'Data\\zones.lua')
  H.init()
end

local function say(t) msg, msgAt = t, os.time() end

local function runLlt(feature, value)
  local p = string.format('-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%sScripts\\llt.ps1" -Exe "%s" -Feature "%s" -Value "%s"',
    SKIN:GetVariable('@'), H.str('LltPath', ''), feature, value)
  SKIN:Bang('!SetOption', 'mLlt', 'Parameter', p)
  SKIN:Bang('!UpdateMeasure', 'mLlt')
  SKIN:Bang('!CommandMeasure', 'mLlt', 'Run')
  say('SET ' .. string.upper(feature) .. ' > ' .. string.upper(value))
end

function OnLltDone()
  local out = H.sval('mLlt', '')
  if string.find(out, 'result=ok') then say('DONE') else say('SWITCH FAILED') end
  SKIN:Bang('!CommandMeasure', 'mStatus', 'Run')
end

function OnStatus()
  local out = H.sval('mStatus', '')
  local path
  for k, v in string.gmatch(out, '(%w+)=([^\r\n]*)') do
    if k == 'lltpath' then path = v else st[k] = string.lower(v) end
  end
  -- share the state with the settings dial and the info screen (they can't read this script's variables)
  local f = io.open(SKIN:GetVariable('@') .. 'Data\\llt_state.txt', 'w')
  if f then
    f:write('T ' .. os.time() .. '\n')
    for _, k in ipairs({ 'hybrid', 'power', 'refresh', 'battery', 'llt' }) do f:write(k .. ' ' .. (st[k] or '') .. '\n') end
    f:close()
  end
  -- status.ps1 found Legion Toolkit somewhere other than LltPath: remember where, so switching works too
  if path and path ~= '' and string.lower(path) ~= string.lower(H.str('LltPath', '')) then
    H.save('LltPath', path)
    SKIN:Bang('!SetOption', 'mStatus', 'Parameter', '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' .. SKIN:GetVariable('@') ..
      'Scripts\\status.ps1" -Exe "' .. path .. '" -Hybrid "' .. H.str('LltHybridFeature', 'hybrid-mode') .. '" -Power "' .. H.str('LltPowerFeature', 'power-mode') ..
      '" -Refresh "' .. H.str('LltRefreshFeature', 'refresh-rate') .. '" -Battery "' .. H.str('LltBatteryFeature', 'battery') .. '"')
  end
end

local function hybridIndex()
  if st.hybrid == '' then return nil end
  for i = 1, 4 do
    if string.lower(H.str(TABS[i].key, '#')) == st.hybrid then return i end
  end
  return nil
end

local function buttons()
  local tierOv = H.num('PerfOverride', -1)
  local modes = split(H.str('LltPowerModes', 'quiet,balance,performance'), ',')
  local rates = split(H.str('LltRefreshRates', '60,165'), ',')
  local PM = { quiet = 'QUIET', balance = 'BAL', balanced = 'BAL', performance = 'PERF', custom = 'CUST', extreme = 'MAX' }
  local pw = st.power ~= '' and (PM[st.power] or string.upper(string.sub(st.power, 1, 5))) or '--'
  local hz = st.refresh ~= '' and (string.match(st.refresh, '%d+') or st.refresh) .. 'HZ' or '--HZ'
  local cons = st.battery ~= '' and (string.find(st.battery, string.lower(H.str('LltBatteryConserve', 'conservation')), 1, true) and 'ON' or 'OFF') or '--'
  return {
    { label = pw, tip = 'Power mode - click to cycle ' .. table.concat(modes, ' / ') },
    { label = hz, tip = 'Refresh rate - click to toggle ' .. table.concat(rates, ' / ') .. ' Hz' },
    { label = H.num('ChargeLimit', 80) .. '%', on = cons == 'ON', tip = 'Battery conservation (hold at ' .. H.num('ChargeLimit', 80) .. '%)' },
    { label = (tierOv < 0 and string.sub(TIERS[H.num('PerfTier', 0)] or 'FULL', 1, 4) or string.sub(TIERS[tierOv], 1, 4)),
      tip = 'Graphics tier: ' .. (TIERS[tierOv] or 'AUTO') .. ' (now ' .. (TIERS[H.num('PerfTier', 0)] or '?') .. ') - click to cycle' },
    { label = 'dGPU', light = st.dgpu, tip = 'RTX 5070: ' .. (st.dgpu == 'on' and 'present / powered' or (st.dgpu == 'off' and 'off (ECO mode)' or 'unknown')) .. ' - click to refresh' },
    { label = 'CARGO', tip = 'All apps (drop-down drawer)' },
    { label = 'MASTER', on = tierOv == 3, tip = 'Kill switch: drop the whole HUD to STEALTH / restore' },
    { label = 'CFG', tip = 'Control Center: modules, layout, theme, apps, sensors, presets' },
  }
end

-- reference positions (ref pixels inside the console zone 463..797 x 10..57, centred on the axis x = 630)
local SXR, SYR = 2560 / 1260, 1600 / 709
local function RX(x) return (x - 463) * SXR end
local function RY(y) return (y - 10) * SYR end
local TABX = { 549, 591, 630, 669, 711 }
local BOX = { { 538, 559 }, { 569, 589 } }
local TXT = { { 671, 51 }, { 695, 50 }, { 719, 49 }, { 743, 48 }, { 767, 47 } }

function Update()
  H.refreshTier()
  tick = tick + 1
  if tick == 2 or tick % 60 == 0 then SKIN:Bang('!CommandMeasure', 'mStatus', 'Run') end
  if armed and os.time() - armedAt > 5 then armed = nil end
  local z = H.zones[1]
  local c = H.canvas(1)
  local W, D = H.C.white, H.C.dim
  -- tab row (reference: COMBAT STARMAP MINING GROUND OFF)
  local active = hybridIndex()
  if hudHidden then active = 5 end
  for i, t in ipairs(TABS) do
    local x, y = RX(TABX[i]), RY(23)
    local on = i == active
    local label = armed == i and 'CONFIRM?' or t.id
    H.text(1, i, x, y, label, { size = 6.4, weight = 700, align = 'CenterCenter',
      color = armed == i and H.C.warn or (on and W or { 150, 170, 185 }), alpha = on and 255 or 200 })
    if on then c:hair(x - 22, y + 9, x + 22, y + 9, H.C.accent, 1.2, 160) end
    if t.id == 'dGPU' and st.dgpu ~= '' then c:dot(x + 26, y, 2.6, st.dgpu == 'on' and H.C.good or D) end
    H.hit(1, i, x - 34, y - 12, 68, 24, t.tip)
  end
  -- reference RADR IFCS pair -> CARGO, CFG
  local boxes = { { 'CARGO', 11, 'All apps (drop-down drawer)' }, { 'CFG', 13, 'Control Center' } }
  for i, b in ipairs(boxes) do
    local x0, x1 = RX(BOX[i][1]), RX(BOX[i][2])
    local y0, y1 = RY(46), RY(55)
    -- plain glowing labels with a short underline (no boxes)
    H.text(1, 5 + i, (x0 + x1) / 2, (y0 + y1) / 2, b[1], { size = 5.6, weight = 700, align = 'CenterCenter', color = H.C.accent })
    c:hair((x0 + x1) / 2 - (x1 - x0) * 0.32, y1 + 2, (x0 + x1) / 2 + (x1 - x0) * 0.32, y1 + 2, H.C.accent, 1.2, 150)
    H.hit(1, 5 + i, x0, y0, x1 - x0, y1 - y0, b[3])
  end
  -- text group (reference: MISL HEAT CLSN FUEL GFRC, FUEL lit) -> quick settings
  local bs = buttons()
  local items = { { bs[1], 6 }, { bs[2], 7 }, { bs[3], 8 }, { bs[4], 9 }, { bs[7], 12 } }
  for i, it in ipairs(items) do
    local b, k = it[1], it[2]
    local x, y = RX(TXT[i][1]), RY(TXT[i][2])
    local lit = b.on
    H.text(1, 7 + i, x, y, b.label, { size = 5.6, weight = 700, clip = 64, align = 'CenterCenter', color = lit and H.C.hi or { 160, 180, 195 } })
    H.hit(1, 7 + i, x - 24, y - 10, 48, 20, b.tip)
  end
  -- transient message between the two groups
  if os.time() - msgAt < 6 and msg ~= '' then
    H.text(1, 14, RX(630), RY(49), msg, { size = 6.5, weight = 700, align = 'CenterCenter', color = H.C.warn, clip = 150 })
  else H.hideText(1, 14) end
  H.hit(1, 14, RX(612), RY(50), RX(648) - RX(612), RY(58) - RY(50), 'dGPU: ' .. (st.dgpu ~= '' and st.dgpu or 'unknown') .. ' - click to refresh status')
  c:flush()
  return 0
end

local function toggleHud()
  hudHidden = not hudHidden
  for _, m in ipairs(Z.modules) do
    if m.key ~= 'TopConsole' then
      SKIN:Bang(hudHidden and '!HideFade' or '!ShowFade', m.config)
    end
  end
end

local function cycle(listVar, current, default)
  local list = split(H.str(listVar, default), ',')
  for i, v in ipairs(list) do
    if string.lower(v) == current or string.find(current, string.lower(v), 1, true) then return list[i % #list + 1] end
  end
  return list[1]
end

local HITMAP = { [6] = 11, [7] = 13, [8] = 6, [9] = 7, [10] = 8, [11] = 9, [12] = 12, [14] = 10 }

function OnClick(zi, k)
  if k > 5 then k = HITMAP[k] or k end
  if k <= 4 then
    if k == 4 and armed ~= 4 then armed, armedAt = 4, os.time(); say('dGPU MODE NEEDS A REBOOT - CLICK AGAIN'); return end
    armed = nil
    runLlt(H.str('LltHybridFeature', 'hybrid-mode'), H.str(TABS[k].key, ''))
  elseif k == 5 then
    toggleHud()
  elseif k == 6 then
    runLlt(H.str('LltPowerFeature', 'power-mode'), cycle('LltPowerModes', st.power, 'quiet,balance,performance'))
  elseif k == 7 then
    runLlt(H.str('LltRefreshFeature', 'refresh-rate'), cycle('LltRefreshRates', string.match(st.refresh, '%d+') or '', '60,165'))
  elseif k == 8 then
    local on = string.find(st.battery, string.lower(H.str('LltBatteryConserve', 'conservation')), 1, true)
    runLlt(H.str('LltBatteryFeature', 'battery'), on and H.str('LltBatteryNormal', 'normal') or H.str('LltBatteryConserve', 'conservation'))
  elseif k == 9 then
    local ov = H.num('PerfOverride', -1) + 1
    if ov > 3 then ov = -1 end
    H.save('PerfOverride', ov)
    SKIN:Bang('!CommandMeasure', 'mScript', 'SetOverride(' .. ov .. ')', 'Spaceship\\Controller')
  elseif k == 10 then
    SKIN:Bang('!CommandMeasure', 'mStatus', 'Run'); say('REFRESHING STATUS')
  elseif k == 11 then
    SKIN:Bang('!ToggleConfig', 'Spaceship\\Overlay\\Drawer', 'Drawer.ini')
  elseif k == 12 then
    SKIN:Bang('!CommandMeasure', 'mScript', 'Master()', 'Spaceship\\Controller')
  elseif k == 13 then
    SKIN:Bang('!ToggleConfig', 'Spaceship\\Overlay\\Control', 'Control.ini')
  end
  Update()
end

function OnRightClick(zi, k)
  if k <= 5 then SKIN:Bang('!CommandMeasure', 'mStatus', 'Run') end
end
function OnScroll(zi, k, d) end
function OnHover(zi, k, on) end
