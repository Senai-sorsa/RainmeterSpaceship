"""confirm: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import re
from .base import setting


# the whole reply has to be one of these: "yes, but don't" is not a yes
YES = {"yes", "yeah", "yep", "yup", "sure", "confirm", "confirmed", "do it", "go ahead", "proceed", "affirmative", "ok",
       "okay", "please do", "yes please", "yes do it", "yes go ahead", "yes confirm", "yes i confirm", "i confirm", "continue", "carry on"}
DANGER = re.compile(r"self[- ]?destruct|system ?32|format (my|the|c)|wipe (my|the)|delete (all|every|my files|windows)|rm -rf|"
                    r"disable (the )?(antivirus|defender|firewall)|hack|brick|destroy|nuke|blow up|kill (all|every)", re.I)
NAMES = "travis jervis javis jarvus service droves drovis glover klover clova".split()   # how Whisper writes "Jarvis" (JarvisNameAliases adds more)


def is_yes(answer):
    """A plain yes; his name, "sir" or "now" around it is fine ("Yes, Jarvis." / "yes sir"). "yes, but don't" is not."""
    said = " ".join(re.sub(r"[^a-z]+", " ", (answer or "").lower()).split())
    extra = [re.escape(n.strip().lower()) for n in setting("JarvisNameAliases", "").split(",") if n.strip()]
    around = "|".join(["clover", "jarvis", "sir", "now"] + NAMES + extra)
    return re.sub(rf"^(?:(?:{around}) )+|(?: (?:{around}))+$", "", said) in YES


def confirmed(pending, answer, now):
    """True only for a plain yes to this pending action before it expires."""
    return is_yes(answer) and now < pending["expires"]
