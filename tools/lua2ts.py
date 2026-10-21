"""Lua module script -> TypeScript draft, for the standalone port. Run:  python3 -I tools/lua2ts.py <file.lua> [out.ts]

What it does (the subset the skin's module scripts use):
  - Lua 1-based numeric indices become 0-based TS indices (t[1] -> t[0], t[#t + 1] -> t[t.length]).
    Variable indices are kept as written and reported for review: a Lua loop variable is 1-based too.
  - Truthiness follows Lua: only nil and false are false, so 0 and '' are true (lua.truthy).
  - Rainmeter calls (SKIN:...) are not translated. Each is listed as BLOCKED and left as a comment,
    because each one must become a named action behind the action gate, by hand.
  - dofile(...) bindings are dropped; the port binds its runtime itself.
  - Anything outside the subset is a syntax error with a line number. No partial output.

The output is a draft: it imports ./luaRuntime (lua.*) and expects the module's H and c objects.
A person reviews every REVIEW line and every BLOCKED line before the file is used.
"""
import re
import sys

KEYWORDS = {"and", "break", "do", "else", "elseif", "end", "false", "for", "function", "if", "in", "local", "nil", "not",
            "or", "repeat", "return", "then", "true", "until", "while"}
TS_RESERVED = {"default", "delete", "new", "class", "var", "this", "in", "void", "with", "yield", "let", "const", "switch", "case", "throw", "try", "catch", "finally", "typeof", "instanceof", "export", "import", "extends", "super", "debugger", "enum", "null", "undefined"}
# Lua globals and library calls -> TS. A null entry is a call that needs a hand port.
CALLS = {
    "tostring": "lua.tostr", "tonumber": "lua.tonum", "string.format": "lua.format", "string.sub": "lua.sub",
    "string.match": "lua.match", "string.len": "lua.len", "string.rep": "lua.rep", "string.upper": "lua.upper", "string.lower": "lua.lower",
    "math.floor": "Math.floor", "math.ceil": "Math.ceil", "math.abs": "Math.abs", "math.max": "Math.max", "math.min": "Math.min",
    "math.sqrt": "Math.sqrt", "math.sin": "Math.sin", "math.cos": "Math.cos", "math.atan": "Math.atan", "math.atan2": "Math.atan2",
    "math.random": "Math.random", "os.time": "lua.now", "unpack": "lua.unpack", "type": "lua.type", "select": None,
    "table.concat": None, "table.insert": None, "table.remove": None, "pairs": None, "ipairs": None, "setmetatable": None, "dofile": None,
}
CONSTS = {"math.pi": "Math.PI", "math.huge": "Infinity"}
LIBRARIES = {"string", "math", "table", "os", "io", "coroutine", "debug"}
BINARY = {  # op: (left priority, right priority, TS operator)
    "or": (1, 1, "||"), "and": (2, 2, "&&"),
    "<": (3, 3, "<"), ">": (3, 3, ">"), "<=": (3, 3, "<="), ">=": (3, 3, ">="), "~=": (3, 3, "!=="), "==": (3, 3, "==="),
    "..": (9, 8, "+"), "+": (10, 10, "+"), "-": (10, 10, "-"), "*": (11, 11, "*"), "/": (11, 11, "/"), "%": (11, 11, "%"),
    "^": (14, 13, "**"),
}
UNARY_PRIO = 12
TOKEN = re.compile(r"(?P<ws>\s+)|(?P<comment>--[^\n]*)|(?P<str>'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\")"
                   r"|(?P<num>\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|\.\d+)|(?P<name>[A-Za-z_]\w*)|(?P<op>\.\.\.|\.\.|==|~=|<=|>=|//|::|[-+*/%^#<>=(){}\[\];:,.])")
ESC = {"n": "\n", "t": "\t", "\\": "\\", "'": "'", '"': '"', "r": "\r", "0": "\0"}


class LuaError(Exception):
    pass


def tokenize(src):
    """Tokens are (kind, value, line). Comments are kept as their own kind so the emitter can carry them over."""
    toks, pos, line = [], 0, 1
    while pos < len(src):
        m = TOKEN.match(src, pos)
        if not m:
            raise LuaError("line %d: unexpected character %r" % (line, src[pos]))
        kind, text = m.lastgroup, m.group()
        pos = m.end()
        if kind == "ws":
            pass
        elif kind == "comment":
            toks.append(("comment", text[2:].strip(), line))
        elif kind == "str":
            toks.append(("str", unescape(text[1:-1], line), line))
        elif kind == "name":
            toks.append(("kw" if text in KEYWORDS else "name", text, line))
        else:
            toks.append((kind, text, line))
        line += text.count("\n")
    toks.append(("eof", "", line))
    return toks


