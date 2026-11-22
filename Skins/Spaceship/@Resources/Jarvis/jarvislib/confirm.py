"""confirm: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import re
from .base import setting


# the whole reply has to be one of these: "yes, but don't" is not a yes
YES = {"yes", "yeah", "yep", "yup", "sure", "confirm", "confirmed", "do it", "go ahead", "proceed", "affirmative", "ok",
       "okay", "please do", "yes please", "yes do it", "yes go ahead", "yes confirm", "yes i confirm", "i confirm", "continue", "carry on",
       "yeah sure", "yes sure", "sure thing", "go for it", "absolutely", "ok do it", "okay do it", "yeah do it", "yeah go ahead",
       "yes please do", "yes absolutely", "yes definitely", "definitely"}
DANGER = re.compile(r"self[- ]?destruct|system ?32|format (?:my |the |this )?(?:[a-z]:|[c-h] drive|c\b|(?:hard |main |system |boot |whole )?(?:drive|disk|ssd|hdd|computer|pc|laptop|partition|volume|machine))|wipe (my|the)\b|delete (all|every|my files|windows)\b|rm -rf|"
                    r"disable (the )?(antivirus|defender|firewall)|\bhack\b|\bbrick\b|\bdestroy\b|\bnuke\b|blow up\b(?! (?:a |an |the |this |my )?(?:balloons?|tires?|tyres?|pool|raft|air mattress|inflatables?))|kill (all|every)\b", re.I)
# a question or a request to explain is not a destructive order: "what is a nuke", "how do I delete all my emails in gmail"
DANGER_ASK = re.compile(r"(?:(?:hey |ok |okay )?(?:jarvis |clover )?(?:please |can you |could you )?)?(?:how|what|why|who|when|where|which|whose|"
                        r"is|are|was|were|does|did|tell me|explain|describe|define|show me how|teach me)\b", re.I)
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
