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
  if string.find(out, 'result=ok') then say('DONE') else say('LLT: CHECK CLI (see Data\\llt.log)') end
  SKIN:Bang('!CommandMeasure', 'mStatus', 'Run')
end

function OnStatus()
  local out = H.sval('mStatus', '')
  for k, v in string.gmatch(out, '(%w+)=([^\r\n]*)') do st[k] = string.lower(v) end
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
    { label = 'PWR ' .. pw, tip = 'Power mode - click to cycle ' .. table.concat(modes, ' / ') },
    { label = hz, tip = 'Refresh rate - click to toggle ' .. table.concat(rates, ' / ') .. ' Hz' },
    { label = H.num('ChargeLimit', 80) .. '% ' .. cons, tip = 'Battery conservation (hold at ' .. H.num('ChargeLimit', 80) .. '%)' },
    { label = 'TIER ' .. (tierOv < 0 and ('A-' .. string.sub(TIERS[H.num('PerfTier', 0)] or 'FULL', 1, 1)) or string.sub(TIERS[tierOv], 1, 4)),
      tip = 'Graphics tier: ' .. (TIERS[tierOv] or 'AUTO') .. ' (now ' .. (TIERS[H.num('PerfTier', 0)] or '?') .. ') - click to cycle' },
    { label = 'dGPU', light = st.dgpu, tip = 'RTX 5070: ' .. (st.dgpu == 'on' and 'present / powered' or (st.dgpu == 'off' and 'off (ECO mode)' or 'unknown')) .. ' - click to refresh' },
    { label = 'CARGO', tip = 'All apps (drop-down drawer)' },
    { label = 'MASTER', on = tierOv == 3, tip = 'Kill switch: drop the whole HUD to STEALTH / restore' },
    { label = 'CFG', tip = 'Control Center: modules, layout, theme, apps, sensors, presets' },
  }
end

function Update()
  H.refreshTier()
  tick = tick + 1
  if tick == 2 or tick % 60 == 0 then SKIN:Bang('!CommandMeasure', 'mStatus', 'Run') end
  if armed and os.time() - armedAt > 5 then armed = nil end
  local z = H.zones[1]
  local c = H.canvas(1)
  local A, D = H.C.accent, H.C.dim
  -- row 1: angled tab strip
  local active = hybridIndex()
  if hudHidden then active = 5 end
  local tw = z.w / 5
  c:line(0, 30, z.w, 30, D, 1.2, 200)
  for i, t in ipairs(TABS) do
    local x = (i - 1) * tw
    local on = (i == active)
    local col = on and A or D
    if on then
      c:fillPoly({ { x + 8, 2 }, { x + tw - 8, 2 }, { x + tw, 30 }, { x, 30 } }, A, 40)
      c:poly({ { x, 30 }, { x + 8, 2 }, { x + tw - 8, 2 }, { x + tw, 30 } }, A, 1.6)
    end
    if armed == i then c:poly({ { x, 30 }, { x + 8, 2 }, { x + tw - 8, 2 }, { x + tw, 30 } }, H.C.warn, 1.8) end
    H.text(1, i, x + tw / 2, 16, armed == i and 'CONFIRM?' or t.id, { size = 10.5, align = 'CenterCenter', font = H.fontTitle, weight = 700,
      color = armed == i and H.C.warn or (on and H.C.text or col) })
    H.hit(1, i, x, 0, tw, 32, t.tip)
  end
  -- row 2: boxed quick buttons (reference: RADR / IFCS / MISL HEAT CLSN FUEL)
  local bs = buttons()
  local bw, gap = 66, (z.w - 66 * 8) / 7
  for i, b in ipairs(bs) do
    local x = (i - 1) * (bw + gap)
    local col = b.on and H.C.alert or A
    c:fillRect(x, 44, bw, 26, H.C.panel, b.on and 160 or 110)
    c:rect(x, 44, bw, 26, b.on and H.C.alert or D, 1.2)
    if b.light ~= nil then
      local lc = b.light == 'on' and H.C.good or (b.light == 'off' and D or H.C.warn)
      c:dot(x + 10, 57, 4, lc)
      H.text(1, 5 + i, x + bw / 2 + 6, 57, b.label, { size = 9, align = 'CenterCenter', color = col, font = H.fontText, weight = 700 })
    else
      H.text(1, 5 + i, x + bw / 2, 57, b.label, { size = 9, align = 'CenterCenter', color = col, font = H.fontText, weight = 700 })
    end
    H.hit(1, 5 + i, x, 44, bw, 26, b.tip)
  end
  -- status line
  local llt = st.llt == 'missing' and 'LLT CLI NOT FOUND - SET LltPath / ENABLE CLI' or (st.llt == 'found' and 'LEGION TOOLKIT LINKED' or 'READING STATUS...')
  local line = (os.time() - msgAt < 8 and msg ~= '') and msg or llt
  H.text(1, 14, z.w / 2, 88, line, { size = 8.5, align = 'CenterCenter', color = st.llt == 'missing' and H.C.warn or D })
  c:hair(0, 80, 120, 80, D, 1, 120)
  c:hair(z.w - 120, 80, z.w, 80, D, 1, 120)
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

function OnClick(zi, k)
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