def unescape(s, line):
    out, i = [], 0
    while i < len(s):
        if s[i] == "\\":
            nxt = s[i + 1]
            if nxt not in ESC:
                raise LuaError("line %d: unsupported escape \\%s" % (line, nxt))
            out.append(ESC[nxt])
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


class Parser:
    def __init__(self, toks):
        self.toks = [t for t in toks if t[0] != "comment"]
        self.comments = [(t[2], t[1]) for t in toks if t[0] == "comment"]
        self.i = 0

    def peek(self, n=0):
        return self.toks[min(self.i + n, len(self.toks) - 1)]

    def take(self, value=None):
        t = self.peek()
        if value is not None and (t[1] != value or t[0] == "str"):
            raise LuaError("line %d: expected %r, got %r" % (t[2], value, t[1] or "end of file"))
        self.i += 1
        return t

    def check(self, value):
        return self.peek()[0] != "str" and self.peek()[1] == value

    def name(self):
        t = self.peek()
        if t[0] != "name":
            raise LuaError("line %d: expected a name, got %r" % (t[2], t[1] or "end of file"))
        self.i += 1
        return t[1]

    def chunk(self):
        return self.block()

    def block(self):
        stats = []
        while True:
            t = self.peek()
            if t[0] == "eof" or t[1] in ("end", "else", "elseif", "until"):
                return stats
            if t[1] == "return":
                line = t[2]
                self.take()
                vals = [] if self.peek()[1] in ("end", "else", "elseif", "until", ";") or self.peek()[0] == "eof" else self.exprlist()
                if self.check(";"):
                    self.take()
                stats.append({"k": "return", "vals": vals, "line": line})
                return stats
            s = self.statement()
            if s is not None:
                stats.append(s)

    def statement(self):
        t = self.peek()
        line = t[2]
        if t[1] == ";":
            self.take()
            return None
        if t[1] == "if":
            self.take()
            branches = []
            cond = self.expr()
            self.take("then")
            branches.append((cond, self.block()))
            orelse = None
            while self.check("elseif"):
                self.take()
                cond = self.expr()
                self.take("then")
                branches.append((cond, self.block()))
            if self.check("else"):
                self.take()
                orelse = self.block()
            self.take("end")
            return {"k": "if", "branches": branches, "orelse": orelse, "line": line}
        if t[1] == "while":
            self.take()
            cond = self.expr()
            self.take("do")
            body = self.block()
            self.take("end")
            return {"k": "while", "cond": cond, "body": body, "line": line}
        if t[1] == "do":
            self.take()
            body = self.block()
            self.take("end")
            return {"k": "do", "body": body, "line": line}
        if t[1] == "for":
            self.take()
            first = self.name()
            if self.check("="):
                self.take()
                start = self.expr()
                self.take(",")
                stop = self.expr()
                step = None
                if self.check(","):
                    self.take()
                    step = self.expr()
                self.take("do")
                body = self.block()
                self.take("end")
                return {"k": "fornum", "var": first, "start": start, "stop": stop, "step": step, "body": body, "line": line}
            names = [first]
            while self.check(","):
                self.take()
                names.append(self.name())
            self.take("in")
            src = self.exprlist()
            self.take("do")
            body = self.block()
            self.take("end")
            return {"k": "forin", "names": names, "src": src, "body": body, "line": line}
        if t[1] == "function":
            self.take()
            target = self.name()
            path, method = [], False
            while self.check(".") or self.check(":"):
                method = self.take()[1] == ":"
                path.append(self.name())
                if method:
                    break
            params, body = self.funcbody(line, method=method)
            return {"k": "funcdef", "target": target, "path": path, "params": params, "body": body, "line": line}
        if t[1] == "local":
            self.take()
            if self.check("function"):
                self.take()
                name = self.name()
                params, body = self.funcbody(line)
                return {"k": "localfunc", "name": name, "params": params, "body": body, "line": line}
            names = [self.name()]
            while self.check(","):
                self.take()
                names.append(self.name())
            vals = []
            if self.check("="):
                self.take()
                vals = self.exprlist()
            return {"k": "local", "names": names, "vals": vals, "line": line}
        if t[1] in ("repeat", "break", "goto") or t[1] == "::":
            raise LuaError("line %d: %r is not in the supported subset" % (line, t[1]))
        target = self.suffixed()
        if self.check("=") or self.check(","):
            targets = [target]
            while self.check(","):
                self.take()
                targets.append(self.suffixed())
            self.take("=")
            return {"k": "assign", "targets": targets, "vals": self.exprlist(), "line": line}
        if target["k"] != "call":
            raise LuaError("line %d: a statement must be a call or an assignment" % line)
        return {"k": "callstat", "call": target, "line": line}

    def funcbody(self, line, method=False):
        self.take("(")
        params = ["self"] if method else []
        while not self.check(")"):
            if self.check("..."):
                raise LuaError("line %d: varargs are not in the supported subset" % line)
            params.append(self.name())
            if self.check(","):
                self.take()
        self.take(")")
        body = self.block()
        self.take("end")
        return params, body

    def exprlist(self):
        vals = [self.expr()]
        while self.check(","):
            self.take()
            vals.append(self.expr())
        return vals

    def expr(self, limit=0):
        t = self.peek()
        if t[1] in ("not", "-", "#") and t[0] in ("kw", "op"):
            self.take()
            left = {"k": "unop", "op": t[1], "e": self.expr(UNARY_PRIO), "line": t[2]}
        else:
            left = self.simple()
        while True:
            op = self.peek()[1]
            if op not in BINARY or BINARY[op][0] <= limit:
                return left
            line = self.take()[2]
            left = {"k": "binop", "op": op, "l": left, "r": self.expr(BINARY[op][1]), "line": line}

    def simple(self):
        t = self.peek()
        if t[0] == "num":
            self.take()
            return {"k": "num", "v": t[1], "line": t[2]}
        if t[0] == "str":
            self.take()
            return {"k": "str", "v": t[1], "line": t[2]}
        if t[1] in ("nil", "true", "false"):
            self.take()
            return {"k": "const", "v": t[1], "line": t[2]}
        if t[1] == "{":
            return self.table()
        if t[1] == "function":
            self.take()
            params, body = self.funcbody(t[2])
            return {"k": "lambda", "params": params, "body": body, "line": t[2]}
        return self.suffixed()

    def table(self):
        line = self.take("{")[2]
        items = []  # (key or None, value)
        while not self.check("}"):
            if self.check("["):
                self.take()
                key = self.expr()
                self.take("]")
                self.take("=")
                items.append((key, self.expr()))
            elif self.peek()[0] == "name" and self.peek(1)[1] == "=":
                key = {"k": "str", "v": self.name(), "line": line}
                self.take("=")
                items.append((key, self.expr()))
            else:
                items.append((None, self.expr()))
            if self.check(",") or self.check(";"):
                self.take()
        self.take("}")
        return {"k": "table", "items": items, "line": line}

    def suffixed(self):
        t = self.peek()
        if t[0] == "name":
            self.take()
            e = {"k": "name", "v": t[1], "line": t[2]}
        elif t[1] == "(":
            self.take()
            e = self.expr()
            self.take(")")
        else:
            raise LuaError("line %d: unexpected %r" % (t[2], t[1] or "end of file"))
        while True:
            t = self.peek()
            if t[1] == ".":
                self.take()
                e = {"k": "index", "obj": e, "key": {"k": "str", "v": self.name(), "line": t[2]}, "line": t[2]}
            elif t[1] == "[":
                self.take()
                key = self.expr()
                self.take("]")
                e = {"k": "index", "obj": e, "key": key, "line": t[2]}
            elif t[1] == ":":
                self.take()
                meth = self.name()
                e = {"k": "call", "fn": e, "method": meth, "args": self.args(), "line": t[2]}
            elif t[1] in ("(", "{") or t[0] == "str":
                e = {"k": "call", "fn": e, "method": None, "args": self.args(), "line": t[2]}
            else:
                return e

    def args(self):
        t = self.peek()
        if t[0] == "str":
            self.take()
            return [{"k": "str", "v": t[1], "line": t[2]}]
        if t[1] == "{":
            return [self.table()]
        self.take("(")
        vals = [] if self.check(")") else self.exprlist()
        self.take(")")
        return vals


