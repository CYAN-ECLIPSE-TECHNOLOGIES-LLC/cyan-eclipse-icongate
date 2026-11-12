"""Cyan Eclipse Icongate — mechanical icon gate.

Enforces the firm's icon wordmark standard (owner directive 2026-11-11,
gate commissioned 2026-11-12): every product icon spells its product name
inside the icon itself, the name sits on its own ground inside the frame
with a real margin — never bunched into the glyph, never clipped by the
rim — and the name stays readable at actual 48px and 32px renders.

Method notes (stated plainly, per the commission):
- Wordmark presence + geometry come from the SVG source and from
  renderer-true pixel masks: the icon is rendered with CairoSVG with and
  without its <text> elements; the pixel difference IS the wordmark as
  actually painted (real font metrics, real positions).
- Legibility at size uses a contrast / cap-height / letter-separability
  proxy over those rendered masks. tesseract is not present in the
  estate, so no OCR claim is made; the proxy thresholds were calibrated
  against the eight icons whose human verdicts are on record (the five
  elected icons + the three rejected 2026-11-12 trio drafts) and are
  locked in tests/test_gate.py.
- Renderer of record (owner ruling 2026-11-12): verdicts of record are
  produced only on the calibration toolchain (the VM tools-venv renderer
  stack). The Shard E renderer variance on the Monocle boundary fixture
  (rim margin -0.1u here vs +0.77u on the calibration stack; the two
  rim-margin tests) is a named accepted variance, not a verdict defect.
  A verdict from any other renderer must be labelled with its renderer
  and does not supersede a calibration-stack verdict.
"""
from __future__ import annotations

import io
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import cairosvg
import numpy as np
from PIL import Image

# --- locked thresholds (calibrated 2026-11-12; see tests) -------------------
# Calibration set: the eight icons with human verdicts on record — the five
# elected icons (Loom · Monocle · Plumb · Parity · Quill) and the three trio
# drafts the owner rejected 2026-11-12. Core masks (strict delta) carry the
# legibility + overlap calls; the soft mask (AA-inclusive) carries the
# rim/margin calls, because AA halo is paint a viewer sees at the rim but
# not letterform.
DIFF_THRESHOLD = 24            # per-channel delta that counts as "painted"
CORE_THRESHOLD = 110           # per-channel delta for letterform cores
OUTSIDE_TOLERANCE = 0.001      # fraction of wordmark px allowed outside frame
OVERLAP_TOLERANCE = 0.005      # fraction of wordmark CORE px allowed over glyph cores
MARGIN_MIN_FRAC = 0.01         # hard floor: rim margin, fraction of frame size
MARGIN_NOTE_FRAC = 0.025       # below this, margin is reported as a note
CAP_RATIO = 0.716              # cap height / font-size, grotesque sans average
CAP_LEGIBLE = {48: 4.0, 32: 3.1}    # analytic cap height px at render size
CAP_MARGINAL_32 = 2.7          # 48px has no marginal band: legible or not
CONTRAST_LEGIBLE = 3.0
CONTRAST_MARGINAL = 2.5
OVERLAP_HARD = 0.05            # core overlap above this fails at any depth
OVERLAP_DEPTH_FAIL = 0.30      # glyph penetration into the wordmark band,
                               # fraction of cap height — above = interleaved
GEOMETRY_RENDER = 1024


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def normalize_name(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())


@dataclass
class Frame:
    kind: str                       # "circle" | "rect"
    cx: float = 0.0
    cy: float = 0.0
    r: float = 0.0
    x: float = 0.0
    y: float = 0.0
    w: float = 0.0
    h: float = 0.0
    rx: float = 0.0

    @property
    def size(self) -> float:
        return 2 * self.r if self.kind == "circle" else max(self.w, self.h)

    def signed_distance(self, px: float, py: float) -> float:
        """Positive = inside, distance to boundary; negative = outside."""
        if self.kind == "circle":
            return self.r - math.hypot(px - self.cx, py - self.cy)
        # rounded rect: standard sdRoundBox
        rx = min(self.rx, self.w / 2, self.h / 2)
        cx, cy = self.x + self.w / 2, self.y + self.h / 2
        qx = abs(px - cx) - (self.w / 2 - rx)
        qy = abs(py - cy) - (self.h / 2 - rx)
        ax, ay = max(qx, 0.0), max(qy, 0.0)
        return -(math.hypot(ax, ay) + min(max(qx, qy), 0.0) - rx)


