import unittest

from godmode import memory as M
from godmode.profiles import Profile

G = M.GiB


def snap(avail, total=32, vt=12, vu=0, cu=10, cl=80):
    return M.Snapshot(int(total * G), int(avail * G), int(cu * G), int(cl * G),
                      None if vt is None else int(vt * G), None if vu is None else int(vu * G))


def prof(file_gb, exp_gb, layers=36, kv=73728, ctx=32768, ctx_min=8192):
    return Profile("x", "X", "llama-server", "m", int(file_gb * G), int(exp_gb * G), layers, kv, ctx, ctx_min, True)


class Budget(unittest.TestCase):
    def test_reserve_is_max_of_floor_and_share(self):
        self.assertEqual(M.reserve(snap(20, total=16), M.Policy()), 6 * G)
        self.assertEqual(M.reserve(snap(20, total=64), M.Policy()), int(64 * G * 0.2))

    def test_budget_never_negative(self):
        self.assertEqual(M.ram_budget(snap(3), M.Policy()), 0)

    def test_unknown_vram_is_none_not_zero(self):
        self.assertIsNone(M.vram_budget(snap(20, vt=None, vu=None), M.Policy()))


class Plan(unittest.TestCase):
    def test_unknown_vram_refuses(self):
        self.assertEqual(M.plan(prof(61, 58), snap(25, vt=None, vu=None)).mode, "refuse")

    def test_small_model_all_gpu(self):
        p = M.plan(prof(6, 5), snap(25))
        self.assertEqual((p.mode, p.n_cpu_moe), ("gpu", 0))

    def test_split_when_cpu_experts_fit_budget(self):
        p = M.plan(prof(22, 20, layers=40), snap(28, total=32))
        self.assertEqual(p.mode, "split")
        self.assertLessEqual(p.cpu_expert_bytes, p.ram_budget)
        self.assertGreater(p.n_cpu_moe, 0)
        self.assertLessEqual(p.working_set_cap, p.ram_budget)

    def test_stream_between_floor_and_full(self):
        # 120B-class: ~55 GB experts on CPU, ~23 GB comfortable -> ~40%+ -> stream
        p = M.plan(prof(61, 58), snap(30, total=32), M.Policy(reserve_min=4 * G, reserve_frac=0.1))
        self.assertEqual(p.mode, "stream", p.reason)
        self.assertEqual(p.working_set_cap, p.ram_budget)
        self.assertGreaterEqual(p.coverage, 0.4)

    def test_refuse_below_floor_with_plain_reason(self):
        p = M.plan(prof(61, 58), snap(13.7, total=31.3))
        self.assertEqual(p.mode, "refuse")
        self.assertIn("Close some apps", p.reason)

    def test_ctx_shrinks_until_vram_fits(self):
        # big KV per token: default ctx can't fit, a smaller one can
        p = M.plan(prof(10, 6, kv=400_000, ctx=32768, ctx_min=4096), snap(28))
        self.assertLess(p.ctx, 32768)
        self.assertNotEqual(p.mode, "refuse")

    def test_vram_too_small_refuses(self):
        p = M.plan(prof(30, 10), snap(28, vt=4))
        self.assertEqual(p.mode, "refuse")

    def test_threads_leave_two_cores(self):
        self.assertEqual(M.plan(prof(6, 5), snap(25), physical_cores=10).threads, 8)

    def test_never_exceeds_vram_budget(self):
        pol = M.Policy()
        for avail in (8, 14, 20, 28):
            for vu in (0, 3, 6):
                s = snap(avail, vu=vu)
                pr = prof(61, 58)
                p = M.plan(pr, s, pol)
                if p.mode != "refuse":
                    gpu = pr.other_bytes + pr.kv_bytes_per_token * p.ctx + pol.gpu_overhead + \
                          (pr.n_layers - p.n_cpu_moe) * pr.expert_bytes_per_layer
                    self.assertLessEqual(gpu, M.vram_budget(s, pol))


class OllamaCheck(unittest.TestCase):
    def test_fits(self):
        self.assertEqual(M.ollama_check(prof(22.6, 20.5, layers=40, kv=40960), snap(28))[0], "fits")

    def test_stream(self):
        mode, ctx, why = M.ollama_check(prof(22.6, 20.5, layers=40, kv=40960), snap(16, total=31.3))
        self.assertEqual(mode, "stream", why)
        self.assertGreater(ctx, 0)

    def test_refuse(self):
        self.assertEqual(M.ollama_check(prof(65, 61), snap(10, total=31.3))[0], "refuse")

    def test_empty_profile(self):
        self.assertEqual(M.ollama_check(prof(0, 0), snap(20))[0], "refuse")


class Watch(unittest.TestCase):
    def test_pause_needs_sustained_low_then_resume_with_hysteresis(self):
        w = M.Watchdog()
        acts = [w.step(snap(a)) for a in (3.5, 3.5, 3.5, 4.5, 6, 6, 6, 6, 6)]
        self.assertEqual(acts[:3], ["none", "none", "pause"])
        self.assertEqual(acts[3], "none")            # 4.5 is above pause but below resume
        self.assertEqual(acts[-1], "resume")
        self.assertFalse(w.paused)

    def test_single_dip_does_not_pause(self):
        w = M.Watchdog()
        self.assertEqual([w.step(snap(a)) for a in (3.5, 8, 3.5, 8)], ["none"] * 4)

    def test_critical_stops_once(self):
        w = M.Watchdog()
        self.assertEqual(w.step(snap(2)), "stop")
        self.assertEqual(w.step(snap(2)), "none")
        self.assertTrue(w.stopped)

    def test_commit_pressure_pauses(self):
        w = M.Watchdog()
        acts = [w.step(snap(10, cu=78, cl=80)) for _ in range(3)]
        self.assertEqual(acts[-1], "pause")


class Probe(unittest.TestCase):
    def test_parse_nvidia_smi(self):
        self.assertEqual(M.parse_nvidia_smi("12231, 0\n"), (12231 << 20, 0))
        self.assertEqual(M.parse_nvidia_smi("[N/A], [N/A]"), (None, None))
        self.assertEqual(M.parse_nvidia_smi(""), (None, None))


if __name__ == "__main__":
    unittest.main()