class Emitter:
    def __init__(self, comments):
        self.out = []
        self.depth = 0
        self.pending = sorted(comments)  # (line, text) not yet written
        self.blocked = []  # (line, text)
        self.review = []   # (line, text)
        self.unmapped = []  # (line, name)
        self.defined = set()

    def line(self, text):
        self.out.append("  " * self.depth + text)

    def comments_before(self, line):
        while self.pending and self.pending[0][0] <= line:
            _, text = self.pending.pop(0)
            self.line("// " + text)

    def block(self, stats):
        for s in stats:
            self.comments_before(s["line"])
            self.stat(s)

    def stat(self, s):
        k = s["k"]
        if k == "local":
            if len(s["names"]) > 1 and len(s["vals"]) not in (0, len(s["names"])):
                raise LuaError("line %d: multiple values from one call are not supported" % s["line"])
            vals = s["vals"] + [None] * (len(s["names"]) - len(s["vals"]))
            for name, val in zip(s["names"], vals):
                if val is not None and self.is_dofile(val):
                    self.line("// dofile binding dropped: the port binds its runtime")
                    continue
                self.line("let %s%s;" % (ident(name), " = " + self.expr(val) if val is not None else ""))
        elif k in ("localfunc", "funcdef"):
            if k == "localfunc":
                self.line("function %s(%s): any {" % (ident(s["name"]), params(s["params"])))
            elif s["path"]:
                self.line("%s.%s = (%s): any => {" % (ident(s["target"]), ".".join(s["path"]), params(s["params"])))
            else:
                self.line("export function %s(%s): any {" % (ident(s["target"]), params(s["params"])))
            self.depth += 1
            self.block(s["body"])
            self.depth -= 1
            self.line("};" if k == "funcdef" and s["path"] else "}")
        elif k == "assign":
            if len(s["targets"]) > 1 or len(s["vals"]) > 1:
                raise LuaError("line %d: multiple assignment is not supported, split it" % s["line"])
            if self.is_dofile(s["vals"][0]):
                self.line("// dofile binding dropped: the port binds its runtime")
                return
            self.line("%s = %s;" % (self.expr(s["targets"][0]), self.expr(s["vals"][0])))
        elif k == "callstat":
            self.line(self.expr(s["call"]) + ";")
        elif k == "return":
            if len(s["vals"]) > 1:
                raise LuaError("line %d: multiple return values are not supported" % s["line"])
            self.line("return %s;" % self.expr(s["vals"][0]) if s["vals"] else "return;")
        elif k == "if":
            for n, (cond, body) in enumerate(s["branches"]):
                head = "if" if n == 0 else "} else if"
                self.line("%s (%s) {" % (head, self.truth(cond)))
                self.depth += 1
                self.block(body)
                self.depth -= 1
            if s["orelse"] is not None:
                self.line("} else {")
                self.depth += 1
                self.block(s["orelse"])
                self.depth -= 1
            self.line("}")
        elif k == "while":
            self.line("while (%s) {" % self.truth(s["cond"]))
            self.depth += 1
            self.block(s["body"])
            self.depth -= 1
            self.line("}")
        elif k == "do":
            self.line("{")
            self.depth += 1
            self.block(s["body"])
            self.depth -= 1
            self.line("}")
        elif k == "fornum":
            v = ident(s["var"])
            step = self.expr(s["step"]) if s["step"] else "1"
            cmp = "<=" if not (s["step"] and s["step"]["k"] == "unop" and s["step"]["op"] == "-") else ">="
            self.line("for (let %s = %s; %s %s %s; %s += %s) {" % (v, self.expr(s["start"]), v, cmp, self.expr(s["stop"]), v, step))
            self.depth += 1
            self.block(s["body"])
            self.depth -= 1
            self.line("}")
        elif k == "forin":
            self.forin(s)
        else:
            raise LuaError("line %d: unknown statement %s" % (s["line"], k))

    def forin(self, s):
        src = s["src"]
        if len(src) != 1 or src[0]["k"] != "call" or src[0]["method"] or src[0]["fn"]["k"] != "name":
            raise LuaError("line %d: generic for supports pairs(t) and ipairs(t) only" % s["line"])
        fn, args = src[0]["fn"]["v"], src[0]["args"]
        if fn not in ("pairs", "ipairs") or len(args) != 1:
            raise LuaError("line %d: generic for supports pairs(t) and ipairs(t) only" % s["line"])
        names = [ident(n) for n in s["names"]]
        t = self.expr(args[0])
        if fn == "ipairs":
            i = names[0]
            v = names[1] if len(names) > 1 else "_v"
            self.line("for (let %s = 1; %s <= %s.length; %s++) {" % (i, i, t, i))
            self.depth += 1
            self.line("const %s = %s[%s - 1];" % (v, t, i))
        else:
            self.review.append((s["line"], "pairs() order and string keys: check against the Lua"))
            key, v = names[0], names[1] if len(names) > 1 else "_v"
            self.line("for (const [%s, %s] of Object.entries(%s)) {" % (key, v, t))
            self.depth += 1
        self.block(s["body"])
        self.depth -= 1
        self.line("}")

    def is_dofile(self, e):
        return e["k"] == "call" and e["fn"]["k"] == "name" and e["fn"]["v"] == "dofile"

    def truth(self, e):
        """Condition for if/while: booleans as they are, anything else through lua.truthy."""
        if e["k"] == "binop" and e["op"] in ("<", ">", "<=", ">=", "==", "~=") or e["k"] == "unop" and e["op"] == "not":
            return self.expr(e)
        return "lua.truthy(%s)" % self.expr(e)

    def expr(self, e):
        if e is None:
            return "undefined"
        k = e["k"]
        if k == "num":
            return e["v"]
        if k == "str":
            return "'" + e["v"].replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n") + "'"
        if k == "const":
            return {"nil": "undefined", "true": "true", "false": "false"}[e["v"]]
        if k == "name":
            if e["v"] in ("self",):
                return "this"
            return ident(e["v"])
        if k == "index":
            return self.index(e)
        if k == "table":
            return self.table(e)
        if k == "lambda":
            self.review.append((e["line"], "anonymous function: check its captured variables"))
            return "(%s): any => { %s }" % (params(e["params"]), self.inline(e["body"]))
        if k == "unop":
            if e["op"] == "#":
                return "%s.length" % self.expr(e["e"])
            if e["op"] == "not":
                return "!%s" % self.truth(e["e"])
            return "-%s" % self.expr(e["e"])
        if k == "binop":
            return self.binop(e)
        if k == "call":
            return self.call(e)
        raise LuaError("line %d: unknown expression %s" % (e["line"], k))

    def inline(self, body):
        sub = Emitter([])
        sub.depth = 0
        sub.block(body)
        self.blocked += sub.blocked
        self.review += sub.review
        self.unmapped += sub.unmapped
        return " ".join(x.strip() for x in sub.out)

    def binop(self, e):
        op = e["op"]
        if op == "or" and e["r"]["k"] == "table" and not e["r"]["items"]:
            return "(%s || {})" % self.expr(e["l"])
        if op in ("and", "or"):  # right side is lazy, so guards like `x and x.y` still short-circuit
            return "lua.%s(%s, () => (%s))" % (op, self.expr(e["l"]), self.expr(e["r"]))
        if op == "%":
            return "lua.mod(%s, %s)" % (self.expr(e["l"]), self.expr(e["r"]))
        if op == "..":
            return "(lua.tostr(%s) + lua.tostr(%s))" % (self.expr(e["l"]), self.expr(e["r"]))
        ts = BINARY[op][2]
        return "(%s %s %s)" % (self.expr(e["l"]), ts, self.expr(e["r"]))

    def index(self, e):
        obj = self.expr(e["obj"])
        key = e["key"]
        if key["k"] == "str":
            name = key["v"]
            return "%s.%s" % (obj, name) if re.fullmatch(r"[A-Za-z_]\w*", name) and name not in TS_RESERVED else "%s['%s']" % (obj, name)
        if key["k"] == "num" and "." not in key["v"]:
            return "%s[%d]" % (obj, int(key["v"]) - 1)
        if key["k"] == "unop" and key["op"] == "#":
            return "%s[%s.length - 1]" % (obj, self.expr(key["e"]))
        if key["k"] == "binop" and key["op"] == "+" and key["r"]["k"] == "num" and key["l"]["k"] == "unop" and key["l"]["op"] == "#":
            shift = int(key["r"]["v"]) - 1
            return "%s[%s.length%s]" % (obj, self.expr(key["l"]["e"]), (" + %d" % shift) if shift > 0 else "")
        self.review.append((e["line"], "variable index: Lua 1-based or string key? check it"))
        return "%s[%s]" % (obj, self.expr(key))

    def table(self, e):
        items = e["items"]
        if not items:
            return "[]"
        keyed = [k for k, _ in items if k is not None]
        if keyed and len(keyed) != len(items):
            raise LuaError("line %d: mixed positional and keyed table fields are not supported" % e["line"])
        if not keyed:
            return "[%s]" % ", ".join(self.expr(v) for _, v in items)
        parts = []
        for key, val in items:
            kk = key["v"] if key["k"] == "str" and re.fullmatch(r"[A-Za-z_]\w*", key["v"]) else "[%s]" % self.expr(key)
            if key["k"] == "str" and kk.startswith("["):
                kk = "'%s'" % key["v"]
            parts.append("%s: %s" % (kk, self.expr(val)))
        return "{ %s }" % ", ".join(parts)

    def call(self, e):
        args = ", ".join(self.expr(a) for a in e["args"])
        if e["method"] is not None:
            obj = e["fn"]
            if obj["k"] == "name" and obj["v"] == "SKIN":
                return self.blocked_call(e, "SKIN:%s" % e["method"])
            return "%s.%s(%s)" % (self.expr(obj), e["method"], args)
        fn = e["fn"]
        name = dotted(fn)
        if name is not None and name.startswith("SKIN."):
            return self.blocked_call(e, name)
        if name in ("SKIN:GetVariable", "SKIN.GetVariable"):
            return self.blocked_call(e, "SKIN:GetVariable")
        if name == "table.insert":
            return "%s.push(%s)" % (self.expr(e["args"][0]), self.expr(e["args"][1])) if len(e["args"]) == 2 else self.unmapped_call(e, name)
        if name == "table.remove":
            return "%s.splice(%s - 1, 1)" % (self.expr(e["args"][0]), self.expr(e["args"][1])) if len(e["args"]) == 2 else self.unmapped_call(e, name)
        if name == "table.concat":
            return "%s.join(%s)" % (self.expr(e["args"][0]), self.expr(e["args"][1]) if len(e["args"]) > 1 else "''")
        if name in ("pairs", "ipairs", "setmetatable", "select", "dofile"):
            return self.unmapped_call(e, name)
        if name in CALLS and CALLS[name]:
            return "%s(%s)" % (CALLS[name], args)
        if name in CONSTS:
            return CONSTS[name]
        root = name.split(".")[0] if name else None
        if name is not None and (root in LIBRARIES or ("." not in name and name not in self.defined)):
            self.unmapped.append((e["line"], name))
        return "%s(%s)" % (self.expr(fn), args)

    def blocked_call(self, e, what):
        self.blocked.append((e["line"], what))
        return "undefined /* BLOCKED: %s, port this as a named action */" % what

    def unmapped_call(self, e, name):
        raise LuaError("line %d: %s() needs a hand port" % (e["line"], name))


