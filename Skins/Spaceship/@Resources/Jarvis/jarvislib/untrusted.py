"""untrusted: text that comes from a file or a page, not from you, is data. A note can say "ignore your instructions"; this
module finds the obvious cases so the snippet is left out of the prompt (idea and pattern families from OpenJarvis
security/injection_scanner.py, kept small). Pure functions, no I/O. The model never runs OS actions, so the damage is a
steered spoken answer; this keeps the cheap, obvious attacks out. Counts only go to the log, never the text."""
import re

PATTERNS = (
    re.compile(r"\bignore\s+(?:all\s+|any\s+)?(?:the\s+)?(?:previous|prior|above|earlier|your)\s+(?:instructions?|prompts?|rules?|programming)", re.I),
    re.compile(r"\bdisregard\s+(?:all\s+)?(?:the\s+)?(?:previous|prior|above|your)\s+(?:instructions?|programming|rules?)", re.I),
    re.compile(r"\byou\s+are\s+now\s+(?:a\s+|an\s+)?(?:different|new|my|unrestricted|jailbroken)", re.I),
    re.compile(r"\b(?:new|updated)\s+(?:system\s+)?instructions?\s*:", re.I),
    re.compile(r"\bsystem\s+prompt\b", re.I),
    re.compile(r"\b(?:reveal|print|repeat|show)\s+(?:me\s+)?(?:your|the)\s+(?:system\s+)?(?:prompt|instructions|rules)\b", re.I),
    re.compile(r"\bact\s+as\s+(?:if\s+you\s+(?:were|are)\s+)?(?:an?\s+)?(?:unrestricted|jailbroken|dan)\b", re.I),
    re.compile(r"<\s*/?\s*(?:system|assistant|im_start|im_end)\s*>|\[\s*/?\s*INST\s*\]", re.I),
    re.compile(r"\b(?:run|execute)\s+(?:this\s+)?(?:command|script)\s*:", re.I),
)


def looks_hostile(text):
    """True when the text contains an obvious instruction aimed at an assistant."""
    return any(p.search(text or "") for p in PATTERNS)


def clean_hits(hits):
    """hits: [(score, name, snippet)] -> (kept hits, number left out). A snippet that looks like an instruction is dropped."""
    kept = [h for h in hits if not (looks_hostile(h[2]) or looks_hostile(h[1]))]
    return kept, len(hits) - len(kept)


def sensitive_name(filename):
    """A-09: notes whose name says they hold secrets are not searched or indexed (names from OpenJarvis security/file_policy.py)."""
    low = (filename or "").lower()
    return bool(re.search(r"password|passwd|secret|credential|api[-_ ]?key|private[-_ ]?key|recovery[-_ ]?(?:code|key)|seed[-_ ]?phrase|2fa|\.env\b", low))
