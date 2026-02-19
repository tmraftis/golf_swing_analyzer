"""Generate branded 1080×1080 share images using Pillow.

Design: minimal, dark, premium feel.  Optimised for Instagram / X / iMessage.

Layout (1080×1080):
  ┌──────────────────────────────────┐
  │  [logo]  PURE         swingpure  │  48px  top bar
  ├──────────────┬───────────────────┤
  │              │                   │
  │  User frame  │  Tiger frame      │  540px side-by-side
  │       YOU ▸  │  ◂ TIGER          │
  ├──────────────┴───────────────────┤
  │                                  │
  │        ── 83 ──                  │
  │     similarity / 100             │  180px score section
  │     Down the Line · Impact       │
  │                                  │
  ├──────────────────────────────────┤
  │  #1 Spine +7.2°  #2 Arm +10.0°  │  252px differences
  │  #3 Elbow +10.0°                 │  (horizontal list)
  ├──────────────────────────────────┤
  │  Swing pure.          swingpure  │  60px footer
  └──────────────────────────────────┘
"""

import logging
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# ── Brand palette ────────────────────────────────────────
BG       = (2, 27, 34)        # Blue Charcoal — base
BG_CARD  = (8, 36, 44)        # slightly lighter for cards
CREAM    = (246, 241, 229)
CREAM70  = (200, 196, 188)    # 70 %
CREAM45  = (140, 137, 132)    # 45 %
CREAM20  = (60, 58, 56)       # 20 %
GREEN    = (46, 91, 59)       # Forest Green
GREEN_BR = (88, 180, 112)     # bright green for the arc
YELLOW   = (244, 215, 106)
RED      = (197, 58, 58)

# ── Canvas ───────────────────────────────────────────────
# Render at 2× for Retina-quality anti-aliasing, downscale at the end.
_S         = 2                            # supersampling factor
W, H       = 1080 * _S, 1080 * _S
TOP_H      = 48 * _S
FRAMES_H   = 640 * _S
FOOTER_H   = 60 * _S
SCORE_H    = H - TOP_H - FRAMES_H - FOOTER_H

# ── Assets ───────────────────────────────────────────────
# Resolve project root by searching upward for the assets directory.
# Locally: image_generator.py is at backend/app/pipeline/ → root is 4 parents up.
# Docker:  image_generator.py is at /app/app/pipeline/   → root is 3 parents up
#          (because backend/ is copied into /app/).
def _find_root() -> Path:
    p = Path(__file__).resolve().parent
    for _ in range(6):
        if (p / "assets" / "fonts").is_dir():
            return p
        p = p.parent
    return Path(__file__).resolve().parent.parent.parent.parent  # fallback

_ROOT = _find_root()
_LOGO = _ROOT / "assets" / "pure-logo-light.png"
_LOGO_FALLBACK = _ROOT / "assets" / "pure-logo.jpeg"
_FONT = _ROOT / "assets" / "fonts" / "Inter-Variable.ttf"

# ── Font cache ───────────────────────────────────────────
_fcache: dict[tuple, ImageFont.FreeTypeFont] = {}