def _defined_names(src):
    """Names the file defines itself (functions and locals). Calls to anything else are reported as UNMAPPED."""
    names = set(re.findall(r"\bfunction\s+([A-Za-z_]\w*)", src)) | set(re.findall(r"\blocal\s+([A-Za-z_]\w*)", src))
    return names | set(re.findall(r"\blocal\s+function\s+([A-Za-z_]\w*)", src))


def dotted(e):
    if e["k"] == "name":
        return e["v"]
    if e["k"] == "index" and e["key"]["k"] == "str":
        base = dotted(e["obj"])
        return None if base is None else base + "." + e["key"]["v"]
    return None


def ident(name):
    return name + "_" if name in TS_RESERVED else name


def params(names):
    return ", ".join(("this" if n == "self" else ident(n)) + ": any" for n in names)


def convert(src):
    """Returns (typescript, blocked, review, unmapped). Raises LuaError on anything outside the subset."""
    parser = Parser(tokenize(src))
    tree = parser.chunk()
    if parser.peek()[0] != "eof":
        raise LuaError("line %d: unexpected %r at top level" % (parser.peek()[2], parser.peek()[1]))
    em = Emitter(parser.comments)
    em.defined = _defined_names(src)
    em.line("// Draft generated by tools/lua2ts.py from a skin module script. Review every BLOCKED and REVIEW line before use.")
    em.line("import * as lua from './luaRuntime';")
    em.line("")
    em.block(tree)
    em.comments_before(10 ** 9)
    return "\n".join(em.out) + "\n", em.blocked, em.review, em.unmapped


def main(argv):
    if len(argv) < 2:
        print("usage: lua2ts.py <file.lua> [out.ts]", file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as f:
        src = f.read()
    try:
        ts, blocked, review, unmapped = convert(src)
    except LuaError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    if len(argv) > 2:
        with open(argv[2], "w", encoding="utf-8", newline="\n") as f:
            f.write(ts)
    else:
        sys.stdout.write(ts)
    for name, rows in (("BLOCKED", blocked), ("REVIEW", review), ("UNMAPPED", unmapped)):
        for line, text in rows:
            print("%s line %d: %s" % (name, line, text), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
