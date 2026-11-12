"""Proof-suite runner: gates the eight labelled icons through the real CLI
and writes PROOF-RESULTS.md + render sheets beside this script.

Usage: python proof/run_proof.py   (from the repo root, deps installed)
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIX = os.path.join(ROOT, "tests", "fixtures")
SHEETS = os.path.join(HERE, "sheets")

CASES = [
    ("routeseal", "ROUTESEAL", "FAIL", "v1 draft, rejected 2026-11-12 — wordmark missing entirely"),
    ("grantseal", "GRANTSEAL", "FAIL", "v1 draft, rejected 2026-11-12 — wordmark bunched/clipped at rim, illegible at size"),
    ("darkseal", "DARKSEAL", "FAIL", "v1 draft, rejected 2026-11-12 — wordmark bunched/clipped at rim, illegible at size"),
    ("loom", "LOOM", "PASS", "elected 2026-11-11 (IP register §A40)"),
    ("monocle", "MONOCLE", "PASS or MARGINAL", "elected 2026-11-11 (§A42) with a 32px-marginal note on record"),
    ("plumb", "PLUMB", "PASS", "elected 2026-11-11 (§A43), legibility clean at 512/48/32 on record"),
    ("parity", "PARITY", "PASS", "elected 2026-11-11 (§A44)"),
    ("quill", "QUILL", "PASS", "elected 2026-11-11 (§A45), legibility clean at 512/48/32 on record"),
]


def main() -> int:
    env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))
    rows, detail, all_ok = [], [], True
    for stem, name, want, record in CASES:
        proc = subprocess.run(
            [sys.executable, "-m", "icongate.cli", "check",
             os.path.join(FIX, f"{stem}.svg"), "--name", name, "--out", SHEETS],
            capture_output=True, text=True, env=env)
        verdict = proc.stdout.split()[0] if proc.stdout else "ERROR"
        ok = verdict in want.split(" or ")
        all_ok &= ok
        rows.append(f"| {stem}.svg | {name} | {record} | {want} | **{verdict}** | "
                    f"{'✓' if ok else '✗ MISMATCH'} |")
        detail.append(f"### {stem}.svg — expected {want}, gate {verdict}\n\n```\n{proc.stdout.strip()}\n```")
    doc = ["# Icongate proof suite — commissioning results (2026-11-12)", "",
           "Eight icons with human verdicts on record, gated through the shipped CLI.",
           "Fixtures are byte-identical to the sources of record (see tests/fixtures/SOURCES.md).",
           "Render sheets: proof/sheets/.", "",
           "| file | name | human record | expected | gate verdict | match |",
           "|---|---|---|---|---|---|", *rows, "",
           "**Overall: " + ("ALL EIGHT MATCH THE HUMAN RECORD" if all_ok else "MISMATCH — TOOL NOT DONE") + "**",
           "", "## Detail", "", *detail, ""]
    with open(os.path.join(HERE, "PROOF-RESULTS.md"), "w") as f:
        f.write("\n".join(doc))
    print("\n".join(rows))
    print("ALL MATCH" if all_ok else "MISMATCH")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
