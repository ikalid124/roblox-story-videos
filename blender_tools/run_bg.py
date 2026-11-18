import sys, os, traceback
_B = os.path.join(os.path.expanduser("~"), "Downloads", "BalloonTest")
_t = sys.argv[sys.argv.index("--") + 1]
try:
    exec(open(os.path.join(_B, "tools", _t)).read(), {"__name__": "__main__"})
    open(os.path.join(_B, "run_status.txt"), "w").write("OK " + _t)
except Exception:
    open(os.path.join(_B, "run_status.txt"), "w").write("ERR " + _t + "\n" + traceback.format_exc())
