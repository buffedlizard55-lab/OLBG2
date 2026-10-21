import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from poisson import evaluate

d = json.loads((Path(__file__).resolve().parent / "events.json").read_text())
p = d["model"]
print(f"{'matchup':34} {'lh':>4} {'la':>4} {'MLh':>5} {'MLa':>5} {'puck-1.5':>8} {'o5.5':>5} {'o6.5':>5} {'pick':22} {'%':>5} {'conf':7}")
for e in d["events"]:
    m = evaluate(e, p)
    mu = f'{e["away"]["abbrev"]} @ {e["home"]["abbrev"]}'
    print(f"{mu:34} {m['lambda_home']:>4} {m['lambda_away']:>4} {m['money_line']['home']:>5} {m['money_line']['away']:>5} "
          f"{m['puck_line']['home_minus_1_5']:>8} {m['totals']['5.5']['over']:>5} {m['totals']['6.5']['over']:>5} "
          f"{m['selection'][:22]:22} {m['selection_prob']:>5} {m['confidence']:7}")
