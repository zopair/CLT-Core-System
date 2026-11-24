import json, os, itertools
PRIORITIES = {"high": 0, "medium": 1, "low": 2}

class ValidationError(ValueError):
    pass

class TaskStore:
    def __init__(self, path=None):
        self.path = path
        self.tasks = []
        if path and os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self.tasks = self._parse(f.read())

    @staticmethod
    def _validate(t):
        if not isinstance(t, dict):
            raise ValidationError("task must be an object")
        title = t.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValidationError("title is required")
        if t.get("priority", "medium") not in PRIORITIES:
            raise ValidationError("unknown priority: %r" % t.get("priority"))
        return {"id": t.get("id"), "title": title.strip(),
                "priority": t.get("priority", "medium"),
                "due": t.get("due"), "done": bool(t.get("done", False))}

    def _parse(self, text):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValidationError("invalid JSON: %s" % e)
        if not isinstance(data, list):
            raise ValidationError("top level must be a list")
        out = [self._validate(t) for t in data]
        used = {t["id"] for t in out if t["id"] is not None}
        n = itertools.count(1)
        for t in out:
            if t["id"] is None:
                i = next(n)
                while i in used: i = next(n)
                t["id"] = i; used.add(i)
        return out

    def _next_id(self):
        return max([t["id"] for t in self.tasks], default=0) + 1

    def add(self, title, priority="medium", due=None):
        t = self._validate({"title": title, "priority": priority, "due": due})
        t["id"] = self._next_id()
        self.tasks.append(t)
        return t

    def _get(self, tid):
        for t in self.tasks:
            if t["id"] == tid: return t
        raise KeyError(tid)

    def set_done(self, tid, done=True):
        self._get(tid)["done"] = done

    def delete(self, tid):
        self.tasks.remove(self._get(tid))

    def list(self, status=None, priority=None):
        r = self.tasks
        if status == "done": r = [t for t in r if t["done"]]
        elif status == "open": r = [t for t in r if not t["done"]]
        if priority: r = [t for t in r if t["priority"] == priority]
        return sorted(r, key=lambda t: (PRIORITIES[t["priority"]], t["due"] or "9999", t["id"]))

    def import_json(self, text):
        new = self._parse(text)  # raises before any change
        base = self._next_id()
        for i, t in enumerate(new):
            t["id"] = base + i
        self.tasks.extend(new)
        return len(new)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, indent=2, ensure_ascii=False)
