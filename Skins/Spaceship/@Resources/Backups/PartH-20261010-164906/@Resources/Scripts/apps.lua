-- App catalog: parses Apps.ini, resolves targets against the Start-menu scan, launches apps.
-- Usage:  A = dofile(SKIN:GetVariable('@') .. 'Scripts\\apps.lua'); A.load()
local A = {}
local RES = SKIN:GetVariable('@')

local function trim(s) return (string.gsub(s or '', '^%s*(.-)%s*$', '%1')) end
local function lower(s) return string.lower(s or '') end

local function readLines(path)
  local ok, f = pcall(io.open, path, 'r')
  if not ok or not f then return nil end
  local lines = {}
  for line in f:lines() do lines[#lines + 1] = line end
  f:close()
  if lines[1] then lines[1] = string.gsub(lines[1], '^\239\187\191', '') end -- strip UTF-8 BOM
  return lines
end
A.readLines = readLines

function A.parseIni(path)
  local data, order, sec = {}, {}, nil
  for _, raw in ipairs(readLines(path) or {}) do
    local line = trim(raw)
    if line ~= '' and string.sub(line, 1, 1) ~= ';' then
      local s = string.match(line, '^%[(.+)%]$')
      if s then
        sec = s
        data[sec] = data[sec] or {}
        order[#order + 1] = sec
      elseif sec then
        local k, v = string.match(line, '^([^=]+)=(.*)$')
        if k then data[sec][trim(k)] = trim(v) end
      end
    end
  end
  return data, order
end

local function exists(path)
  local ok, f = pcall(io.open, path, 'rb')
  if ok and f then f:close(); return true end
  return false
end

local function expandEnv(s)
  return (string.gsub(s, '%%([%w_]+)%%', function(v)
    local ok, val = pcall(os.getenv, v)
    return (ok and val) or ('%' .. v .. '%')
  end))
end

-- Start menu scan written by Scripts\scan-apps.ps1:  Name|AppID per line
function A.loadStart()
  A.start = {}
  for _, line in ipairs(readLines(RES .. 'Data\\StartApps.txt') or {}) do
    local name, id = string.match(line, '^(.-)|(.+)$')
    if name and id then A.start[#A.start + 1] = { name = name, lname = lower(name), id = trim(id) } end
  end
  A.startCount = #A.start
end

local function findStart(q)
  q = lower(q)
  local best, bestLen
  for _, e in ipairs(A.start) do if e.lname == q then return e end end
  for pass = 1, 2 do
    for _, e in ipairs(A.start) do
      local hit = (pass == 1 and string.sub(e.lname, 1, #q) == q) or (pass == 2 and string.find(e.lname, q, 1, true))
      if hit and (not bestLen or #e.name < bestLen) then best, bestLen = e, #e.name end
    end
    if best then return best end
  end
  return nil
end

-- returns { kind='start'|'file'|'cmd', value=..., label=... } or nil
function A.resolve(targets)
  for part in string.gmatch((targets or '') .. '||', '(.-)||') do
    local t = trim(part)
    if t ~= '' then
      if string.sub(t, 1, 6) == 'start:' then
        local e = findStart(trim(string.sub(t, 7)))
        if e then return { kind = 'start', value = e.id, label = e.name } end
      elseif string.sub(t, 1, 4) == 'cmd:' then
        return { kind = 'cmd', value = trim(string.sub(t, 5)) }
      else
        local p = expandEnv(t)
        if exists(p) then return { kind = 'file', value = p } end
      end
    end
  end
  return nil
end

function A.load()
  A.loadStart()
  local data = A.parseIni(RES .. 'Apps.ini')
  A.layout = data['Layout'] or {}
  A.hideMissing = (A.layout.HideMissing or '1') ~= '0'
  A.apps, A.cats, A.catOrder = {}, {}, {}
  for sec, kv in pairs(data) do
    local id = string.match(sec, '^App%.(.+)$')
    if id then
      local r = A.resolve(kv.Target)
      A.apps[id] = {
        id = id, name = kv.Name or id, short = string.upper(kv.Short or kv.Name or id),
        icon = kv.Icon or 'gear', info = kv.Info or '', proc = kv.Proc or '',
        target = r, missing = (r == nil),
      }
    end
  end
  local _, order = A.parseIni(RES .. 'Apps.ini')
  for _, sec in ipairs(order) do
    local id = string.match(sec, '^Category%.(.+)$')
    if id then
      local kv = data[sec]
      local list = {}
      for a in string.gmatch((kv.Apps or '') .. ',', '%s*([^,]-)%s*,') do
        local app = A.apps[a]
        if app and not (A.hideMissing and app.missing) then list[#list + 1] = app end
      end
      A.cats[id] = { id = id, name = kv.Name or id, short = string.upper(kv.Short or kv.Name or id), icon = kv.Icon or 'box', apps = list }
      A.catOrder[#A.catOrder + 1] = id
    end
  end
  A.loadAll()
end

-- Start-menu entries that are not apps
local JUNK = { 'uninstall', 'readme', 'read me', 'help', 'documentation', 'website', 'release notes', 'license',
  'manual', 'changelog', "what's new", 'support', 'faq', 'troubleshoot', 'repair' }

-- a line icon guessed from the name, for apps that are not in the catalog
local GUESS = { { 'code', 'code' }, { 'terminal', 'terminal' }, { 'shell', 'terminal' }, { 'python', 'code' },
  { 'java', 'code' }, { 'git', 'git' }, { 'docker', 'box' }, { 'camera', 'camera' }, { 'photo', 'camera' },
  { 'video', 'film' }, { 'player', 'film' }, { 'music', 'music' }, { 'audio', 'music' }, { 'sound', 'music' },
  { 'mail', 'mail' }, { 'calendar', 'note' }, { 'note', 'note' }, { 'word', 'pen' }, { 'excel', 'matrix' },
  { 'powerpoint', 'window' }, { 'pdf', 'pdf' }, { 'zip', 'archive' }, { 'drive', 'cloud' }, { 'cloud', 'cloud' },
  { 'game', 'game' }, { 'steam', 'game' }, { 'xbox', 'game' }, { 'chat', 'chat' }, { 'team', 'chat' },
  { 'monitor', 'gauge' }, { 'disk', 'disk' }, { 'usb', 'usb' }, { 'nvidia', 'gpu' }, { 'amd', 'gpu' },
  { 'lenovo', 'gear' }, { 'settings', 'gear' }, { 'paint', 'palette' }, { 'map', 'map' }, { 'browser', 'globe' },
  { 'edge', 'globe' }, { 'firefox', 'globe' }, { 'store', 'box' }, { 'clock', 'gauge' }, { 'calculator', 'matrix' } }

local function guessIcon(lname)
  for _, g in ipairs(GUESS) do if string.find(lname, g[1], 1, true) then return g[2] end end
  return 'window'
end

-- every installed app (the Start-menu scan) joins the catalog: catalog apps keep their folders, the rest go to
-- OTHER APPS, and ALL INSTALLED APPS lists them all A-Z
function A.loadAll()
  local claimed, used = {}, {}
  for _, app in pairs(A.apps) do
    if app.target and app.target.kind == 'start' then claimed[app.target.value] = app end
  end
  local all, other = {}, {}
  for _, e in ipairs(A.start or {}) do
    local junk = false
    for _, j in ipairs(JUNK) do if string.find(e.lname, j, 1, true) then junk = true; break end end
    if not junk and not used[e.id] then
      used[e.id] = true
      local app = claimed[e.id]
      if not app then
        local base = 's_' .. string.sub(string.gsub(e.lname, '[^%w]', ''), 1, 40)
        local sid, n = base, 2
        while A.apps[sid] do sid = base .. n; n = n + 1 end
        local short = string.upper(string.match(e.name, '^(%S+)') or e.name)
        app = { id = sid, name = e.name, short = string.sub(short, 1, 10), icon = guessIcon(e.lname), info = '',
          proc = '', target = { kind = 'start', value = e.id, label = e.name }, missing = false, auto = true }
        A.apps[sid] = app
        other[#other + 1] = app
      end
      all[#all + 1] = app
    end
  end
  -- catalog apps found by their file path (not in the Start menu) are installed too
  for _, app in pairs(A.apps) do
    if app.target and app.target.kind ~= 'start' and app.target.kind ~= 'cmd' then all[#all + 1] = app end
  end
  local function byName(a, b) return lower(a.name) < lower(b.name) end
  table.sort(all, byName); table.sort(other, byName)
  A.cats.all = { id = 'all', name = 'ALL INSTALLED APPS', short = 'ALL', icon = 'search', apps = all }
  if #other > 0 then
    A.cats.other = { id = 'other', name = 'OTHER APPS', short = 'OTHER', icon = 'box', apps = other }
    A.catOrder[#A.catOrder + 1] = 'other'
  end
end

-- what a slot shows: { kind='app', app=... } or { kind='cat', cat=... }
function A.entry(id)
  if A.cats[id] then return { kind = 'cat', cat = A.cats[id] } end
  if A.apps[id] then return { kind = 'app', app = A.apps[id] } end
  return nil
end

-- an app that is not installed, or was uninstalled / moved since the last Start-menu scan: nothing is launched,
-- the reason goes to the Rainmeter log, and the Controller rescans (at most once a minute) so a program you just
-- installed is picked up without a manual refresh
local lastRescan = 0
function A.notFound(app)
  print('Spaceship: ' .. tostring(app and app.name or 'app') .. ' was not found (not installed, or moved). '
    .. 'Install it, or point its Target= in Apps.ini at the right path. Rescanning the Start menu.')
  if os.time() - lastRescan >= 60 then
    lastRescan = os.time()
    SKIN:Bang('!CommandMeasure', 'mScript', 'Rescan()', 'Spaceship\\Controller')
  end
end

-- is this exe running right now? (ShipCore's windows.txt, refreshed every ~1.5 s)
local function running(proc)
  local f = io.open(RES .. 'Data\\windows.txt', 'r')
  if not f then return false end
  local want, hit = string.lower(proc), false
  for line in f:lines() do
    local v = string.match(line, '^[WP] (.+)$')
    if v and string.lower(v) == want then hit = true; break end
  end
  f:close()
  return hit
end

function A.launch(app)
  if not app then return false end
  local t = app.target
  if not t or (t.kind == 'file' and not exists(t.value)) then
    app.missing = true
    A.notFound(app)
    return false
  end
  local target = t.kind == 'start' and ('shell:AppsFolder\\' .. t.value) or t.value
  -- already open? ShipCore brings its window to the front (restoring it if minimised) instead of launching a
  -- second copy, which most programs just ignore; with no window it launches the app as usual
  local core = RES .. 'Bin\\ShipCore.exe'
  local proc = (app.proc and app.proc ~= '') and app.proc or (t.kind == 'file' and string.match(t.value, '([^\\/]+%.[eE][xX][eE])$')) or nil
  if proc and t.kind ~= 'cmd' and exists(core) and running(proc) then
    SKIN:Bang('["' .. core .. '" focus "' .. proc .. '" "' .. target .. '"]')
  elseif t.kind == 'start' then
    SKIN:Bang('["explorer.exe" "' .. target .. '"]')
  else
    SKIN:Bang('["' .. t.value .. '"]')
  end
  return true
end

-- icon extraction queue for Scripts\app-icons.ps1: "id|path" (path = file, or shell:AppsFolder\AppID)
function A.writeIconQueue()
  local f = io.open(RES .. 'Data\\IconQueue.txt', 'w')
  if not f then return 0 end
  local n = 0
  for id, app in pairs(A.apps) do
    local t = app.target
    if t and t.kind == 'start' then f:write(id .. '|shell:AppsFolder\\' .. t.value .. '\n'); n = n + 1
    elseif t and t.kind == 'file' then f:write(id .. '|' .. t.value .. '\n'); n = n + 1 end
  end
  f:close()
  return n
end

-- persistent per-panel selection (State.inc)
function A.getState(key, default)
  local v = SKIN:GetVariable(key, '')
  if v == nil or v == '' then return default end
  return v
end

function A.setState(key, value)
  SKIN:Bang('!SetVariable', key, value)
  SKIN:Bang('!WriteKeyValue', 'Variables', key, value, RES .. 'State.inc')
end

return A
