import sys, argparse
from .core import TaskStore, ValidationError
def main(argv=None):
    p = argparse.ArgumentParser(prog="taskmgr")
    p.add_argument("--db", default="data/tasks.json")
    s = p.add_subparsers(dest="cmd", required=True)
    a = s.add_parser("add"); a.add_argument("title"); a.add_argument("--priority", default="medium"); a.add_argument("--due")
    l = s.add_parser("list"); l.add_argument("--status"); l.add_argument("--priority")
    d = s.add_parser("done"); d.add_argument("id", type=int)
    r = s.add_parser("delete"); r.add_argument("id", type=int)
    args = p.parse_args(argv)
    st = TaskStore(args.db)
    try:
        if args.cmd == "add": print("added", st.add(args.title, args.priority, args.due)["id"])
        elif args.cmd == "list":
            for t in st.list(args.status, args.priority):
                print("[%s] #%d %-6s %s %s" % ("x" if t["done"] else " ", t["id"], t["priority"], t["due"] or "-", t["title"]))
        elif args.cmd == "done": st.set_done(args.id)
        elif args.cmd == "delete": st.delete(args.id)
        st.save()
    except (ValidationError, KeyError) as e:
        print("error:", e); return 1
    return 0
if __name__ == "__main__": sys.exit(main())