def _num(el: ET.Element, attr: str, default: float = 0.0) -> float:
    v = el.get(attr)
    if v is None:
        return default
    try:
        return float(re.sub(r"[^0-9.\-]", "", v) or default)
    except ValueError:
        return default


def parse_svg(svg_bytes: bytes) -> ET.ElementTree:
    return ET.ElementTree(ET.fromstring(svg_bytes))


def viewbox(tree: ET.ElementTree) -> tuple[float, float, float, float]:
    root = tree.getroot()
    vb = root.get("viewBox")
    if vb:
        parts = [float(p) for p in re.split(r"[\s,]+", vb.strip())]
        return parts[0], parts[1], parts[2], parts[3]
    w = _num(root, "width", 64.0)
    h = _num(root, "height", 64.0)
    return 0.0, 0.0, w, h


def text_elements(tree: ET.ElementTree) -> list[ET.Element]:
    return [el for el in tree.iter() if _local(el.tag) == "text"]


def element_text(el: ET.Element) -> str:
    return "".join(el.itertext())


def find_frame(tree: ET.ElementTree) -> Frame | None:
    """The frame is the largest filled circle/rect not inside <defs>."""
    best: Frame | None = None
    best_area = 0.0

    def walk(el: ET.Element, in_defs: bool):
        nonlocal best, best_area
        tag = _local(el.tag)
        now_in_defs = in_defs or tag == "defs"
        if not now_in_defs:
            fill = (el.get("fill") or "").strip().lower()
            if tag == "circle" and fill != "none":
                r = _num(el, "r")
                area = math.pi * r * r
                if area > best_area:
                    best_area = area
                    best = Frame("circle", cx=_num(el, "cx"), cy=_num(el, "cy"), r=r)
            elif tag == "rect" and fill != "none":
                w, h = _num(el, "width"), _num(el, "height")
                area = w * h
                if area > best_area:
                    best_area = area
                    best = Frame("rect", x=_num(el, "x"), y=_num(el, "y"),
                                 w=w, h=h, rx=_num(el, "rx"))
        for child in el:
            walk(child, now_in_defs)

    walk(tree.getroot(), False)
    return best


def _clone_without_text(tree: ET.ElementTree) -> bytes:
    import copy
    t = copy.deepcopy(tree)

    def strip(el: ET.Element):
        for child in list(el):
            if _local(child.tag) == "text":
                el.remove(child)
            else:
                strip(child)

    strip(t.getroot())
    return ET.tostring(t.getroot(), encoding="utf-8", xml_declaration=True)


def _clone_frame_only(tree: ET.ElementTree, frame: Frame) -> bytes:
    import copy
    t = copy.deepcopy(tree)
    root = t.getroot()
    target = None

    def hunt(el: ET.Element, in_defs: bool):
        nonlocal target
        tag = _local(el.tag)
        now = in_defs or tag == "defs"
        if not now and target is None:
            fill = (el.get("fill") or "").strip().lower()
            if frame.kind == "circle" and tag == "circle" and fill != "none" \
                    and _num(el, "r") == frame.r and _num(el, "cx") == frame.cx \
                    and _num(el, "cy") == frame.cy:
                target = el
            elif frame.kind == "rect" and tag == "rect" and fill != "none" \
                    and _num(el, "width") == frame.w and _num(el, "x") == frame.x \
                    and _num(el, "y") == frame.y:
                target = el
        for c in el:
            hunt(c, now)

    hunt(root, False)
    keep_defs = [c for c in root if _local(c.tag) == "defs"]
    for c in list(root):
        root.remove(c)
    for d in keep_defs:
        root.append(d)
    if target is not None:
        root.append(target)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def render(svg_bytes: bytes, width: int) -> np.ndarray:
    png = cairosvg.svg2png(bytestring=svg_bytes, output_width=width)
    img = Image.open(io.BytesIO(png)).convert("RGBA")
    return np.asarray(img).astype(np.int16)


