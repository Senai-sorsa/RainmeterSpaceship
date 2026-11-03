"""The reply filter chain, defined once (refactor phase 2). exchange() used to build it inline.

Order (each stage reads the one before, lazily: the first piece goes to the voice as soon as it is ready):
  sentences_from  chunks the model stream (speech.py; JarvisVoiceSmooth picks the chunker), appends raw text to `collected`
  no_claims       "I've set it" / "the PC will lock" -> CLAIM_LINE; "I'll send it" -> CANT_LINE; the answer ends (routing.py)
  no_hope         drops "I hope this helps" sentences (mood.py)
  grounded        a reading or count that is not in `known` -> NO_READING; the answer ends (mood.py)
  polish          stock sentences, "sir" once, Mr. Sorsa only when serious, the sentence cap, "Pardon ...?" (mood.py)
A stage may pass, edit, or end the reply with a registered fixed line (reply/fixed.py). It never speaks.
mood's stages are looked up on the module at call time, so a test that patches mood.polish still reaches here."""
from .. import mood
from ..routing import no_claims
from ..speech import sentences_from

ORDER = ("sentences_from", "no_claims", "no_hope", "grounded", "polish")


def reply_chain(stream, collected, known, cap, serious):
    """The spoken pieces of a model reply (a lazy generator). `collected` gets the raw text, or the fixed line that replaced it."""
    return mood.polish(mood.grounded(mood.no_hope(no_claims(sentences_from(stream, collected), collected)), collected, known),
                       collected, cap, serious)
