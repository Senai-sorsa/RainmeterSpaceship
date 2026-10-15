"""calc: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import math
import re
import time
from datetime import datetime
from datetime import timedelta


# ------------------------------------------------------------------ answers by code: the clock, dates, sums, conversions
# Exact and instant, where the model is slow and gets sums wrong. Words are parsed here; nothing said is run as code.
MONTHS = "january february march april may june july august september october november december".split()
WEEKDAYS = "monday tuesday wednesday thursday friday saturday sunday".split()
# dimension, factor to the dimension's base unit (temperature: which scale), what he says, the names it is heard as
UNIT_ROWS = """length .001 millimetres mm millimetre|length .01 centimetres cm centimetre|length 1 metres m metre
length 1000 kilometres km kms kilometre|length .0254 inches inch|length .3048 feet ft foot|length .9144 yards yd yard
length 1609.344 miles mi mile|weight .001 milligrams mg milligram|weight 1 grams g gram|weight 1000 kilograms kg kgs kilogram kilo
weight 28.349523125 ounces oz ounce|weight 453.59237 pounds lb lbs pound|weight 6350.29318 stone stone
weight 1000000 tonnes tonne ton|volume .001 millilitres ml millilitre|volume 1 litres l litre
volume .00492892159375 teaspoons tsp teaspoon|volume .01478676478125 tablespoons tbsp tablespoon
volume .0295735295625 fluid_ounces fl_oz fluid_ounce|volume .2365882365 cups cup|volume .473176473 pints pint
volume .946352946 quarts quart|volume 3.785411784 gallons gallon
speed .2777777777777778 kilometres_per_hour kph km/h kmh kilometre_per_hour|speed .44704 miles_per_hour mph mile_per_hour
speed 1 metres_per_second m/s metre_per_second|speed .5144444444444445 knots knot
area 1 square_metres square_metre|area 1000000 square_kilometres square_kilometre|area .09290304 square_feet square_foot
area 2589988.110336 square_miles square_mile|area 4046.8564224 acres acre|area 10000 hectares hectare
time 1 seconds s sec secs second|time 60 minutes min mins minute|time 3600 hours hr hrs hour|time 86400 days day
time 604800 weeks week|data .125 bits bit|data 1 bytes byte|data 1000 kilobytes kb kilobyte|data 1e6 megabytes mb megabyte
data 1e9 gigabytes gb gigabyte|data 1e12 terabytes tb terabyte
temp 0 degrees_Celsius c celsius centigrade|temp 1 degrees_Fahrenheit f fahrenheit|temp 2 kelvin k kelvin"""
UNITS = {}
for _row in UNIT_ROWS.replace("\n", "|").split("|"):
    _dim, _factor, _say, *_names = _row.split()
    for _name in [_say.lower()] + _names:
        UNITS[_name.replace("_", " ")] = (_dim, float(_factor), _say.replace("_", " "))


def for_ear(x):
    """108.0 -> '108', 34.2857 -> 'about 34.3', 0.123456 -> 'about 0.123'."""
    r = float(f"{x:.3g}") if abs(x) < 1 else round(x, 2 if abs(x) < 10 else 1)
    s = f"{r:f}".rstrip("0").rstrip(".")
    return s if abs(r - x) < 1e-9 else "about " + s


def on_day(s, today):
    """'friday', 'the 3rd', 'december 25th', 'the 25th of december' -> the next such date from today, or None."""
    s = re.sub(r"^(?:next |this |the )", "", s)
    if s in WEEKDAYS:
        return today + timedelta((WEEKDAYS.index(s) - today.weekday() - 1) % 7 + 1)
    months = "|".join(MONTHS)
    m = re.fullmatch(rf"(?:({months}) (?:the )?)?(\d{{1,2}})(?:st|nd|rd|th)?(?: of ({months}))?", s)
    if not m or (m.group(1) and m.group(3)):
        return None
    month = MONTHS.index(m.group(1) or m.group(3)) + 1 if m.group(1) or m.group(3) else None
    try:
        d = today.replace(month=month or today.month, day=int(m.group(2)))
        if d < today:
            d = d.replace(year=d.year + 1) if month else (d.replace(day=1) + timedelta(32)).replace(day=d.day)
        return d
    except ValueError:                                         # February 30th, or the 31st of a short month
        return None


def calc(q):
    """'12 times 9', 'fifteen percent of 240', 'square root of 81' -> the line to say, or None."""
    # shortcut: one operation per sum ("2 plus 3 times 4" goes to the model); chains would need precedence rules
    q = re.sub(r"(?<=\d),(?=\d{3}\b)", "", q).replace("%", " percent")
    q = re.sub(r"(?<=\d) ?([-+*/×^]) ?(?=\d)", r" \1 ", q)
    m = re.fullmatch(r"(?:the )?square root of (.+)", q)
    if m:
        a, op, b = _num(m.group(1)), "root", 0
    else:
        m = re.fullmatch(r"(.+?) (?:(squared|cubed)|(plus|minus|times|x|multiplied by|divided by|over|to the power of|"
                         r"percent of|[-+*/×^]) (.+))", q)
        if not m:
            return None
        a, op = _num(m.group(1)), m.group(2) or m.group(3)
        b = {"squared": 2, "cubed": 3}[op] if m.group(2) else _num(m.group(4))
    if a is None or b is None:
        return None
    if max(a, b) > 1e12:
        return "That number is too big to say."
    op = {"plus": "+", "minus": "-", "times": "*", "x": "*", "×": "*", "multiplied by": "*", "divided by": "/",
          "over": "/", "squared": "^", "cubed": "^", "to the power of": "^", "percent of": "%"}.get(op, op)
    if op == "/" and not b:
        return "You can't divide by zero."
    if op == "^" and a > 1 and b * math.log10(a) > 15:        # refused before it is worked out, never after
        return "That number is too big to say."
    x = {"root": lambda: math.sqrt(a), "+": lambda: a + b, "-": lambda: a - b, "*": lambda: a * b, "/": lambda: a / b,
         "^": lambda: a ** b, "%": lambda: a * b / 100}[op]()
    return "That number is too big to say." if abs(x) > 1e15 else for_ear(x).capitalize() + "."


def unit(s):
    s = re.sub(r"^degrees? ", "", s).replace("meter", "metre").replace("liter", "litre").replace("s per ", " per ")
    return UNITS.get(s) or (UNITS.get(s[:-1]) if s.endswith("s") else None)


def amount(s):
    """'26 miles', 'twenty six miles', '5 feet 10' -> (number, unit row), or None."""
    s = re.sub(r"(?<=\d)(?=[a-z])", " ", s)
    m = re.fullmatch(r"(.+?) (?:feet|foot|ft) (?:and )?(.+?)(?: inch(?:es)?)?", s)
    if m and _num(m.group(1)) is not None and _num(m.group(2)) is not None:
        return _num(m.group(1)) * 12 + _num(m.group(2)), UNITS["inch"]
    w = s.split()
    for i in range(1, len(w)):
        n, u = _num(" ".join(w[:i])), unit(" ".join(w[i:]))
        if n is not None and u:
            return n, u
    return None


def convert(q):
    """'how many km in 26 miles', '100 fahrenheit in celsius' -> the line to say, or None."""
    m = re.fullmatch(r"how many (.+?) (?:are )?(?:there )?(?:in|is|are) (.+)", q)
    if m:
        dst, src = m.groups()
    else:
        m = re.fullmatch(r"(?:convert )?(.+) (?:in|to|into|as) (.+)", q)
        if not m:
            return None
        src, dst = m.groups()
    have, want = amount(src), unit(dst)
    if not have or not want or have[1][0] != want[0] or have[0] > 1e12:
        return None
    (n, (dim, f, _)), (_, g, say) = have, want
    if dim == "temp":
        c = [n, (n - 32) * 5 / 9, n - 273.15][int(f)]
        x = [c, c * 9 / 5 + 32, c + 273.15][int(g)]
    else:
        x = n * f / g
    return f"{for_ear(x).capitalize()} {say}."


def fact_answer(q, now):
    """A question the code answers exactly -> the line to say, or None (it goes to the model as before)."""
    q = re.sub(r"^(?:tell me |do you know )", "", re.sub(r"\bwhat['’]?s\b", "what is", q))
    today = datetime.fromtimestamp(now).date()
    if re.fullmatch(r"what time is it(?: now)?|what time it is|what is the time(?: now)?|the time", q):
        return f"It's {clock(now, now)}."
    if re.fullmatch(r"what is (?:the|today's) date(?: today)?|what date is it(?: today)?|(?:the|today's) date", q):
        return f"It's {today:%A}, {today:%B} {today.day}."
    if re.fullmatch(r"what day is (?:it|today)(?: today)?|what day of the week is it", q):
        return f"It's {today:%A}."
    m = re.fullmatch(r"what (?:is |will )?(?:the )?(?:date|day)(?: is it| will it be| be)? in (.+?) (days?|weeks?)", q)
    n = m and _num(m.group(1))
    if n is not None and n <= 3650:
        d = today + timedelta(n * (7 if m.group(2).startswith("week") else 1))
        return f"That's {d:%A}, {d:%B} {d.day}" + ("." if d.year == today.year else f", {d.year}.")
    m = re.fullmatch(r"what day is (.+)", q)
    d = m and on_day(m.group(1), today)
    if d:
        return f"{d:%B} {d.day} is a {d:%A}."
    m = re.fullmatch(r"how many days (?:until|till|til|to|before) (.+)", q)
    d = m and on_day(m.group(1), today)
    if d:
        n = (d - today).days
        return "That's today." if not n else f"{n} day{'s' if n != 1 else ''} until {d:%A}, {d:%B} {d.day}."
    q = re.sub(r"^(?:what is |how much is |calculate |work out )", "", q)
    return calc(q) or convert(q)


ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
        "seventeen eighteen nineteen").split()
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
_remind_bad = [False]                                         # the file could not be read: said once, not every second


def _num(s):
    """'12', '1.5', 'twelve', 'twenty five', 'a' -> the number, anything else -> None."""
    s = s.strip().replace("-", " ")
    if s in ("a", "an"):
        return 1
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return float(s)
    if not s or [w for w in s.split() if w not in ONES and w not in TENS]:
        return None
    return sum(ONES.index(w) if w in ONES else TENS[w] for w in s.split())


def clock(ts, now=None):
    d = datetime.fromtimestamp(ts)
    days = (d.date() - datetime.fromtimestamp(now or time.time()).date()).days
    return (f"{d.hour % 12 or 12}:{d.minute:02d} {'AM' if d.hour < 12 else 'PM'}"
            + ("" if days == 0 else " tomorrow" if days == 1 else d.strftime(" on %A")))
