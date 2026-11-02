import sys

from predictz.backtest.walk_forward import load_matches, run, report
from predictz.models.reference import Baseline, Bookmaker
from predictz.models.elo import Elo

comp = sys.argv[1] if len(sys.argv) > 1 else "PL"
matches = load_matches(comp)
print(comp, len(matches), "matches loaded\n")
results = run([Baseline(), Elo(), Bookmaker()], matches, eval_from=2017)
report(results)