"""respath: which folder is @Resources for this process. No imports of jarvislib and no side effects, so it can be tested without
creating a Data folder (the trap in the refactor plan, section 6: a tool that keeps its own flag, `--cases x`, used to get RES="--cases").

  1. the first command-line argument, when it is a folder (the host starts `jarvis.py <@Resources>`); an argument that starts with "-" is
     a tool's own flag and is never a folder;
  2. the JARVIS_RES environment variable, for tools and tests that keep their own arguments;
  3. @Resources two folders above jarvislib (the skin's own, as before)."""
import os


def pick_res(argv, env, here):
    arg = argv[1].strip().strip('"') if len(argv) > 1 else ""
    if arg.startswith("-"):
        arg = ""
    override = (env.get("JARVIS_RES") or "").strip().strip('"')
    return os.path.abspath(arg or override or os.path.join(here, "..", ".."))