def _f(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load Inter variable font with correct optical-size and weight axes.

    Inter's variation axes: [optical_size (14-32), weight (100-900)].
    Optical size should scale with point size — larger text gets higher
    optical size for tighter, crisper letterforms.
    """
    key = (size, bold)
    if key not in _fcache:
        try:
            f = ImageFont.truetype(str(_FONT), size)
            # Map font size → optical size (14=body, 32=display)
            opsz = min(32, max(14, size))
            weight = 700 if bold else 400
            try:
                f.set_variation_by_axes([opsz, weight])
            except Exception:
                pass
            _fcache[key] = f
        except Exception:
            _fcache[key] = ImageFont.load_default()
    return _fcache[key]


def _logo(h: int) -> Image.Image:
    """Load the cream-on-transparent logo, falling back to original."""
    for path in [_LOGO, _LOGO_FALLBACK]:
        try:
            img = Image.open(path).convert("RGBA")
            ratio = h / img.height
            return img.resize((int(img.width * ratio), h), Image.Resampling.LANCZOS)
        except Exception:
            continue
    return Image.new("RGBA", (h, h), (0, 0, 0, 0))


def _fit(img: Image.Image, tw: int, th: int) -> Image.Image:
    img = img.convert("RGB")
    s = max(tw / img.width, th / img.height)
    nw, nh = int(img.width * s), int(img.height * s)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    l, t = (nw - tw) // 2, (nh - th) // 2
    return img.crop((l, t, l + tw, t + th))


def _cx(draw: ImageDraw.ImageDraw, text: str, y: int, font, fill, w: int = W):
    """Draw centred text."""
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text(((w - (bb[2] - bb[0])) // 2, y), text, fill=fill, font=font)


def _right(draw: ImageDraw.ImageDraw, text: str, y: int, font, fill, margin: int = 0):
    if margin == 0:
        margin = 32 * _S
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text((W - (bb[2] - bb[0]) - margin, y), text, fill=fill, font=font)


def _sev_color(s: str) -> tuple:
    return {"major": RED, "moderate": YELLOW, "minor": CREAM70}.get(s, CREAM70)


def _vgradient(canvas: Image.Image, y0: int, h: int, c1: tuple, c2: tuple):
    """Vertical linear gradient fill."""
    draw = ImageDraw.Draw(canvas)
    for r in range(h):
        t = r / max(h - 1, 1)
        c = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        draw.line([(0, y0 + r), (W, y0 + r)], fill=c)


def _bottom_fade(canvas: Image.Image, x: int, y: int, fw: int, fh: int, fade_h: int = 100):
    """Draw a bottom-to-top dark gradient overlay for label readability."""
    overlay = Image.new("RGBA", (fw, fade_h), (0, 0, 0, 0))
    for row in range(fade_h):
        a = int(200 * (row / (fade_h - 1)))
        ImageDraw.Draw(overlay).line([(0, row), (fw, row)], fill=(*BG, a))
    canvas.paste(overlay, (x, y + fh - fade_h), overlay)


# ── Score ring ───────────────────────────────────────────

def _draw_ring(canvas: Image.Image, cx: int, cy: int, r: int, score: int, show_percent: bool = False):
    """Draw a smooth anti-aliased score ring with number in centre.

    To avoid alpha-fringe ("bleed") that occurs when downscaling an RGBA
    layer, we render the ring graphics on an **opaque** tile whose
    background matches the canvas, and build a separate alpha mask.
    Both are downscaled independently, then composited onto the canvas.
    Score text is rendered directly on the main canvas.
    """
    import math

    SCALE = 4                            # ring-internal supersample (canvas is already 2×)
    stroke = 4 * _S                      # visual stroke scales with canvas
    big_stroke = stroke * SCALE
    half_s = big_stroke / 2.0
    pad = stroke + 6                     # padding around the ring
    sz = (r + pad) * 2
    big_sz = sz * SCALE
    big_r = r * SCALE
    big_c = big_sz / 2.0
    bbox_i = [
        (int(big_c - big_r), int(big_c - big_r)),
        (int(big_c + big_r), int(big_c + big_r)),
    ]

    # --- Colour layer (RGB, opaque, BG-coloured) ---
    # Sample the background colour from the canvas at the ring centre
    bg_sample = canvas.getpixel((cx, cy))[:3]
    colour_big = Image.new("RGB", (big_sz, big_sz), bg_sample)
    dc = ImageDraw.Draw(colour_big)

    # --- Mask layer (L, white = visible) ---
    mask_big = Image.new("L", (big_sz, big_sz), 0)
    dm = ImageDraw.Draw(mask_big)

    # Track — full circle, subtle
    track_alpha = 50
    track_rgb = tuple(
        int(bg_sample[i] + (CREAM20[i] - bg_sample[i]) * track_alpha / 255)
        for i in range(3)
    )
    dc.ellipse(bbox_i, outline=track_rgb, width=big_stroke)
    dm.ellipse(bbox_i, outline=track_alpha, width=big_stroke)

    # Progress arc — bright green, from 12-o'clock clockwise
    frac = min(score, 100) / 100.0
    sweep = 360.0 * frac
    if sweep > 0:
        dc.arc(bbox_i, start=-90, end=-90 + sweep,
               fill=GREEN_BR, width=big_stroke)
        dm.arc(bbox_i, start=-90, end=-90 + sweep,
               fill=255, width=big_stroke)

        # Note: endcaps removed — the arc with big_stroke width is clean enough
        # after supersampling. Manually drawn cap circles were misaligning.

    # Downscale both layers independently
    colour = colour_big.resize((sz, sz), Image.Resampling.LANCZOS)
    mask = mask_big.resize((sz, sz), Image.Resampling.LANCZOS)

    # Paste ring onto canvas using the mask
    paste_x = cx - sz // 2
    paste_y = cy - sz // 2
    canvas.paste(colour, (paste_x, paste_y), mask)

    # Score text — drawn directly on the opaque canvas for crisp rendering
    draw = ImageDraw.Draw(canvas)
    if show_percent:
        # "83" large + "%" smaller, laid out as a single centred block
        f_num = _f(48 * _S, bold=True)
        f_pct = _f(24 * _S, bold=True)
        num_str = str(score)
        pct_str = "%"
        bb_n = draw.textbbox((0, 0), num_str, font=f_num)
        bb_p = draw.textbbox((0, 0), pct_str, font=f_pct)
        num_w = bb_n[2] - bb_n[0]
        pct_w = bb_p[2] - bb_p[0]
        gap_px = 2 * _S
        total_w = num_w + gap_px + pct_w
        num_h = bb_n[3] - bb_n[1]
        # Centre the combined block
        num_x = cx - total_w // 2
        num_y = cy - num_h // 2 - bb_n[1]
        draw.text((num_x, num_y), num_str, fill=CREAM, font=f_num)
        # Align % baseline with number baseline
        pct_y = num_y + (bb_n[3] - bb_n[1]) - (bb_p[3] - bb_p[1])
        draw.text((num_x + num_w + gap_px, pct_y), pct_str, fill=CREAM45, font=f_pct)
    else:
        f_num = _f(54 * _S, bold=True)
        score_str = str(score)
        bb = draw.textbbox((0, 0), score_str, font=f_num)
        tw = bb[2] - bb[0]
        glyph_h = bb[3] - bb[1]
        text_x = cx - tw // 2
        text_y = cy - glyph_h // 2 - bb[1]
        draw.text((text_x, text_y), score_str, fill=CREAM, font=f_num)


# ── Public API ───────────────────────────────────────────

def _draw_card_column(
    draw: ImageDraw.ImageDraw,
    items: list[dict],
    header_text: str,
    x: int,
    y0: int,
    w: int,
    row_h: int,
    row_gap: int,
    accent_color: tuple,
    show_delta: bool = True,
):
    """Draw a vertical stack of compact card rows with a header label.

    Shared renderer for both similarities and differences columns.
    """
    S = _S
    header_h = 22 * S
    header_gap = 8 * S

    # Header
    draw.text(
        (x, y0),
        header_text,
        fill=CREAM70,
        font=_f(11 * S, bold=True),
    )

    row_y = y0 + header_h + header_gap
    for i, item in enumerate(items):
        ry = row_y + i * (row_h + row_gap)

        # Subtle card background
        draw.rounded_rectangle(
            [(x, ry), (x + w, ry + row_h)],
            radius=8 * S,
            fill=BG_CARD,
        )

        # Accent dot — severity-based for diffs, fixed green for sims
        if show_delta:
            dot_color = _sev_color(item.get("severity", "minor"))
        else:
            dot_color = accent_color
        dot_r = 3 * S
        draw.ellipse(
            [
                (x + 10 * S, ry + row_h // 2 - dot_r),
                (x + 10 * S + dot_r * 2, ry + row_h // 2 + dot_r),
            ],
            fill=dot_color,
        )

        # Title + phase — pixel-aware truncation
        title = item.get("title", item.get("angle_name", ""))
        f_title = _f(12 * S, bold=True)
        max_title_w = w - 22 * S - 10 * S   # full width minus padding
        bb_t = draw.textbbox((0, 0), title, font=f_title)
        if (bb_t[2] - bb_t[0]) > max_title_w:
            while len(title) > 5 and draw.textbbox((0, 0), title + "\u2026", font=f_title)[2] > max_title_w:
                title = title[:-1]
            title = title.rstrip() + "\u2026"
        draw.text(
            (x + 22 * S, ry + 6 * S),
            title,
            fill=CREAM,
            font=f_title,
        )
        phase = item.get("phase", "").replace("_", " ").title()
        draw.text(
            (x + 22 * S, ry + 26 * S),
            phase,
            fill=CREAM20,
            font=_f(9 * S),
        )

        # Severity badge on the right (no angle values)
        if show_delta:
            severity = item.get("severity", "minor")
            badge_text = severity.upper()
            f_badge = _f(8 * S, bold=True)
            badge_color = _sev_color(severity)
            bb_b = draw.textbbox((0, 0), badge_text, font=f_badge)
            tw_b = bb_b[2] - bb_b[0]
            draw.text(
                (x + w - tw_b - 10 * S, ry + (row_h - (bb_b[3] - bb_b[1])) // 2),
                badge_text,
                fill=badge_color,
                font=f_badge,
            )


def generate(
    similarity_score: int,
    top_differences: list[dict],
    top_similarities: list[dict] | None = None,
    user_phase_image_path: str | None = None,
    ref_phase_image_path: str | None = None,
    view_label: str = "Down the Line",
) -> bytes:
    """Produce a 1080×1080 branded PNG and return the bytes.

    Internally renders at 2× (2160×2160) for Retina-quality text and
    line rendering, then downscales to 1080×1080 with Lanczos.
    """
    S = _S  # shorthand for the scale factor
    if top_similarities is None:
        top_similarities = []

    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)
    y = 0

    # ── TOP BAR ──────────────────────────────────────────
    logo = _logo(24 * S)
    canvas.paste(logo, (32 * S, (TOP_H - logo.height) // 2), logo)
    # "SWING" in yellow + "PURE" in cream
    brand_x = 32 * S + logo.width + 10 * S
    brand_y = (TOP_H - 16 * S) // 2
    f_brand = _f(16 * S, bold=True)
    draw.text((brand_x, brand_y), "SWING", fill=YELLOW, font=f_brand)
    swing_bb = draw.textbbox((brand_x, brand_y), "SWING", font=f_brand)
    draw.text((swing_bb[2] + 5 * S, brand_y), "PURE", fill=CREAM, font=f_brand)
    _right(draw, "swingpure.ai", (TOP_H - 12 * S) // 2, _f(12 * S), CREAM45)
    draw.line([(32 * S, TOP_H - 1), (W - 32 * S, TOP_H - 1)], fill=CREAM20, width=max(1, S // 2))
    y = TOP_H

    # ── FRAMES ───────────────────────────────────────────
    gap = 4 * S
    fw = (W - gap) // 2

    def _load(path, label):
        if path and Path(path).exists():
            return _fit(Image.open(path), fw, FRAMES_H)
        p = Image.new("RGB", (fw, FRAMES_H), (14, 26, 30))
        d = ImageDraw.Draw(p)
        bb = d.textbbox((0, 0), label, font=_f(20 * S))
        tw = bb[2] - bb[0]
        d.text(((fw - tw) // 2, FRAMES_H // 2 - 12 * S), label, fill=CREAM20, font=_f(20 * S))
        return p

    uf = _load(user_phase_image_path, "Your Swing")
    rf = _load(ref_phase_image_path, "Tiger Woods")

    canvas.paste(uf, (0, y))
    canvas.paste(rf, (fw + gap, y))

    # Gap
    draw.rectangle([(fw, y), (fw + gap, y + FRAMES_H)], fill=BG)

    # Gradient overlays for labels
    _bottom_fade(canvas, 0, y, fw, FRAMES_H, 90 * S)
    _bottom_fade(canvas, fw + gap, y, fw, FRAMES_H, 90 * S)

    # Labels
    draw.text((16 * S, y + FRAMES_H - 28 * S), "YOU", fill=CREAM, font=_f(12 * S, bold=True))
    draw.text((fw + gap + 16 * S, y + FRAMES_H - 28 * S), "TIGER", fill=CREAM, font=_f(12 * S, bold=True))

    y += FRAMES_H

    # ── SCORE SECTION ────────────────────────────────────
    # 3-column layout: [ring] [similarities] [differences]
    _vgradient(canvas, y, SCORE_H, (8, 40, 48), BG)

    # Thin top rule
    draw.line([(32 * S, y), (W - 32 * S, y)], fill=CREAM20, width=max(1, S // 2))

    margin = 32 * S
    col_gap = 12 * S                     # gap between card columns

    # Card columns: fixed width, right-aligned
    card_col_w = 310 * S                 # ~310px at 1× per column
    cards_total_w = card_col_w * 2 + col_gap
    diff_x = W - margin - card_col_w                      # rightmost column
    sim_x = diff_x - col_gap - card_col_w                 # middle column

    # Column 1: Score ring — centred in the remaining left space
    ring_r = 52 * S
    ring_left_space = sim_x - col_gap    # space from left edge to start of sim column
    ring_cx = ring_left_space // 2       # centred in that space
    ring_cy = y + SCORE_H // 2 - 8 * S

    # Shared row sizing (needed early for score card height)
    row_h = 48 * S
    row_gap = 6 * S

    sims = top_similarities[:3]
    diffs = top_differences[:3]

    # Compute vertical centering based on the taller column
    header_h = 22 * S
    header_gap = 8 * S
    max_n = max(len(sims), len(diffs), 1)
    block_h = header_h + header_gap + max_n * row_h + (max_n - 1) * row_gap
    block_y0 = y + (SCORE_H - block_h) // 2

    # Score card background — same vertical extent as the card columns
    score_card_x = margin
    score_card_w = sim_x - col_gap - margin
    draw.rounded_rectangle(
        [(score_card_x, block_y0), (score_card_x + score_card_w, block_y0 + block_h)],
        radius=8 * S,
        fill=BG_CARD,
    )

    # "Similarity" header — top-left of card, matching other column headers
    draw.text(
        (score_card_x + 14 * S, block_y0 + 10 * S),
        "Similarity",
        fill=CREAM70,
        font=_f(11 * S, bold=True),
    )

    # Centre the ring in the card area below the header
    ring_area_top = block_y0 + header_h + header_gap
    ring_area_h = block_h - header_h - header_gap
    ring_cx = score_card_x + score_card_w // 2
    ring_cy = ring_area_top + ring_area_h // 2
    _draw_ring(canvas, ring_cx, ring_cy, ring_r, similarity_score, show_percent=True)

    # Column 2: Similarities
    if sims:
        _draw_card_column(
            draw, sims,
            header_text="Matching Tiger",
            x=sim_x, y0=block_y0, w=card_col_w,
            row_h=row_h, row_gap=row_gap,
            accent_color=GREEN_BR,
            show_delta=False,
        )

    # Column 3: Differences
    if diffs:
        _draw_card_column(
            draw, diffs,
            header_text="Work on",
            x=diff_x, y0=block_y0, w=card_col_w,
            row_h=row_h, row_gap=row_gap,
            accent_color=RED,
            show_delta=True,
        )
    else:
        # No diffs — show encouraging message
        msg_y = y + SCORE_H // 2 - 12 * S
        draw.text(
            (diff_x, msg_y),
            "Great swing! \U0001f3cc\ufe0f",
            fill=CREAM70,
            font=_f(20 * S, bold=True),
        )

    y += SCORE_H

    # ── FOOTER ───────────────────────────────────────────
    draw.line([(32 * S, y + S), (W - 32 * S, y + S)], fill=CREAM20, width=max(1, S // 2))

    # "Swing" in yellow + "pure" in cream
    footer_y = y + (FOOTER_H - 13 * S) // 2
    f_footer = _f(13 * S, bold=True)
    draw.text((32 * S, footer_y), "Swing", fill=YELLOW, font=f_footer)
    swing_bb_f = draw.textbbox((32 * S, footer_y), "Swing", font=f_footer)
    draw.text((swing_bb_f[2] + 5 * S, footer_y), "pure", fill=CREAM45, font=f_footer)
    _right(draw, "swingpure.ai", y + (FOOTER_H - 12 * S) // 2, _f(12 * S), CREAM45)

    # Small logo watermark near the right text
    wm = _logo(16 * S)
    if wm.mode == "RGBA":
        a = wm.split()[3].point(lambda p: int(p * 0.35))
        wm.putalpha(a)
    wm_x = W - 32 * S - wm.width - 84 * S
    canvas.paste(wm, (wm_x, y + (FOOTER_H - wm.height) // 2), wm)

    # ── Downscale 2× → 1080×1080 ────────────────────────
    if _S > 1:
        canvas = canvas.resize((1080, 1080), Image.Resampling.LANCZOS)

    # ── Encode ───────────────────────────────────────────
    buf = BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()
