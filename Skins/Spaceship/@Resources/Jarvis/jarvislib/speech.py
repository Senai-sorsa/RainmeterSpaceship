"""speech: kept so `from jarvislib.speech import ...` still works. The code lives in jarvislib/voice/ (refactor phase 3).
Names are the same objects, so a test fake set on any module that holds one still reaches the code."""
from .voice.chunker import LONG_WORDS, START_AFTER, START_BEFORE, START_CAP, _ABBR, _CLAUSE, _SENT, _WEAK, _done, _sentence, first_cut, first_words, sentences_from, smooth_sentences_from, split_long  # noqa: F401
from .voice.pacing import HESITATE, MERGE_MAX, MERGE_UNDER, hesitation_parts, merged, plan_chunks  # noqa: F401
from .voice.output import HEADPHONES, HIDE_LOG, SHOW_LOG, _out_name, headphone_gain, muted, output_name, play_samples, say_text_only  # noqa: F401
from .voice.fillers import FILLERS, _filler_audio, _filler_thread, _filler_voice, filler, filler_done, prepare_fillers  # noqa: F401
from .voice.speaker import _speak_queue, speak_all  # noqa: F401
import queue, re, threading, time  # noqa: F401,E401
# names speech.py imported and that tools or tests still read through it:
from .base import ENV_FILE, JARVIS_WORD, S, cancel, live, log, name_until, problem, setting  # noqa: F401
from .audio import speakers_mute  # noqa: F401
from . import quiet  # noqa: F401
from .voice.player import boundary, pause_ms, player, smooth_on  # noqa: F401
from .say import speakable  # noqa: F401
from .stopwords import far_add, saying  # noqa: F401
from .voice import synth as _tts  # noqa: F401
from .voice.synth import synth_audio, voice_rate  # noqa: F401
