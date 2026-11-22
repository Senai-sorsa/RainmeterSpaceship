"""online: S2-5 weather (Open-Meteo, no key) and headlines (an RSS feed, no key). Off unless JarvisOnline=1.
One HTTPS request per question, cached 30 minutes, 5 s timeout, nothing in the background. The answer is a sentence this
code builds from numbers and cleaned headline text: the fetched text never reaches the model and is never an instruction."""
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from .base import log, setting

CACHE_S, TIMEOUT, MAX_BYTES = 1800, 5, 200_000
WEATHER_ASK = re.compile(r"weather|forecast|is it (?:raining|snowing|cold|hot|sunny)", re.I)
NEWS_ASK = re.compile(r"news|headlines", re.I)
FEED = "https://feeds.bbci.co.uk/news/rss.xml"                 # JarvisNewsFeed overrides it (https only)
SKY = {0: "clear", 1: "mostly clear", 2: "partly cloudy", 3: "overcast", 45: "foggy", 48: "foggy", 51: "drizzly", 53: "drizzly",
       55: "drizzly", 56: "freezing drizzle", 57: "freezing drizzle", 61: "rainy", 63: "rainy", 65: "heavy rain", 66: "freezing rain",
       67: "freezing rain", 71: "snowy", 73: "snowy", 75: "heavy snow", 77: "snowy", 80: "showery", 81: "showery", 82: "heavy showers",
       85: "snow showers", 86: "snow showers", 95: "stormy", 96: "stormy", 99: "stormy"}
_cache = {}


def fetch(url):
    """The body of an https URL, at most MAX_BYTES. Raises OSError (URLError is one) on any failure."""
    if not url.startswith("https://"):
        raise OSError("not https")
    req = urllib.request.Request(url, headers={"User-Agent": "CSpace-JARVIS"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read(MAX_BYTES)


def cached(key, make):
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_S:
        return hit[1]
    value = make()
    _cache[key] = (time.time(), value)
    return value


def clean(s, cap):
    """Untrusted text: letters, digits and plain punctuation only, cut at cap."""
    return re.sub(r"\s+", " ", re.sub(r"[^\w .,'&:%-]", " ", s or "")).strip()[:cap]


def weather(text):
    place = setting("JarvisPlace", "").strip().strip('"')
    if not place:
        return "I don't know your town. Set JarvisPlace in the settings."
    geo = json.loads(cached(("geo", place), lambda: fetch(
        "https://geocoding-api.open-meteo.com/v1/search?count=1&name=" + urllib.parse.quote(place))))["results"][0]
    lat, lon = float(geo["latitude"]), float(geo["longitude"])
    w = json.loads(cached(("wx", lat, lon), lambda: fetch(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat:.3f}&longitude={lon:.3f}&timezone=auto&forecast_days=2"
        "&temperature_unit=fahrenheit&wind_speed_unit=mph&current=temperature_2m,weather_code"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min")))
    name = clean(str(geo.get("name", place)), 40) or "your town"
    d = w["daily"]
    if re.search(r"tomorrow", text, re.I):
        return (f"Tomorrow in {name}: {SKY.get(int(d['weather_code'][1]), 'mixed')}, a high of {round(d['temperature_2m_max'][1])} "
                f"and a low of {round(d['temperature_2m_min'][1])} degrees.")
    c = w["current"]
    return (f"In {name} it's {round(c['temperature_2m'])} degrees and {SKY.get(int(c['weather_code']), 'mixed')}, with a high of "
            f"{round(d['temperature_2m_max'][0])} and a low of {round(d['temperature_2m_min'][0])} today.")


def headlines():
    url = setting("JarvisNewsFeed", FEED).strip().strip('"') or FEED
    raw = cached(("rss", url), lambda: fetch(url))
    if re.search(rb"<!(?:DOCTYPE|ENTITY)", raw, re.I):         # no entity tricks from a feed
        raise ValueError("feed has a DTD")
    ch = ET.fromstring(raw).find("channel")
    titles = [t for t in (clean(i.findtext("title"), 120) for i in ch.findall("item")[:5]) if t][:3]
    if not titles:
        raise ValueError("no headlines")
    return "Top headlines from " + (clean(ch.findtext("title"), 30) or "the feed") + ": " + ". ".join(titles) + "."


def answer(text):
    """The spoken answer to a weather or news question, or None when this is not one or online is off."""
    if setting("JarvisOnline", "0") != "1":
        return None
    kind = "weather" if WEATHER_ASK.search(text) else "news" if NEWS_ASK.search(text) else None
    if kind is None:
        return None
    try:
        return weather(text) if kind == "weather" else headlines()
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError, ET.ParseError) as e:
        log(f"online: {kind} failed ({type(e).__name__})")
        return f"I couldn't reach the {kind} service."
