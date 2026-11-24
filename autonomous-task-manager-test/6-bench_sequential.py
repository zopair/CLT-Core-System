import time, sys
from orchestrator import job
A=("unit_tests",[sys.executable,"-m","unittest","discover","-s","tests","-t","."])
B=("import_bad_file",[sys.executable,"-c","from taskmgr.core import TaskStore;s=TaskStore();s.import_json(open('data/bad_import.json').read())"])
t=time.time(); job(*A); job(*B); print("sequential run of the same two jobs: wall=%.2fs" % (time.time()-t))
