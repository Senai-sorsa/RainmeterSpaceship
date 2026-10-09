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

function A.launch(app)
  if not app then return false end
  local t = app.target
  if not t or (t.kind == 'file' and not exists(t.value)) then
    app.missing = true
    A.notFound(app)
    return false
  end
  if t.kind == 'start' then
    SKIN:Bang('["explorer.exe" "shell:AppsFolder\\' .. t.value .. '"]')
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
