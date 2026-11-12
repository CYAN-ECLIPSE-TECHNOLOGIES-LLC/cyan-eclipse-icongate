# Cyan Eclipse Icongate

**No product icon reaches the owner or ships without an Icongate verdict on file.**

Icongate is a small CLI gate that mechanically enforces the firm's icon
wordmark standard (owner directive 2026-11-11; gate commissioned 2026-11-12
after three draft icons arrived with their names bunched into the artwork,
clipped at the rim, and — in one case — missing entirely):

> Every product icon spells its product name inside the icon itself. The
> name sits on its own ground inside the frame, with a real margin — never
> overlapping the glyph, never clipped by the rim — and stays readable at
> actual 48px and 32px renders.

## What it checks

For a candidate icon (SVG, or a PNG with its SVG source beside it) and its
expected product name:

1. **Wordmark present** — the name appears as text in the artwork. (A bare
   raster with no SVG source FAILs with reason `no checkable source`.)
2. **Layout** — the wordmark as actually painted (renderer-true pixel
   masks: the icon rendered with and without its text elements) sits fully
   inside the disc/frame with margin on all sides. Paint outside the frame
   = *clipped by the rim*; glyph cores reaching into the wordmark band =
   *interleaved with the glyph* — both FAIL. Edge grazes and near-rim
   seating above the hard floor are recorded as notes, not failures.
3. **Legibility at size** — the cap height the source's own font-size
   produces at actual 48px and 32px, gated on the letterform cores
   painting with real contrast against the ground beneath them.

**Legibility method, stated plainly:** the estate has no OCR engine, so
Icongate makes no OCR claim. It uses the cap-height / contrast /
letter-separability proxy described above. Thresholds were calibrated
against the eight icons whose human verdicts are on record (the five
elected icons + the three rejected trio drafts) and are locked by
`tests/test_gate.py` — if a threshold change ever flips one of those
eight, the test suite fails, which is the alarm working as designed.

## Verdicts

- **PASS** — present, seated, legible at 48 and 32.
- **MARGINAL** — legible at 48, marginal at 32. Allowed only with the
  note recorded (the Monocle case).
- **FAIL** — with named reasons. No icon with a FAIL is presented or shipped.

## Use

```
pip install -e .            # deps: cairosvg, pillow, numpy

icongate check branding/icon-candidate.svg --name ROUTESEAL --out evidence/
icongate sweep path/to/icons/
icongate check icon.svg --name LOOM --json
```

Exit codes are machine-usable: `0` = PASS or MARGINAL, `1` = FAIL.
`check` writes a render sheet (512 / 48 / 32) as evidence when `--out`
is given.

## Proof

`proof/PROOF-RESULTS.md` records the commissioning proof suite: the three
rejected trio v1 drafts FAIL with the right reasons; the five elected
icons PASS (Monocle admissible as PASS or MARGINAL per its record).
Reproduce with `python proof/run_proof.py`.

## Standing notes

- Icongate is an internal CLI tool. Per the firm's new-app branding
  default, its own product icon is **not** invented here: icon election
  is the owner's act and is pending.
- Product names checked by this gate remain working names until their
  trademark screens clear; the gate checks lettering, not clearance.
