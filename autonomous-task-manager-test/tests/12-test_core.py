import unittest, tempfile, os, json
from taskmgr.core import TaskStore, ValidationError
SEED = os.path.join(os.path.dirname(__file__), "..", "data", "seed_tasks.json")
class T(unittest.TestCase):
    def setUp(self):
        self.st = TaskStore()
    def test_add_defaults(self):
        t = self.st.add("a"); self.assertEqual((t["id"], t["priority"], t["done"]), (1, "medium", False))
    def test_empty_title(self):
        with self.assertRaises(ValidationError): self.st.add("   ")
    def test_bad_priority(self):
        with self.assertRaises(ValidationError): self.st.add("a", "urgent")
    def test_done_reopen(self):
        t = self.st.add("a"); self.st.set_done(t["id"]); self.assertTrue(self.st.tasks[0]["done"])
        self.st.set_done(t["id"], False); self.assertFalse(self.st.tasks[0]["done"])
    def test_delete_and_missing(self):
        t = self.st.add("a"); self.st.delete(t["id"]); self.assertEqual(self.st.tasks, [])
        with self.assertRaises(KeyError): self.st.delete(99)
    def test_ids_not_reused_after_delete_of_middle(self):
        a = self.st.add("a"); b = self.st.add("b"); self.st.delete(a["id"])
        self.assertEqual(self.st.add("c")["id"], b["id"] + 1)
    def test_sort_and_filter(self):
        self.st.add("l", "low"); self.st.add("h2", "high", "2026-12-02"); self.st.add("h1", "high", "2026-12-01")
        self.assertEqual([t["title"] for t in self.st.list()], ["h1", "h2", "l"])
        self.assertEqual(len(self.st.list(priority="low")), 1)
    def test_status_filter(self):
        a = self.st.add("a"); self.st.add("b"); self.st.set_done(a["id"])
        self.assertEqual(len(self.st.list("done")), 1); self.assertEqual(len(self.st.list("open")), 1)
    def test_persistence_roundtrip(self):
        p = os.path.join(tempfile.mkdtemp(), "t.json")
        s = TaskStore(p); s.add("x", "high"); s.save()
        self.assertEqual(TaskStore(p).tasks[0]["title"], "x")
    def test_seed_loads(self):
        s = TaskStore(SEED); self.assertEqual(len(s.tasks), 5); self.assertEqual(len({t["id"] for t in s.tasks}), 5)
    def test_import_valid(self):
        self.st.add("a"); n = self.st.import_json('[{"title":"b"},{"title":"c"}]')
        self.assertEqual((n, len(self.st.tasks)), (2, 3)); self.assertEqual(len({t["id"] for t in self.st.tasks}), 3)
    def test_import_malformed_leaves_data(self):
        self.st.add("a")
        for bad in ["{oops", '{"a":1}', '[{"title":"ok"},{"title":""}]']:
            with self.assertRaises(ValidationError): self.st.import_json(bad)
        self.assertEqual(len(self.st.tasks), 1)
if __name__ == "__main__": unittest.main()
