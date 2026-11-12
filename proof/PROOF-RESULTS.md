# Icongate proof suite — commissioning results (2026-11-12)

Eight icons with human verdicts on record, gated through the shipped CLI.
Fixtures are byte-identical to the sources of record (see tests/fixtures/SOURCES.md).
Render sheets: proof/sheets/.

| file | name | human record | expected | gate verdict | match |
|---|---|---|---|---|---|
| routeseal.svg | ROUTESEAL | v1 draft, rejected 2026-11-12 — wordmark missing entirely | FAIL | **FAIL** | ✓ |
| grantseal.svg | GRANTSEAL | v1 draft, rejected 2026-11-12 — wordmark bunched/clipped at rim, illegible at size | FAIL | **FAIL** | ✓ |
| darkseal.svg | DARKSEAL | v1 draft, rejected 2026-11-12 — wordmark bunched/clipped at rim, illegible at size | FAIL | **FAIL** | ✓ |
| loom.svg | LOOM | elected 2026-11-11 (IP register §A40) | PASS | **PASS** | ✓ |
| monocle.svg | MONOCLE | elected 2026-11-11 (§A42) with a 32px-marginal note on record | PASS or MARGINAL | **PASS** | ✓ |
| plumb.svg | PLUMB | elected 2026-11-11 (§A43), legibility clean at 512/48/32 on record | PASS | **PASS** | ✓ |
| parity.svg | PARITY | elected 2026-11-11 (§A44) | PASS | **PASS** | ✓ |
| quill.svg | QUILL | elected 2026-11-11 (§A45), legibility clean at 512/48/32 on record | PASS | **PASS** | ✓ |

**Overall: ALL EIGHT MATCH THE HUMAN RECORD**

## Detail

### routeseal.svg — expected FAIL, gate FAIL

```
FAIL  /home/hatch/workspace/cyan-eclipse/icongate-build/tests/fixtures/routeseal.svg  (name: ROUTESEAL)
  FAIL-REASON: no wordmark: the artwork carries no text element at all
```
### grantseal.svg — expected FAIL, gate FAIL

```
FAIL  /home/hatch/workspace/cyan-eclipse/icongate-build/tests/fixtures/grantseal.svg  (name: GRANTSEAL)
  FAIL-REASON: wordmark clipped by the rim: 20.9% of the name's painted pixels fall outside the frame
  FAIL-REASON: wordmark interleaved with the glyph artwork: 18.6% of the name's letterform-core pixels sit on glyph-core pixels, penetrating 49% of the cap height into the wordmark band
  FAIL-REASON: wordmark illegible at 48px (cap height 3.5px, contrast 6.6, status illegible)
  FAIL-REASON: wordmark illegible at 32px (cap height 2.3px, contrast 8.2, status illegible)
  48px: illegible (cap 3.5px · contrast 6.6 · letter separability 0.89)
  32px: illegible (cap 2.3px · contrast 8.2 · letter separability 0.33)
  sheet: /home/hatch/workspace/cyan-eclipse/icongate-build/proof/sheets/grantseal-icongate-sheet.png
```
### darkseal.svg — expected FAIL, gate FAIL

```
FAIL  /home/hatch/workspace/cyan-eclipse/icongate-build/tests/fixtures/darkseal.svg  (name: DARKSEAL)
  FAIL-REASON: wordmark clipped by the rim: 11.4% of the name's painted pixels fall outside the frame
  FAIL-REASON: wordmark interleaved with the glyph artwork: 17.2% of the name's letterform-core pixels sit on glyph-core pixels, penetrating 49% of the cap height into the wordmark band
  FAIL-REASON: wordmark illegible at 48px (cap height 3.5px, contrast 4.8, status illegible)
  FAIL-REASON: wordmark illegible at 32px (cap height 2.3px, contrast 6.2, status illegible)
  48px: illegible (cap 3.5px · contrast 4.8 · letter separability 1.00)
  32px: illegible (cap 2.3px · contrast 6.2 · letter separability 0.38)
  sheet: /home/hatch/workspace/cyan-eclipse/icongate-build/proof/sheets/darkseal-icongate-sheet.png
```
### loom.svg — expected PASS, gate PASS

```
PASS  /home/hatch/workspace/cyan-eclipse/icongate-build/tests/fixtures/loom.svg  (name: LOOM)
  48px: legible (cap 7.0px · contrast 5.8 · letter separability 1.00)
  32px: legible (cap 4.7px · contrast 5.3 · letter separability 0.75)
  sheet: /home/hatch/workspace/cyan-eclipse/icongate-build/proof/sheets/loom-icongate-sheet.png
```
### monocle.svg — expected PASS or MARGINAL, gate PASS

```
PASS  /home/hatch/workspace/cyan-eclipse/icongate-build/tests/fixtures/monocle.svg  (name: MONOCLE)
  NOTE: wordmark seated close to the rim: margin 0.8 units (1.2% of frame) — inside, above the hard floor
  48px: legible (cap 4.8px · contrast 4.6 · letter separability 0.14)
  32px: legible (cap 3.2px · contrast 4.3 · letter separability 0.57)
  sheet: /home/hatch/workspace/cyan-eclipse/icongate-build/proof/sheets/monocle-icongate-sheet.png
```
### plumb.svg — expected PASS, gate PASS

```
PASS  /home/hatch/workspace/cyan-eclipse/icongate-build/tests/fixtures/plumb.svg  (name: PLUMB)
  NOTE: glyph grazes the wordmark band: 1.1% core overlap at 17% of cap height penetration — edge contact, not interleaving
  48px: legible (cap 4.8px · contrast 5.0 · letter separability 0.60)
  32px: legible (cap 3.2px · contrast 4.4 · letter separability 0.20)
  sheet: /home/hatch/workspace/cyan-eclipse/icongate-build/proof/sheets/plumb-icongate-sheet.png
```
### parity.svg — expected PASS, gate PASS

```
PASS  /home/hatch/workspace/cyan-eclipse/icongate-build/tests/fixtures/parity.svg  (name: PARITY)
  48px: legible (cap 5.1px · contrast 4.9 · letter separability 0.17)
  32px: legible (cap 3.4px · contrast 4.3 · letter separability 0.33)
  sheet: /home/hatch/workspace/cyan-eclipse/icongate-build/proof/sheets/parity-icongate-sheet.png
```
### quill.svg — expected PASS, gate PASS

```
PASS  /home/hatch/workspace/cyan-eclipse/icongate-build/tests/fixtures/quill.svg  (name: QUILL)
  48px: legible (cap 5.4px · contrast 4.7 · letter separability 1.00)
  32px: legible (cap 3.6px · contrast 4.0 · letter separability 1.00)
  sheet: /home/hatch/workspace/cyan-eclipse/icongate-build/proof/sheets/quill-icongate-sheet.png
```
