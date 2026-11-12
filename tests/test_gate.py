"""Icongate tests.

The verdict tests ARE the calibration record: the eight fixtures are the
icons whose human verdicts are on record (five owner-elected icons; three
trio drafts the owner rejected 2026-11-12 with named flaws). If a future
threshold change flips any of these, the tool has drifted from the human
standard it exists to enforce — the test failing is the alarm.

Run: python -m pytest tests/   (deps: cairosvg, pillow, numpy)
"""
import os
import subprocess
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from icongate.gate import (Frame, check_icon, count_components,  # noqa: E402
                           effective_font_size, find_frame, normalize_name,
                           parse_svg)

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def check(stem, name):
    with open(os.path.join(FIX, f"{stem}.svg"), "rb") as f:
        return check_icon(f.read(), name)[0]


# --- unit: helpers -----------------------------------------------------------

def test_normalize_name():
    assert normalize_name("Grant Seal") == "GRANTSEAL"
    assert normalize_name("routeseal") == "ROUTESEAL"


def test_frame_signed_distance_circle():
    f = Frame("circle", cx=32, cy=32, r=30)
    assert f.signed_distance(32, 32) == 30
    assert f.signed_distance(32, 62) == 0
    assert f.signed_distance(32, 63) < 0


def test_frame_signed_distance_rounded_rect():
    f = Frame("rect", x=0, y=0, w=64, h=64, rx=14)
    assert f.signed_distance(32, 32) > 0
    assert f.signed_distance(32, 63) == pytest.approx(1.0)
    assert f.signed_distance(1, 1) < 0  # corner is cut by the radius


def test_count_components():
    m = np.zeros((10, 20), dtype=bool)
    m[2:5, 2:4] = True
    m[2:5, 8:10] = True
    m[8, 15] = True  # single px, below min_px
    assert count_components(m) == 2


def test_find_frame_and_font_size():
    with open(os.path.join(FIX, "loom.svg"), "rb") as fh:
        tree = parse_svg(fh.read())
    frame = find_frame(tree)
    assert frame is not None and frame.kind == "circle" and frame.r == 30
    text = [el for el in tree.iter() if el.tag.endswith("text")][0]
    assert effective_font_size(tree, text) == 13


# --- proof verdicts: the rejected trio drafts MUST fail ----------------------

def test_routeseal_fails_no_wordmark():
    r = check("routeseal", "ROUTESEAL")
    assert r.verdict == "FAIL"
    assert any("no wordmark" in x for x in r.reasons)


def test_grantseal_fails_clipped_interleaved_illegible():
    r = check("grantseal", "GRANTSEAL")
    assert r.verdict == "FAIL"
    assert any("clipped by the rim" in x for x in r.reasons)
    assert any("interleaved" in x for x in r.reasons)
    assert any("illegible at 48px" in x for x in r.reasons)
    assert any("illegible at 32px" in x for x in r.reasons)


def test_darkseal_fails_clipped_interleaved_illegible():
    r = check("darkseal", "DARKSEAL")
    assert r.verdict == "FAIL"
    assert any("clipped by the rim" in x for x in r.reasons)
    assert any("interleaved" in x for x in r.reasons)
    assert any("illegible at 48px" in x for x in r.reasons)
    assert any("illegible at 32px" in x for x in r.reasons)


# --- proof verdicts: the elected icons MUST pass ------------------------------

@pytest.mark.parametrize("stem,name", [
    ("loom", "LOOM"), ("plumb", "PLUMB"), ("parity", "PARITY"), ("quill", "QUILL"),
])
def test_elected_icons_pass(stem, name):
    r = check(stem, name)
    assert r.verdict == "PASS", f"{stem}: {r.reasons}"


def test_monocle_passes_or_marginal_only():
    # Elected with a 32px-marginal note on record (§A42): PASS or MARGINAL
    # are the only admissible gate verdicts; FAIL would mean the tool is wrong.
    r = check("monocle", "MONOCLE")
    assert r.verdict in ("PASS", "MARGINAL"), f"monocle: {r.reasons}"


def test_plumb_bracket_graze_is_a_note_not_a_fail():
    # The elected Plumb mark's bracket tips graze the M's top corner —
    # edge contact, recorded as a note; interleaving is the failure.
    r = check("plumb", "PLUMB")
    assert any("grazes" in n for n in r.notes)


def test_monocle_rim_margin_is_a_note_not_a_fail():
    r = check("monocle", "MONOCLE")
    assert any("close to the rim" in n for n in r.notes)


# --- CLI surface --------------------------------------------------------------

def _run_cli(*args):
    env = dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(__file__), "..", "src"))
    return subprocess.run([sys.executable, "-m", "icongate.cli", *args],
                          capture_output=True, text=True, env=env)


def test_cli_exit_codes(tmp_path):
    ok = _run_cli("check", os.path.join(FIX, "loom.svg"), "--name", "LOOM")
    assert ok.returncode == 0 and ok.stdout.startswith("PASS")
    bad = _run_cli("check", os.path.join(FIX, "routeseal.svg"), "--name", "ROUTESEAL")
    assert bad.returncode == 1 and bad.stdout.startswith("FAIL")


def test_cli_bare_png_has_no_checkable_source(tmp_path):
    from PIL import Image
    p = tmp_path / "icon-512.png"
    Image.new("RGBA", (512, 512), (13, 27, 42, 255)).save(p)
    r = _run_cli("check", str(p), "--name", "WHATEVER")
    assert r.returncode == 1
    assert "no checkable source" in r.stdout
