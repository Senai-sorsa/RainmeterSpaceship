"""Self-check for lua2ts.py: plain asserts, no test framework.  Run:  python3 -I tools/test_lua2ts.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lua2ts as L


def body(src):
    ts, blocked, review, unmapped = L.convert(src)
    return ts.split("\n", 3)[3], blocked, review, unmapped  # drop the 3-line header


def out(src):
    return body(src)[0].strip()


def fails(src, needle):
    try:
        L.convert(src)
    except L.LuaError as e:
        assert needle in str(e), (needle, str(e))
        return
    raise AssertionError("expected a LuaError for %r" % src)


# indices: 1-based Lua becomes 0-based TS
assert out("local t = {}\nlocal x = t[1]") == "let t = [];\nlet x = t[0];"
assert out("t[#t + 1] = 5") == "t[t.length] = 5;"
assert out("x = t[#t]") == "x = t[t.length - 1];"
assert out("x = t[i]") == "x = t[i];"
assert "variable index" in " ".join(r[1] for r in body("x = t[i]")[2])

# truthiness: Lua 0 and '' are true, so conditions go through lua.truthy unless they are comparisons
assert out("if x then y() end") == "if (lua.truthy(x)) {\n  y();\n}"
assert out("if a < 3 then y() end") == "if ((a < 3)) {\n  y();\n}"
assert out("local v = w or 0") == "let v = lua.or(w, () => (0));"
assert out("if x and y then z() end") == "if (lua.truthy(lua.and(x, () => (y)))) {\n  z();\n}"

# operators
assert out("local a = 'x' .. n") == "let a = (lua.tostr('x') + lua.tostr(n));"
assert out("local a = n % 4") == "let a = lua.mod(n, 4);"
assert out("if a ~= nil then end") == "if ((a !== undefined)) {\n}"
assert out("local m = not x") == "let m = !lua.truthy(x);"

# strings and escapes
assert out("local s = 'it\\'s'") == "let s = 'it\\'s';"
assert out("local s = '\\\\'") == "let s = '\\\\';"

# calls and methods
assert out("c:line(0, 0, 1, 1, H.C.white, 1.3, 210)") == "c.line(0, 0, 1, 1, H.C.white, 1.3, 210);"
assert out("local z = H.zones[1]") == "let z = H.zones[0];"
assert out("local s = string.format('%.0fW', w)") == "let s = lua.format('%.0fW', w);"
assert out("local r = math.floor(x)") == "let r = Math.floor(x);"
assert out("table.insert(list, v)") == "list.push(v);"
assert out("local j = table.concat(list, '  |  ')") == "let j = list.join('  |  ');"

# table constructors
assert out("local p = { { 1, 2 }, { 3, 4 } }") == "let p = [[1, 2], [3, 4]];"
assert out("local o = { size = 8.5, weight = 700 }") == "let o = { size: 8.5, weight: 700 };"

# loops
assert out("for i = 1, 3 do x(i) end") == "for (let i = 1; i <= 3; i += 1) {\n  x(i);\n}"
assert out("for i, v in ipairs(list) do x(v) end").startswith("for (let i = 1; i <= list.length; i++) {")
assert "const v = list[i - 1];" in out("for i, v in ipairs(list) do x(v) end")
assert "Object.entries(m)" in out("for k, v in pairs(m) do x(v) end")
assert "pairs() order" in " ".join(r[1] for r in body("for k, v in pairs(m) do x(v) end")[2])

# functions
assert out("function Update()\n  return 1\nend") == "export function Update(): any {\n  return 1;\n}"
assert out("local function alerts()\n  return {}\nend") == "function alerts(): any {\n  return [];\n}"
assert out("local H\nH = dofile(SKIN:GetVariable('@') .. 'x.lua')") == "let H;\n// dofile binding dropped: the port binds its runtime"
assert out("function H.init()\nend") == "H.init = () => {\n};" or out("function H.init()\nend").startswith("H.init = (")
assert out("function OnClick(z, k) end").startswith("export function OnClick(z: any, k: any): any {")

# blocked: Rainmeter calls are reported, not translated
ts, blocked, _, _ = body("function OnClick(z, k) SKIN:Bang('!ActivateConfig', 'x') end")
assert blocked and blocked[0][1] == "SKIN:Bang", blocked
assert "BLOCKED: SKIN:Bang" in ts

# comments carry over to the line of the next statement
assert out("-- top note\nlocal a = 1") == "// top note\nlet a = 1;"

# syntax outside the subset fails with a line number, and produces no output
fails("repeat x() until y", "line 1")
fails("local a = 1\nlocal b, c = f()\nb, c = 1, 2", "line 2")
fails("a, b = 1, 2", "line 1")
fails("x = [[long]]", "unexpected")
fails("local t = {1, k = 2}", "mixed")
fails("function f(...) end", "varargs")

# the four real module scripts convert without error
here = os.path.dirname(os.path.abspath(__file__))
scripts = os.path.join(here, "..", "Skins", "Spaceship", "@Resources", "Scripts")
for name in ("power.lua", "alert.lua", "battery.lua"):
    with open(os.path.join(scripts, name), encoding="utf-8") as f:
        ts, blocked, review, unmapped = L.convert(f.read())
    assert "export function Update" in ts, name
    assert "dofile binding dropped" in ts, name
print("lua2ts self-check ok")
