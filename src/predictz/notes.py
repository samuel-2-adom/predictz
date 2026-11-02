import contextlib
import io
from datetime import datetime, timezone

from predictz import config
from predictz.storage.db import connect
from predictz.tracking import MODEL, score_predictions

MANUAL = config.ROOT / "docs" / "notes_manual.md"
OUT = config.ROOT / "PROJECT_NOTES.md"


def build_notes():
    conn = connect()
    manual = (MANUAL.read_text(encoding="utf-8") if MANUAL.exists()
              else "(docs/notes_manual.md not found)\n")
    now = datetime.now(timezone.utc)
    out = [
        manual.rstrip(), "",
        "## Live status (auto-generated, do not edit)",
        f"- Generated: {now:%Y-%m-%d %H:%M} UTC",
        f"- Current model name: {MODEL}",
        f"- Competitions: {', '.join(config.FOOTBALL_COMPETITIONS)}", "",
        "Finished matches in the database:",
    ]
    for r in conn.execute(
        "SELECT source, competition, COUNT(*) AS n, MAX(utc_date) AS last "
        "FROM matches WHERE status = 'FINISHED' "
        "GROUP BY source, competition ORDER BY source, competition"
    ):
        out.append(f"- {r['source']} {r['competition']}: {r['n']} matches, "
                   f"latest {str(r['last'])[:10]}")

    out += ["", "Logged predictions per model:"]
    for r in conn.execute(
        "SELECT model, COUNT(*) AS n, MAX(made_at) AS last "
        "FROM predictions GROUP BY model"
    ):
        out.append(f"- {r['model']}: {r['n']} logged, last made {str(r['last'])[:16]}")

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        score_predictions()
    out += ["", "Scoring (output of `score`):", "```", buf.getvalue().strip(),
            "```", "", "Source files:"]
    for folder in ("src", "scripts"):
        for p in sorted((config.ROOT / folder).rglob("*")):
            if p.suffix in (".py", ".bat"):
                out.append(f"- {p.relative_to(config.ROOT)}")

    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("Wrote", OUT)