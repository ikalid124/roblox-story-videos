import sys, os, traceback
_B = os.path.join(os.path.expanduser("~"), "Downloads", "BalloonTest")
_ts = sys.argv[sys.argv.index("--") + 1:]
_st = []
for _t in _ts:
    try:
        exec(open(os.path.join(_B, "tools", _t)).read(), {"__name__": "__main__"})
        _st.append("OK " + _t)
    except Exception:
        _st.append("ERR " + _t + "\n" + traceback.format_exc()); break
open(os.path.join(_B, "run_status.txt"), "w").write("\n".join(_st))
