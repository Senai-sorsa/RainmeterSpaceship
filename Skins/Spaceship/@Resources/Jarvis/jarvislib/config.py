"""Every JARVIS setting key and its code default, in one table (refactor phase 1).

Settings.inc is the user's file and wins whenever a key is set there; this table is what the code uses when it is not.
Call sites still read `setting("Key", default)` (tests fake `setting` per module, see test_jarvis.py), so the default is
still written at the call site too; tests/test_settings_schema.py fails if any call site's default differs from this table,
if code reads a key that is not here, or if a key here is never read. To add a setting: one entry here, then the read.

No imports on purpose: importing this module never reads sys.argv / RES (see the trap in the refactor plan, section 6)."""

DEFAULTS = {
    # model and context
    "JarvisModel": "llama3.1:8b",
    "JarvisModelFast": "",
    "JarvisContext": "2048",
    "JarvisKeepAlive": "10",
    "JarvisIdleUnload": "10",
    "JarvisGPU": "prefer",
    "PerfTier": "0",
    # who he is / how he talks
    "JarvisName": "Clover",
    "JarvisNameAliases": "",
    "JarvisCallMe": "",
    "JarvisPersonality": "mirror",
    "JarvisSeriousTopics": "1",
    "JarvisPrivacy": "0",
    "JarvisTalkLess": "0",
    "JarvisProfile": "",
    "JarvisLearn": "auto",
    "JarvisRecall": "on",
    # understanding
    "JarvisAIRouter": "1",
    "JarvisSmartSearch": "1",
    "JarvisDiagnose": "1",
    "JarvisRoomAsk": "0",
    "JarvisOnline": "0",
    "JarvisPlace": "",
    "JarvisNewsFeed": "https://feeds.bbci.co.uk/news/rss.xml",
    # listening
    "JarvisEnabled": "1",
    "JarvisWakeWord": "1",
    "JarvisWakeModel": "hey_jarvis",
    "JarvisWakeSensitivity": "0.5",
    "JarvisWakeVerify": "0",
    "JarvisBargeIn": "wake",
    "JarvisFollowUp": "1",
    "JarvisFollowUpWait": "3",
    "JarvisFollowNameWindow": "10",
    "JarvisMic": "",
    "JarvisSilence": "1.0",          # mic.py also reads it raw ("" = not set) to decide whether JarvisFastEnd applies
    "JarvisFastEnd": "1",
    "JarvisDuck": "1",
    "JarvisDuckLevel": "30",
    "JarvisWhisper": "small.en",
    "JarvisWhisperDevice": "auto",
    "JarvisStopKey": "end",
    "JarvisQuietCalendar": "",
    # voice
    "JarvisVoice": "",
    "JarvisKokoroVoice": "bm_lewis",  # speech.py also reads it raw ("" = not set) as part of the filler cache key
    "JarvisVoiceRate": "1",
    "JarvisVoiceSpeed": "1",
    "JarvisFirstWords": "5",
    "JarvisHeadphoneLevel": "60",
    "JarvisMutedPopup": "1",
    "JarvisChime": "1",
    "JarvisChimeVolume": "25",
    "JarvisVoiceSmooth": "1",         # player.SMOOTH_DEFAULT (test_jarvis.py switches it to "0" for the older speech tests)
    "JarvisWasapi": "1",
    "JarvisPauseCont": 25,            # numbers: player._num() / pause_ms() read these
    "JarvisPauseClause": 150,
    "JarvisPauseSentence": 300,
    "JarvisPauseHesitate": 350,
    "JarvisTrimDb": -45,
    "JarvisFadeMs": 10,
    "JarvisIdleClose": 1.5,
    # devices, notes, logs
    "JarvisBtNames": "",
    "JarvisVault": "",
    "ObsidianTodo": "",
    "JarvisLogHours": "24",
    "JarvisWatch": "1",
}

# Reads that pass "" on purpose to learn whether the user set the key at all (not a second default).
RAW_READS = {("JarvisSilence", ""), ("JarvisKokoroVoice", "")}


def default(name):
    """The code default of a setting (KeyError for an unknown key, so a typo fails loudly)."""
    return DEFAULTS[name]
