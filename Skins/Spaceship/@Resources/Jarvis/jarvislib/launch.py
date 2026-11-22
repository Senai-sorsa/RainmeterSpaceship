"""What "open <app>" may start. Pure (no Windows calls) so tools/test_launch_target.py can run it anywhere.
StartApps.txt is a plain data file, so its contents are untrusted: only an installed-app id or a local program/shortcut path passes."""
import ntpath
import re

APP_ID = re.compile(r"[A-Za-z0-9_.!{}\-]+(?:\\[A-Za-z0-9_. {}()+,&'\-]+)*\Z")           # AUMID or known-folder id: no drive, no quotes, no ..
PATH_EXT = {".exe", ".lnk", ".url", ".appref-ms"}


def launch_target(appid):
    """The string to hand to os.startfile, or OSError. An absolute path must be a local drive path to a program or shortcut."""
    a = (appid or "").strip()
    if not a or any(c in a for c in '\x00\r\n"<>|*?'):
        raise OSError("that app entry is not valid")
    if ntpath.isabs(a):
        if a.startswith("\\\\") or ".." in a.split("\\") or ntpath.splitext(a)[1].lower() not in PATH_EXT:
            raise OSError("that app path is not allowed")
        return a
    if not APP_ID.match(a) or ".." in a:
        raise OSError("that app id is not valid")
    return "shell:AppsFolder\\" + a