def diff_mask(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return (np.abs(a - b).max(axis=2) > DIFF_THRESHOLD)


def core_mask(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return (np.abs(a - b).max(axis=2) > CORE_THRESHOLD)


def count_components(mask: np.ndarray, min_px: int = 2) -> int:
    """8-connected components with at least min_px pixels (small union-find)."""
    h, w = mask.shape
    parent = {}

    def find(p):
        while parent[p] != p:
            parent[p] = parent[parent[p]]
            p = parent[p]
        return p

    pts = [tuple(p) for p in np.argwhere(mask)]
    for p in pts:
        parent[p] = p
    for (y, x) in pts:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                q = (y + dy, x + dx)
                if q in parent:
                    ra, rb = find((y, x)), find(q)
                    if ra != rb:
                        parent[ra] = rb
    sizes: dict = {}
    for p in pts:
        r = find(p)
        sizes[r] = sizes.get(r, 0) + 1
    return sum(1 for s in sizes.values() if s >= min_px)


@dataclass
class SizeGrade:
    size: int
    status: str                     # legible | marginal | illegible | vanished
    cap_height_px: float = 0.0      # letterform core height at this size
    contrast: float = 0.0           # core text vs ground beneath it
    density: float = 0.0            # reserved
    gap_score: float = 0.0          # letter separability: components / characters


@dataclass
class GateResult:
    verdict: str = "FAIL"           # PASS | MARGINAL | FAIL
    reasons: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    grades: list[SizeGrade] = field(default_factory=list)


def effective_font_size(tree: ET.ElementTree, el: ET.Element) -> float | None:
    """The wordmark's font-size in viewBox units: the text element's own
    font-size (attribute or style), inherited from ancestors when unset,
    scaled by any ancestor transform. None when the source doesn't say."""
    parents = {c: p for p in tree.iter() for c in p}

    def own_font_size(node: ET.Element) -> float | None:
        v = node.get("font-size")
        if v is None and node.get("style"):
            m = re.search(r"font-size\s*:\s*([0-9.]+)", node.get("style"))
            v = m.group(1) if m else None
        if v is None:
            return None
        try:
            return float(re.sub(r"[^0-9.]", "", v))
        except ValueError:
            return None

    fs = None
    node: ET.Element | None = el
    scale = 1.0
    while node is not None:
        if fs is None:
            fs = own_font_size(node)
        tr = node.get("transform") or ""
        m = re.search(r"scale\(\s*([0-9.\-]+)", tr)
        if m:
            scale *= float(m.group(1))
        m = re.search(r"matrix\(\s*([0-9.\-]+)[ ,]+([0-9.\-]+)", tr)
        if m:
            scale *= math.hypot(float(m.group(1)), float(m.group(2)))
        node = parents.get(node)
    return fs * scale if fs is not None else None


def _grade_size(full: np.ndarray, notext: np.ndarray, frameonly: np.ndarray,
                size: int, cap_px: float, n_chars: int) -> SizeGrade:
    """Grade one render size.

    Legibility proxy (no OCR in the estate — stated, not hidden): the
    cap height the source's own font-size produces at this render size,
    gated on the letterform cores actually painting with real contrast
    against the ground beneath them. Letter separability is measured and
    reported but does not gate: at these sizes it tracks renderer font
    substitution more than human readability.
    """
    core = core_mask(full, notext)
    if not core.any():
        return SizeGrade(size, "vanished", cap_px, 0.0, 0.0, 0.0)

    def lum(arr: np.ndarray) -> np.ndarray:
        rgb = arr[:, :, :3].astype(np.float64)
        return 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]

    text_lum = float(lum(full)[core].mean())
    bg_lum = float(lum(frameonly)[core].mean())
    hi, lo = max(text_lum, bg_lum), min(text_lum, bg_lum)
    contrast = (hi + 12.75) / (lo + 12.75)  # WCAG-style ratio on 0..255 scale
    comp_score = min(count_components(core) / max(n_chars, 1), 1.0)

    if cap_px >= CAP_LEGIBLE[size] and contrast >= CONTRAST_LEGIBLE:
        status = "legible"
    elif size == 32 and cap_px >= CAP_MARGINAL_32 and contrast >= CONTRAST_MARGINAL:
        status = "marginal"
    else:
        status = "illegible"
    return SizeGrade(size, status, cap_px, contrast, 0.0, comp_score)


def check_icon(svg_bytes: bytes, name: str) -> tuple[GateResult, dict]:
    """Returns (result, renders) where renders maps size->PIL Image of the
    full icon (512/48/32) for the evidence sheet."""
    res = GateResult()
    renders: dict[int, Image.Image] = {}
    try:
        tree = parse_svg(svg_bytes)
    except ET.ParseError as e:
        res.reasons.append(f"unparseable SVG source: {e}")
        return res, renders

    vbx, vby, vbw, vbh = viewbox(tree)
    want = normalize_name(name)

    # 1 — wordmark present ---------------------------------------------------
    texts = text_elements(tree)
    found = None
    for el in texts:
        if want and want in normalize_name(element_text(el)):
            found = el
            break
    if not texts:
        res.reasons.append("no wordmark: the artwork carries no text element at all")
    elif found is None:
        seen = ", ".join(repr(element_text(el).strip()) for el in texts)
        res.reasons.append(f"wordmark missing: no text element spells {name!r} (found: {seen})")
    if res.reasons:
        return res, renders

    frame = find_frame(tree)
    if frame is None:
        res.reasons.append("no frame found: no filled disc/rounded-rect shape to seat the wordmark in")
        return res, renders
    frame_area = math.pi * frame.r ** 2 if frame.kind == "circle" else frame.w * frame.h
    if frame_area < 0.30 * vbw * vbh:
        res.reasons.append("frame too small relative to canvas to be the icon frame")
        return res, renders
    res.metrics["frame"] = f"{frame.kind} size={frame.size:.1f} on {vbw:.0f}x{vbh:.0f} viewBox"

    # renders ----------------------------------------------------------------
    notext_bytes = _clone_without_text(tree)
    frame_bytes = _clone_frame_only(tree, frame)
    full_g = render(svg_bytes, GEOMETRY_RENDER)
    notext_g = render(notext_bytes, GEOMETRY_RENDER)
    frame_g = render(frame_bytes, GEOMETRY_RENDER)
    for size in (512, 48, 32):
        png = cairosvg.svg2png(bytestring=svg_bytes, output_width=size)
        renders[size] = Image.open(io.BytesIO(png)).convert("RGBA")

    sx = GEOMETRY_RENDER / vbw
    sy = GEOMETRY_RENDER / vbh
    wmask = diff_mask(full_g, notext_g)
    gmask = diff_mask(notext_g, frame_g)
    if not wmask.any():
        res.reasons.append("wordmark paints nothing: text element renders empty")
        return res, renders

    # 2 — layout -------------------------------------------------------------
    ys, xs = np.where(wmask)
    step = max(1, len(xs) // 20000)
    dists = []
    outside = 0
    for px, py in zip(xs[::step], ys[::step]):
        d = frame.signed_distance(px / sx + vbx, py / sy + vby)
        dists.append(d)
        if d < 0:
            outside += 1
    outside_frac = outside / len(dists)
    min_margin = min(dists) if dists else 0.0
    res.metrics["rim_margin_units"] = round(min_margin, 2)
    res.metrics["outside_fraction"] = round(float(outside_frac), 4)
    if outside_frac > OUTSIDE_TOLERANCE:
        res.reasons.append(
            f"wordmark clipped by the rim: {outside_frac * 100:.1f}% of the name's "
            "painted pixels fall outside the frame")
    elif min_margin < MARGIN_MIN_FRAC * frame.size:
        res.reasons.append(
            f"wordmark bunched against the rim: margin {min_margin:.1f} units "
            f"< required {MARGIN_MIN_FRAC * frame.size:.1f} ({MARGIN_MIN_FRAC:.0%} of frame)")
    elif min_margin < MARGIN_NOTE_FRAC * frame.size:
        res.notes.append(
            f"wordmark seated close to the rim: margin {min_margin:.1f} units "
            f"({min_margin / frame.size:.1%} of frame) — inside, above the hard floor")

    wcore = core_mask(full_g, notext_g)
    gcore = core_mask(notext_g, frame_g)
    overlap = float((wcore & gcore).sum()) / float(wcore.sum()) if wcore.any() else 0.0
    res.metrics["glyph_overlap_fraction"] = round(overlap, 4)
    # Penetration separates a graze from an interleave: glyph cores that
    # only touch the wordmark band's edge (a bracket tip over a letter top)
    # are noted; glyph cores reaching into the band are the bunching failure.
    depth_frac = 0.0
    if wcore.any():
        ys0, xs0 = np.where(wcore)
        top, bot, left, right = int(ys0.min()), int(ys0.max()), int(xs0.min()), int(xs0.max())
        inside = gcore[top:bot + 1, left:right + 1]
        if inside.any():
            gy, gx = np.where(inside)
            depth = np.minimum(np.minimum(gy, (bot - top) - gy),
                               np.minimum(gx, (right - left) - gx))
            depth_frac = float(depth.max()) / float(bot - top + 1)
    res.metrics["glyph_penetration_fraction"] = round(depth_frac, 3)
    if overlap > OVERLAP_HARD or (overlap > OVERLAP_TOLERANCE and depth_frac > OVERLAP_DEPTH_FAIL):
        res.reasons.append(
            f"wordmark interleaved with the glyph artwork: {overlap * 100:.1f}% of the "
            f"name's letterform-core pixels sit on glyph-core pixels, penetrating "
            f"{depth_frac:.0%} of the cap height into the wordmark band")
    elif overlap > OVERLAP_TOLERANCE:
        res.notes.append(
            f"glyph grazes the wordmark band: {overlap * 100:.1f}% core overlap at "
            f"{depth_frac:.0%} of cap height penetration — edge contact, not interleaving")

    # 3 — legibility at size ---------------------------------------------------
    fs = effective_font_size(tree, found)
    if fs is not None:
        cap_units = fs * CAP_RATIO
        res.metrics["cap_height_units"] = round(cap_units, 2)
    else:
        # Source doesn't state a font-size: fall back to the rendered core
        # height at geometry scale (renderer-dependent — noted, not hidden).
        rows_g = np.where(wcore.any(axis=1))[0]
        cap_units = float(rows_g.max() - rows_g.min() + 1) / sy if len(rows_g) else 0.0
        res.notes.append("font-size not stated in source; cap height measured from the render")
    for size in (48, 32):
        full_s = render(svg_bytes, size)
        notext_s = render(notext_bytes, size)
        frame_s = render(frame_bytes, size)
        cap_px = cap_units * size / vbw
        grade = _grade_size(full_s, notext_s, frame_s, size, cap_px, len(want))
        res.grades.append(grade)
        res.metrics[f"cap_height_{size}px"] = round(grade.cap_height_px, 2)
        res.metrics[f"contrast_{size}px"] = round(grade.contrast, 2)

    g48, g32 = res.grades
    if g48.status in ("illegible", "vanished"):
        res.reasons.append(
            f"wordmark illegible at 48px (cap height {g48.cap_height_px:.1f}px, "
            f"contrast {g48.contrast:.1f}, status {g48.status})")
    if g32.status in ("illegible", "vanished"):
        res.reasons.append(
            f"wordmark illegible at 32px (cap height {g32.cap_height_px:.1f}px, "
            f"contrast {g32.contrast:.1f}, status {g32.status})")

    if res.reasons:
        res.verdict = "FAIL"
    elif g32.status == "marginal":
        res.verdict = "MARGINAL"
        res.notes.append(
            "legible at 48px, marginal at 32px — allowed only with this note on record")
    else:
        res.verdict = "PASS"
    return res, renders


def render_sheet(renders: dict[int, Image.Image], verdict: str, label: str) -> Image.Image:
    """Evidence sheet: 512 render + 48px and 32px renders shown at actual
    relative scale (nearest-neighbour upscale for visibility)."""
    W, H = 760, 300
    sheet = Image.new("RGBA", (W, H), (24, 24, 28, 255))
    if 512 in renders:
        sheet.alpha_composite(renders[512].resize((256, 256)), (16, 28))
    if 48 in renders:
        sheet.alpha_composite(renders[48].resize((192, 192), Image.NEAREST), (300, 28))
    if 32 in renders:
        sheet.alpha_composite(renders[32].resize((192, 192), Image.NEAREST), (520, 28))
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    d.text((16, 8), f"{label} - Icongate {verdict}", fill=(255, 255, 255, 255))
    d.text((300, 228), "48px (x4)", fill=(200, 200, 200, 255))
    d.text((520, 228), "32px (x6)", fill=(200, 200, 200, 255))
    d.text((16, 228), "512px render (shown 256)", fill=(200, 200, 200, 255))
    return sheet
