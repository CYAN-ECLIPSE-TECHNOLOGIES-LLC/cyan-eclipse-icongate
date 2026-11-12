"""Icongate CLI: `icongate check <file> --name <NAME>` · `icongate sweep <dir>`.

Exit codes: 0 = PASS or MARGINAL · 1 = FAIL (machine-usable in build lanes).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from .gate import GateResult, check_icon, render_sheet

GENERIC_STEMS = {"icon", "icon-candidate", "logo", "brand", "index"}


def resolve_source(path: str) -> tuple[bytes | None, str | None]:
    """Returns (svg_bytes, fail_reason). A PNG is checkable only through an
    SVG source beside it (same stem); a bare raster has no checkable source."""
    if path.lower().endswith(".svg"):
        with open(path, "rb") as f:
            return f.read(), None
    if path.lower().endswith(".png"):
        sibling = path[:-4] + ".svg"
        if os.path.exists(sibling):
            with open(sibling, "rb") as f:
                return f.read(), None
        return None, "no checkable source: raster PNG without an SVG source beside it"
    return None, f"unsupported file type: {os.path.basename(path)} (want .svg or .png)"


def guess_name(path: str) -> str:
    stem = os.path.splitext(os.path.basename(path))[0].lower()
    for affix in ("icon-", "-icon", "icon_", "_icon"):
        stem = stem.replace(affix, "")
    if stem in GENERIC_STEMS or not stem:
        parent = os.path.basename(os.path.dirname(os.path.abspath(path)))
        stem = parent.replace("cyan-eclipse-", "").replace("eclipse-", "")
    return stem.replace("-", " ").replace("_", " ").title()


def run_check(path: str, name: str, out_dir: str | None, as_json: bool) -> int:
    svg, fail = resolve_source(path)
    if fail is not None:
        result = GateResult(verdict="FAIL", reasons=[fail])
        renders = {}
    else:
        result, renders = check_icon(svg, name)

    sheet_path = None
    if out_dir and renders:
        os.makedirs(out_dir, exist_ok=True)
        stem = os.path.splitext(os.path.basename(path))[0]
        sheet_path = os.path.join(out_dir, f"{stem}-icongate-sheet.png")
        render_sheet(renders, result.verdict, f"{name} | {os.path.basename(path)}").save(sheet_path)

    if as_json:
        print(json.dumps({
            "file": path, "name": name, "verdict": result.verdict,
            "reasons": result.reasons, "notes": result.notes,
            "metrics": result.metrics,
            "grades": [g.__dict__ for g in result.grades],
            "sheet": sheet_path,
        }, indent=2))
    else:
        print(f"{result.verdict}  {path}  (name: {name})")
        for r in result.reasons:
            print(f"  FAIL-REASON: {r}")
        for n in result.notes:
            print(f"  NOTE: {n}")
        for g in result.grades:
            print(f"  {g.size}px: {g.status} (cap {g.cap_height_px:.1f}px · "
                  f"contrast {g.contrast:.1f} · letter separability {g.gap_score:.2f})")
        if sheet_path:
            print(f"  sheet: {sheet_path}")
    return 1 if result.verdict == "FAIL" else 0


def run_sweep(directory: str, out_dir: str | None, as_json: bool) -> int:
    files = []
    for root, _dirs, names in os.walk(directory):
        for n in sorted(names):
            low = n.lower()
            if low.endswith(".svg"):
                files.append(os.path.join(root, n))
            elif low.endswith(".png"):
                if not os.path.exists(os.path.join(root, n[:-4] + ".svg")):
                    files.append(os.path.join(root, n))
    worst = 0
    rows = []
    for f in files:
        name = guess_name(f)
        svg, fail = resolve_source(f)
        if fail is not None:
            verdict, reasons = "FAIL", [fail]
        else:
            result, _ = check_icon(svg, name)
            verdict, reasons = result.verdict, result.reasons
        rows.append((f, name, verdict, reasons))
        if verdict == "FAIL":
            worst = 1
        if not as_json:
            print(f"{verdict:8s} {name:20s} {f}")
            for r in reasons:
                print(f"         FAIL-REASON: {r}")
    counts = {v: sum(1 for r in rows if r[2] == v) for v in ("PASS", "MARGINAL", "FAIL")}
    if as_json:
        print(json.dumps({"sweep": directory, "counts": counts,
                          "rows": [{"file": f, "name": n, "verdict": v, "reasons": rs}
                                   for f, n, v, rs in rows]}, indent=2))
    else:
        print(f"sweep: {counts['PASS']} PASS · {counts['MARGINAL']} MARGINAL · "
              f"{counts['FAIL']} FAIL  ({len(rows)} icons under {directory})")
    return worst


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="icongate",
                                 description="Cyan Eclipse Icongate — the icon wordmark gate.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="gate one icon")
    c.add_argument("file")
    c.add_argument("--name", required=True, help="expected product name, e.g. --name LOOM")
    c.add_argument("--out", default=None, help="directory for the render-sheet evidence")
    c.add_argument("--json", action="store_true")
    s = sub.add_parser("sweep", help="gate every icon under a directory")
    s.add_argument("directory")
    s.add_argument("--out", default=None)
    s.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.cmd == "check":
        return run_check(args.file, args.name, args.out, args.json)
    return run_sweep(args.directory, args.out, args.json)


if __name__ == "__main__":
    sys.exit(main())
