"""Run: python3 -I tools/test_launch_target.py   (pure string checks; starts nothing)"""
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("launch", os.path.join(ROOT, "Skins", "Spaceship", "@Resources", "Jarvis", "jarvislib", "launch.py"))
launch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launch)
T = launch.launch_target


class LaunchTarget(unittest.TestCase):
    def test_installed_app_ids_pass(self):
        for a in ("Microsoft.WindowsCalculator_8wekyb3d8bbwe!App",
                  r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe",
                  r"{7C5A40EF-A0FB-4BFC-874A-C0F2E0B9FA8E}\Foo (x86)\foo.exe"):
            self.assertEqual(T(a), "shell:AppsFolder\\" + a)

    def test_local_programs_and_shortcuts_pass(self):
        for a in (r"C:\Program Files\App\app.exe", r"D:\Games\x.lnk", r"C:\a\b.URL"):
            self.assertEqual(T(a), a)

    def test_everything_else_is_refused(self):
        for a in ("", "   ", r"\\server\share\a.exe", r"C:\a\..\b.exe", r"C:\a\script.bat", r"C:\a\doc.txt", r"C:\a\noext",
                  'C:\\a\\"b.exe', "x\ny", "a|b", "..\\evil", r"{G}\..\x", "cmd /c calc", "a;b", r"C:\a\b.exe:stream.txt"):
            with self.assertRaises(OSError, msg=a):
                T(a)


if __name__ == "__main__":
    unittest.main()
