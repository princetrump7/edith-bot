#!/usr/bin/env python3
"""
Mira Bot — 6 Premium Telegram Mini App Screens

Design System (Telegram Dark Aesthetic):
  • Background: #0A0A14 (deep navy/black)
  • Cards: #16162A, #1A1A2E
  • Accent: #00A3FF (bright blue)
  • Text: white primary, gray secondary (#8E8E9A)
  • Rounded corners: 12-20px, card shadows
  • Multicolor swirl logo (orange→pink→purple→cyan)

Exact pixel-level recreation of all 6 screens from spec.

Output: 6x PNG files in screens/assets/
"""

from __future__ import annotations

import math
import os
import logging
from typing import Tuple, Optional, List

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# ─── Constants ──────────────────────────────────────────────────────────────
W, H = 414, 896  # mobile frame (iPhone 14 Pro size)
BG = "#0A0A14"
BG2 = "#12121E"
BG3 = "#1A1A2E"
CARD = "#16162A"
CARD2 = "#1E1E34"
CARD3 = "#22223A"
ACCENT = "#00A3FF"
ACCENT_DIM = "#007ACC"
ACCENT_GLOW = "#0055AA"
WHITE = "#FFFFFF"
GRAY = "#8E8E9A"
GRAY2 = "#6B6B7D"
GRAY3 = "#44445A"
GRAY4 = "#2A2A44"
GREEN = "#00E676"
LIGHT_GREEN = "#8BC34A"
LIGHT_GREEN_GRAD_TOP = "#AEE87C"
LIGHT_GREEN_GRAD_BOT = "#6D9F3A"
PURPLE_HEADER = "#7C4DFF"
GOLD = "#FFD700"

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# ─── Font cache ────────────────────────────────────────────────────────────
_FONTS: dict = {}

def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get a system font at the given size, with fallback."""
    key = (size, bold)
    if key in _FONTS:
        return _FONTS[key]
    paths = [
        ("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        ("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        ("C:/Windows/Fonts/seguiemj.ttf", False),  # emoji fallback
    ]
    for path in paths:
        if isinstance(path, tuple):
            p, _ = path
        else:
            p = path
        try:
            f = ImageFont.truetype(p, size)
            _FONTS[key] = f
            return f
        except (IOError, OSError):
            continue
    _FONTS[key] = ImageFont.load_default()
    return _FONTS[key]

def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return get_font(size, bold)

# ─── Drawing primitives ────────────────────────────────────────────────────

def rr(draw: ImageDraw.ImageDraw, xy: Tuple[int, int, int, int], r: int,
       fill: Optional[str] = None, outline: Optional[str] = None,
       width: int = 1) -> None:
    """Rounded rectangle."""
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)

def circle(draw: ImageDraw.ImageDraw, xy: Tuple[int, int, int, int],
           fill: Optional[str] = None, outline: Optional[str] = None,
           width: int = 1) -> None:
    draw.ellipse(xy, fill=fill, outline=outline, width=width)

def gradient_v(draw: ImageDraw.ImageDraw, xy: Tuple[int, int, int, int],
               top_color: str, bot_color: str) -> None:
    """Draw a vertical linear gradient from top_color to bot_color."""
    x0, y0, x1, y1 = xy
    steps = y1 - y0
    if steps <= 0:
        return
    r1, g1, b1 = int(top_color[1:3],16), int(top_color[3:5],16), int(top_color[5:7],16)
    r2, g2, b2 = int(bot_color[1:3],16), int(bot_color[3:5],16), int(bot_color[5:7],16)
    for i in range(steps):
        t = i / max(steps - 1, 1)
        r = int(r1*(1-t) + r2*t)
        g = int(g1*(1-t) + g2*t)
        b = int(b1*(1-t) + b2*t)
        draw.line([(x0, y0+i), (x1-1, y0+i)], fill=(r, g, b))

# ─── Text helpers ──────────────────────────────────────────────────────────

def tw(draw: ImageDraw.ImageDraw, text: str, size: int = 14,
       bold: bool = False) -> int:
    """Return text width."""
    f = font(size, bold)
    bb = draw.textbbox((0, 0), text, font=f)
    return bb[2] - bb[0]

def text(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], txt: str,
         color: str = WHITE, size: int = 14, bold: bool = False,
         anchor: str = "la", align: str = "left") -> None:
    f = font(size, bold)
    draw.text(xy, txt, fill=color, font=f, anchor=anchor, align=align)

def text_center(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], txt: str,
                color: str = WHITE, size: int = 14, bold: bool = False) -> None:
    f = font(size, bold)
    bb = draw.textbbox((0, 0), txt, font=f)
    x, y = xy
    draw.text((x - (bb[2]-bb[0])//2, y), txt, fill=color, font=f, anchor="la")

# ─── UI Components ─────────────────────────────────────────────────────────

def status_bar(draw: ImageDraw.ImageDraw, time_str: str = "1:32 AM",
               battery_pct: int = 65, charging: bool = False) -> None:
    """Android-style status bar with time, network icons, battery."""
    # Time
    text(draw, (20, 14), time_str, WHITE, 13, bold=True)

    # Signal bars (4 bars of increasing height)
    for i in range(4):
        bh = 4 + i * 2
        rr(draw, [W - 128 + i * 3, 28 - bh, W - 125 + i * 3, 27], 1, fill=WHITE)

    # Battery outline
    bx, by = W - 105, 16
    rr(draw, [bx, by, bx + 22, by + 12], 3, outline=WHITE, width=1)
    draw.rectangle([bx + 23, by + 3, bx + 25, by + 9], fill=WHITE)

    # Battery fill (proportional)
    bw = max(1, int(18 * battery_pct / 100))
    fill_inside = ACCENT if charging else WHITE
    rr(draw, [bx + 2, by + 2, bx + 2 + bw, by + 10], 2, fill=fill_inside)

    # Battery percentage + charging indicator
    suffix = " ⚡" if charging else ""
    label_w = tw(draw, f"{battery_pct}%{suffix}", 9)
    text(draw, (bx - label_w - 4, by + 1), f"{battery_pct}%{suffix}", GRAY, 9)


def bottom_nav(draw: ImageDraw.ImageDraw, active_tab: str = "Links") -> None:
    """Android 3-button nav bar + bottom tabs."""
    # Nav bar background
    draw.rectangle([0, H - 48, W, H], fill="#000000")
    # Nav buttons: back (triangle), home (circle), recents (square)
    cx = [W // 3, W // 2, 2 * W // 3]
    draw.polygon([(cx[0] - 7, H - 26), (cx[0], H - 32), (cx[0], H - 20)], fill=GRAY2)
    circle(draw, [cx[1] - 5, H - 31, cx[1] + 5, H - 21], outline=GRAY2, width=2)
    draw.rectangle([cx[2] - 6, H - 32, cx[2] + 6, H - 20], outline=GRAY2, width=2)

    # Tabs background
    draw.rectangle([0, H - 100, W, H - 48], fill=CARD)
    draw.line([0, H - 100, W, H - 100], fill=GRAY3, width=1)

    tabs_list = [("🏠", "Home"), ("🔗", "Links"), ("🤖", "Similar Bots"), ("⚙️", "Settings")]
    tw_tab = W / len(tabs_list)
    for i, (icon, label) in enumerate(tabs_list):
        xc = int(tw_tab * i + tw_tab / 2)
        col = ACCENT if label == active_tab else GRAY
        text_center(draw, (xc, H - 86), icon, col, 16)
        text_center(draw, (xc, H - 65), label, col, 10, bold=(label == active_tab))
        if label == active_tab:
            circle(draw, [xc - 4, H - 48, xc + 4, H - 40], fill=ACCENT)


def draw_telegram_logo(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int) -> None:
    """Minimal Telegram paper-plane logo."""
    # Plane body
    pts = [(cx, cy - r), (cx - r, cy + r // 2), (cx - r // 3, cy + r // 3),
           (cx + r // 3, cy + r), (cx + r, cy)]
    # Simplified: draw circle with accent and a smaller circle inside
    circle(draw, [cx - r, cy - r, cx + r, cy + r], fill="#0088CC")
    circle(draw, [cx - r + 4, cy - r + 4, cx + r - 4, cy + r - 4], fill=ACCENT)
    # Paper plane
    pp = [
        (cx - 2, cy - 2),
        (cx + 6, cy + 5),
        (cx - 3, cy + 1),
        (cx - 8, cy + 5),
    ]
    draw.polygon(pp, fill=WHITE)


def draw_swirl_logo(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int,
                    with_badge: bool = False) -> None:
    """Multicolor gradient spiral logo: orange → pink → purple → cyan/blue.

    Draws a smooth spiral with color interpolation along its length,
    then a white center circle and optional GPT-5 badge.
    """
    # Spiral colors in gradient order
    colors = [
        (255, 120, 0),    # orange
        (255, 50, 150),   # pink
        (150, 50, 255),   # purple
        (0, 180, 255),    # cyan/blue
    ]

    # Generate spiral points
    steps = 250
    pts: List[Tuple[float, float]] = []
    for i in range(steps):
        t = i / steps
        angle = t * 7 * math.pi  # 3.5 turns
        radius = r * (0.08 + 0.92 * t)
        pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))

    # Draw spiral with per-segment color interpolation
    seg = 6
    for i in range(0, len(pts) - seg, 2):
        seg_t = i / max(len(pts) - 1, 1)
        ci = min(int(seg_t * (len(colors) - 1)), len(colors) - 2)
        lt = (seg_t * (len(colors) - 1)) - ci
        rc = int(colors[ci][0] * (1 - lt) + colors[ci + 1][0] * lt)
        gc = int(colors[ci][1] * (1 - lt) + colors[ci + 1][1] * lt)
        bc = int(colors[ci][2] * (1 - lt) + colors[ci + 1][2] * lt)
        for j in range(seg):
            if i + j < len(pts) - 1:
                draw.line([pts[i + j], pts[i + j + 1]], fill=(rc, gc, bc), width=3)

    # Outer glow ring (faint)
    circle(draw, [cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6],
           outline="#00A3FF40", width=2)

    # White center circle
    cr = max(5, r // 5)
    circle(draw, [cx - cr, cy - cr, cx + cr, cy + cr], fill=WHITE)

    if with_badge:
        # GPT-5 badge at bottom-right of logo
        bx, by = cx + r - 12, cy + r - 14
        bw, bh = 44, 18
        rr(draw, [bx - bw // 2, by - bh // 2, bx + bw // 2, by + bh // 2],
           9, fill=ACCENT)
        text_center(draw, (bx, by + 1), "GPT-5", WHITE, 9, bold=True)


# ─── Screen 1: Bot Profile Page ────────────────────────────────────────────

def screen_1() -> Image.Image:
    """Bot Profile Page — top with logo, stats, action buttons, bio, CTA."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Status bar
    status_bar(draw, "1:32 AM", 18, charging=True)

    # Large central swirl logo
    draw_swirl_logo(draw, W // 2, 140, 65, with_badge=True)

    # Title
    text_center(draw, (W // 2, 228), "GPT | GPT Image 2 | Midjourney Ch", WHITE, 15, bold=True)

    # Subtitle — monthly users
    text_center(draw, (W // 2, 252), "359,035 monthly users", GRAY, 12)

    # Action buttons row (4 buttons)
    btn_y = 278
    btn_w, btn_h = 56, 46
    btn_r = 14
    gap = 14
    total_w = 4 * btn_w + 3 * gap
    start_x = (W - total_w) // 2

    actions = [
        ("💬", "Message"),
        ("🔇", "Mute"),
        ("📤", "Share"),
        ("⏹", "Stop"),
    ]
    for i, (icon, label) in enumerate(actions):
        x = start_x + i * (btn_w + gap)
        rr(draw, [x, btn_y, x + btn_w, btn_y + btn_h], btn_r, fill=CARD)
        text_center(draw, (x + btn_w // 2, btn_y + 10), icon, WHITE, 18)
        text_center(draw, (x + btn_w // 2, btn_y + 34), label, GRAY, 8)

    # Bio card
    bio_y = btn_y + btn_h + 18
    rr(draw, [20, bio_y, W - 20, bio_y + 70], 16, fill=CARD)
    text(draw, (34, bio_y + 12),
         "The all-in-one AI bot: ChatGPT, Claude, Gemini,", GRAY, 11)
    text(draw, (34, bio_y + 28),
         "DeepSeek, Midjourney, etc. Join us: @perplexity", GRAY, 11)
    text(draw, (34, bio_y + 46), "@chatcom", ACCENT, 11, bold=True)
    text(draw, (172, bio_y + 46), "(also @GPT5Tbot)", GRAY, 10)

    # Open App button
    oa_y = bio_y + 90
    rr(draw, [40, oa_y, W - 40, oa_y + 54], 16, fill=ACCENT)
    # Inner glow via slight lighter border
    rr(draw, [42, oa_y + 2, W - 42, oa_y + 52], 14, outline="#33B5FF", width=1)
    text_center(draw, (W // 2, oa_y + 27), "Open App  ›", WHITE, 16, bold=True)

    # Disclaimer text
    disc_y = oa_y + 72
    text_center(draw, (W // 2, disc_y),
                "By continuing you agree to our Terms of Service", GRAY, 10)
    text_center(draw, (W // 2, disc_y + 16),
                "and Privacy Policy", GRAY, 10)

    # Add to Group button
    ag_y = disc_y + 44
    rr(draw, [40, ag_y, W - 40, ag_y + 48], 16, outline=ACCENT, width=1)
    text_center(draw, (W // 2, ag_y + 24), "+  Add to Group or Channel", ACCENT, 13, bold=True)

    # Draw bottom tabs (Links active + Similar Bots)
    draw.rectangle([0, H - 100, W, H - 48], fill=CARD)
    draw.line([0, H - 100, W, H - 100], fill=GRAY3, width=1)
    tab_w = W / 2
    for i, t in enumerate(["Links", "Similar Bots"]):
        xc = int(tab_w * i + tab_w / 2)
        col = ACCENT if t == "Links" else GRAY
        text_center(draw, (xc, H - 72), t, col, 14, bold=True)
        if t == "Links":
            circle(draw, [xc - 16, H - 48, xc - 12, H - 44], fill=ACCENT)

    # Bottom nav
    bottom_nav(draw, "Links")
    return img


# ─── Screen 2: /start Menu ────────────────────────────────────────────────

def screen_2() -> Image.Image:
    """/start menu — chat interface with bot greeting and full command list."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    status_bar(draw, "1:31 AM", 65)

    # Header bar
    rr(draw, [0, 48, W, 100], 0, fill=CARD)
    small_logo_r = 16
    draw_swirl_logo(draw, 46, 74, small_logo_r)
    text(draw, (70, 60), "ChatGPT | GPT Image 2", WHITE, 14, bold=True)
    text(draw, (70, 82), "GPT-5 Telegram Bot", GRAY, 11)

    # User bubble — /start (purple, right-aligned)
    ub_y = 118
    ub_w, ub_h = 120, 34
    bx = W - 40 - ub_w
    rr(draw, [bx, ub_y, bx + ub_w, ub_y + ub_h], 16, fill="#2E1A47")
    text_center(draw, (bx + ub_w // 2, ub_y + 8), "/start", "#B388FF", 13, bold=True)
    text(draw, (bx + ub_w - 2, ub_y + ub_h), "1:31 AM", GRAY, 8, anchor="ra")

    # Bot greeting bubble (left-aligned)
    g_y = ub_y + 55
    greeting = "Hello! This bot is your personal AI"
    bubble_w = tw(draw, greeting, 13) + 28
    rr(draw, [20, g_y, 20 + bubble_w, g_y + 36], 16, fill=CARD)
    text(draw, (34, g_y + 10), greeting, WHITE, 13)
    text(draw, (34, g_y + 36), "1:31 AM", GRAY, 8)

    # Command menu list
    menu_items = [
        ("👋", "About the bot", "/start", False),
        ("👤", "My account", "/account", False),
        ("🚀", "Go Premium", "/premium", False),
        ("💬", "Clear chat", "/deletecontext", False),
        ("🌅", "Create image", "/photo", False),
        ("🎬", "Create video", "/video", False),
        ("🎸", "Create music", "/music", False),
        ("💡", "Create presentation", "/slides", True),
        ("🔎", "Web search", "/s", False),
        ("📝", "Select AI model", "/model", False),
        ("⚙️", "Settings", "/settings", False),
        ("❓", "List of commands", "/help", False),
        ("📄", "Terms of service", "/privacy", False),
    ]

    my = g_y + 52
    for i, (emoji, label, cmd, is_new) in enumerate(menu_items):
        item_y = my + i * 44
        if item_y > H - 190:
            break
        # Icon circle
        circle(draw, [30, item_y + 3, 52, item_y + 25], fill=CARD2)
        text_center(draw, (41, item_y + 14), emoji, WHITE, 15)
        # Label
        text(draw, (62, item_y + 1), label, WHITE, 12)
        # Command tag
        text(draw, (62, item_y + 20), cmd, GRAY3, 9)
        # NEW badge
        if is_new:
            rr(draw, [206, item_y, 246, item_y + 16], 6, fill="#FF5252")
            text_center(draw, (226, item_y + 3), "NEW", WHITE, 8, bold=True)
        # Separator
        draw.line([28, item_y + 38, W - 28, item_y + 38], fill=GRAY4, width=1)

    # Bottom input bar
    ib_y = H - 150
    draw.rectangle([0, ib_y, W, H - 48], fill=CARD)
    draw.line([0, ib_y, W, ib_y], fill=GRAY3, width=1)

    rr(draw, [12, ib_y + 8, W - 12, ib_y + 50], 22, fill=BG2)
    # Menu button
    text_center(draw, (36, ib_y + 18), "≡", WHITE, 20, bold=True)
    text(draw, (52, ib_y + 18), "Menu", GRAY, 12)
    # Right side icons
    text_center(draw, (W - 85, ib_y + 18), "😊", WHITE, 18)
    text_center(draw, (W - 52, ib_y + 18), "📎", WHITE, 16)
    text_center(draw, (W - 20, ib_y + 18), "📷", WHITE, 16)

    bottom_nav(draw, "Links")
    return img


# ─── Screen 3: Features & Commands ─────────────────────────────────────────

def screen_3() -> Image.Image:
    """Features & Commands info — command list, free models, premium upgrade."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    status_bar(draw, "1:30 AM", 72)

    # Header
    rr(draw, [0, 48, W, 100], 0, fill=CARD)
    draw_swirl_logo(draw, 46, 74, 16)
    text(draw, (70, 58), "Features & Commands", WHITE, 16, bold=True)
    text(draw, (70, 82), "How to use the bot ✨", GRAY, 11)

    y = 116

    # Command instruction cards
    commands = [
        ("🔎", "/s [query]", "Search the web in real-time", "Web Search"),
        ("🌅", "/photo [prompt]", "Generate stunning AI images", "Image Gen"),
        ("💡", "/slides [topic]", "Create presentations instantly", "Slides"),
        ("🎬", "/video [prompt]", "Generate AI videos from text", "Video"),
        ("🎸", "/music [prompt]", "Compose original music", "Music"),
    ]

    for emoji, cmd, desc, tag in commands:
        rr(draw, [16, y, W - 16, y + 72], 16, fill=CARD)
        circle(draw, [30, y + 14, 54, y + 38], fill=CARD2)
        text_center(draw, (42, y + 26), emoji, WHITE, 20)
        text(draw, (64, y + 8), cmd, WHITE, 13, bold=True)
        text(draw, (64, y + 30), desc, GRAY, 11)
        rr(draw, [W - 92, y + 8, W - 26, y + 26], 8, fill=GRAY4)
        text_center(draw, (W - 59, y + 17), tag, ACCENT, 9, bold=True)
        y += 84

    y += 8

    # FREE models section
    rr(draw, [16, y, W - 16, y + 28], 12, fill="#0D2D1D")
    text(draw, (28, y + 6), "✓  AVAILABLE FOR FREE", "#66FF99", 12, bold=True)
    free_models = [
        "GPT-4o", "Claude 3.5 Sonnet", "Gemini 2.5 Flash",
        "DeepSeek V3", "Nano Banana Pro", "GPT Image 1",
        "Kling AI", "Seedance 2", "Suno AI",
    ]
    y += 38
    cols = 3
    cell_w = (W - 40) // cols
    for i, m in enumerate(free_models):
        col_idx = i % cols
        row_idx = i // cols
        cx = 20 + col_idx * cell_w
        cy = y + row_idx * 40
        rr(draw, [cx, cy, cx + cell_w - 4, cy + 32], 10, fill="#0D1F2D")
        # Dot
        circle(draw, [cx + 8, cy + 12, cx + 12, cy + 16], fill="#66FF99")
        model_name = m.split("/")[-1].strip()
        text(draw, (cx + 18, cy + 8), model_name, "#B0FFC0", 9, bold=True)

    y = y + ((len(free_models) + cols - 1) // cols) * 40 + 12

    # PREMIUM section
    rr(draw, [16, y, W - 16, y + 28], 12, fill="#1A0D2D")
    text(draw, (28, y + 6), "★  UPGRADE VIA /PREMIUM", "#B388FF", 12, bold=True)
    premium_models = [
        "GPT-5.5", "Claude 5", "Gemini 3.5 Pro",
        "Kling 2.0", "Suno V4", "Midjourney",
    ]
    y += 38
    for i, m in enumerate(premium_models):
        col_idx = i % cols
        row_idx = i // cols
        cx = 20 + col_idx * cell_w
        cy = y + row_idx * 40
        rr(draw, [cx, cy, cx + cell_w - 4, cy + 32], 10, fill="#1A0D2D")
        circle(draw, [cx + 8, cy + 12, cx + 12, cy + 16], fill=GOLD)
        text(draw, (cx + 18, cy + 8), m, GOLD, 9, bold=True)

    y = y + 40 + 16

    # Quick actions grid
    rr(draw, [16, y, W - 16, y + 62], 16, fill=CARD)
    text(draw, (30, y + 6), "Quick Actions", WHITE, 12, bold=True)
    quick_actions = ["✏️  Choose Model", "🎨  Image Gen", "🔎  Web Search", "⚙️  Settings"]
    qw = (W - 40 - 24) // 4
    for i, a in enumerate(quick_actions):
        ax = 22 + i * (qw + 8)
        rr(draw, [ax, y + 28, ax + qw - 4, y + 54], 10, fill=CARD2)
        text_center(draw, (ax + (qw - 4) // 2, y + 40), a, GRAY, 9)

    # Bottom area for nav
    draw.rectangle([0, H - 100, W, H], fill=CARD)
    bottom_nav(draw, "Links")
    return img


# ─── Screen 4: How to Create Guide ─────────────────────────────────────────

def screen_4() -> Image.Image:
    """How to Create Guide — detailed instructions for each feature."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    status_bar(draw, "1:29 AM", 80)

    # Header
    rr(draw, [0, 48, W, 148], 0, fill=CARD)
    draw_swirl_logo(draw, 50, 85, 24)
    text(draw, (82, 68), "How to Create Guide", WHITE, 17, bold=True)
    text(draw, (82, 92), "Your personal AI studio", GRAY, 11)
    text(draw, (24, 118), "Create text, images, videos, and music.", GRAY, 12)

    y = 162

    # Section header
    rr(draw, [16, y, W - 16, y + 30], 12, fill=CARD)
    text(draw, (28, y + 7), "📖  HOW TO CREATE (IT'S EASY)", ACCENT, 12, bold=True)
    y += 44

    # Guide cards
    guides = [
        ("📝", "Text Generation",
         "Send any message or /ask [question]\nGPT-4o, Claude, Gemini handle the rest"),
        ("🔎", "Web Search",
         "Type /s [search query]\nReal-time search with AI summaries"),
        ("🌅", "Image Creation",
         "Type /photo [description]\nor /photo [style]: [description]"),
        ("💡", "Presentations",
         "Type /slides [topic]\nGenerates slide deck with AI content"),
        ("🎬", "Video Creation",
         "Type /video [description]\nAI generates video from your prompt"),
        ("🎸", "Music Creation",
         "Type /music [genre/style]\nAI composes original music"),
    ]

    for emoji, title, desc in guides:
        rr(draw, [16, y, W - 16, y + 76], 16, fill=CARD)
        circle(draw, [30, y + 12, 54, y + 36], fill=CARD2)
        text_center(draw, (42, y + 24), emoji, WHITE, 18)
        text(draw, (64, y + 8), title, WHITE, 13, bold=True)
        lines = desc.split("\n")
        for li, line in enumerate(lines):
            text(draw, (64, y + 30 + li * 16), line, GRAY, 10)
        y += 84

    y += 8

    # FREE models
    rr(draw, [16, y, W - 16, y + 28], 12, fill="#0D2D1D")
    text(draw, (28, y + 6), "✓  AVAILABLE FOR FREE", "#66FF99", 12, bold=True)
    y += 36
    text(draw, (24, y), "GPT-4o  ·  Claude 3.5 Sonnet  ·  Gemini 2.5 Flash  ·  DeepSeek V3", GRAY, 11)
    y += 20
    text(draw, (24, y), "Nano Banana Pro  ·  Kling AI  ·  Seedance 2  ·  Suno AI", GRAY, 11)

    y += 42

    # PREMIUM
    rr(draw, [16, y, W - 16, y + 28], 12, fill="#1A0D2D")
    text(draw, (28, y + 6), "★  UPGRADE VIA /PREMIUM", "#B388FF", 12, bold=True)
    y += 36
    text(draw, (24, y), "GPT-5.5  ·  Claude 5  ·  Gemini 3.5 Pro  ·  Kling 2.0", "#FFD700", 11)
    y += 20
    text(draw, (24, y), "Midjourney  ·  Suno V4  ·  Flux 2  ·  Veo 3.1", "#FFD700", 11)

    draw.rectangle([0, H - 100, W, H], fill=CARD)
    bottom_nav(draw, "Links")
    return img


# ─── Screen 5: Capabilities Overview (Light Green Header) ──────────────────

def screen_5() -> Image.Image:
    """Capabilities with light lime-green gradient header + brand icons."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    status_bar(draw, "1:28 AM", 85)

    # Light green gradient header
    header_h = 170
    gradient_v(draw, [0, 48, W, 48 + header_h], LIGHT_GREEN_GRAD_TOP, LIGHT_GREEN_GRAD_BOT)

    # Central swirl logo (larger)
    cx, cy = W // 2, 48 + header_h // 2 - 10
    draw_swirl_logo(draw, cx, cy, 38, with_badge=True)

    # Surrounding AI brand icons in a circle
    brand_icons = ["🤖", "🧠", "✨", "🎨", "🎬", "🎵", "🔬", "💡", "⚡", "📊", "🔮", "🌈"]
    n = len(brand_icons)
    icon_r = 52
    for i, bi in enumerate(brand_icons):
        angle = 2 * math.pi * i / n - math.pi / 2
        ix = cx + int(icon_r * math.cos(angle))
        iy = cy + int(icon_r * math.sin(angle))
        text_center(draw, (ix, iy), bi, WHITE, 13)

    # Title
    ty = 48 + header_h + 14
    text_center(draw, (W // 2, ty), "What can this bot do?", WHITE, 20, bold=True)
    text_center(draw, (W // 2, ty + 28), "All the Best AI Models in One Place", GRAY, 12)

    y = ty + 54

    # Category lists
    categories = [
        ("Text Generation", ACCENT, ["ChatGPT 5.5", "Gemini 3.5", "Claude", "DeepSeek", "Perplexity"]),
        ("Image Generation", "#FF6B35", ["Nano Banana Pro", "GPT Image 2", "Midjourney", "Seedream", "Flux 2"]),
        ("Video Generation", "#E040FB", ["Kling", "Veo 3.1", "Seedance 2", "Grok Imagine", "Hailuo", "Pika"]),
        ("Music Generation", GREEN, ["Suno AI", "Lyria 3"]),
    ]

    for cat_name, cat_color, items in categories:
        rr(draw, [16, y, W - 16, y + 28], 12, fill=CARD)
        rr(draw, [16, y, 22, y + 28], 12, fill=cat_color)
        text(draw, (34, y + 6), cat_name, WHITE, 12, bold=True)
        y += 36

        # 2-column grid
        cols, cell_w = 2, (W - 40) // 2
        for i in range(0, len(items), 2):
            row = items[i:i + 2]
            for ri, item in enumerate(row):
                ix = 18 + ri * cell_w
                rr(draw, [ix, y, ix + cell_w - 6, y + 32], 10, fill=BG3)
                circle(draw, [ix + 10, y + 12, ix + 14, y + 16], fill=cat_color)
                text(draw, (ix + 20, y + 8), item, WHITE, 10)
            y += 38

    y += 8

    # Start Bot CTA
    rr(draw, [40, y, W - 40, y + 54], 16, fill=ACCENT)
    rr(draw, [42, y + 2, W - 42, y + 52], 14, outline="#33B5FF", width=1)
    text_center(draw, (W // 2, y + 27), "▶  Start Bot", WHITE, 16, bold=True)

    draw.rectangle([0, H - 100, W, H], fill=CARD)
    bottom_nav(draw, "Links")
    return img


# ─── Screen 6: Capabilities Overview (Purple Header) ───────────────────────

def screen_6() -> Image.Image:
    """Capabilities with solid purple header — no surrounding icons."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    status_bar(draw, "1:27 AM", 90)

    # Solid purple header
    header_h = 160
    draw.rectangle([0, 48, W, 48 + header_h], fill=PURPLE_HEADER)

    # Single centered swirl logo only
    cx, cy = W // 2, 48 + header_h // 2 - 5
    draw_swirl_logo(draw, cx, cy, 38, with_badge=True)

    # Title
    ty = 48 + header_h + 14
    text_center(draw, (W // 2, ty), "What can this bot do?", WHITE, 20, bold=True)
    text_center(draw, (W // 2, ty + 28), "All the Best AI Models in One Place", GRAY, 12)

    y = ty + 54

    # Same categories as screen 5
    categories = [
        ("Text Generation", ACCENT, ["ChatGPT 5.5", "Gemini 3.5", "Claude", "DeepSeek", "Perplexity"]),
        ("Image Generation", "#FF6B35", ["Nano Banana Pro", "GPT Image 2", "Midjourney", "Seedream", "Flux 2"]),
        ("Video Generation", "#E040FB", ["Kling", "Veo 3.1", "Seedance 2", "Grok Imagine", "Hailuo", "Pika"]),
        ("Music Generation", GREEN, ["Suno AI", "Lyria 3"]),
    ]

    for cat_name, cat_color, items in categories:
        rr(draw, [16, y, W - 16, y + 28], 12, fill=CARD)
        rr(draw, [16, y, 22, y + 28], 12, fill=cat_color)
        text(draw, (34, y + 6), cat_name, WHITE, 12, bold=True)
        y += 36

        cols, cell_w = 2, (W - 40) // 2
        for i in range(0, len(items), 2):
            row = items[i:i + 2]
            for ri, item in enumerate(row):
                ix = 18 + ri * cell_w
                rr(draw, [ix, y, ix + cell_w - 6, y + 32], 10, fill=BG3)
                circle(draw, [ix + 10, y + 12, ix + 14, y + 16], fill=cat_color)
                text(draw, (ix + 20, y + 8), item, WHITE, 10)
            y += 38

    y += 8

    rr(draw, [40, y, W - 40, y + 54], 16, fill=ACCENT)
    rr(draw, [42, y + 2, W - 42, y + 52], 14, outline="#33B5FF", width=1)
    text_center(draw, (W // 2, y + 27), "▶  Start Bot", WHITE, 16, bold=True)

    draw.rectangle([0, H - 100, W, H], fill=CARD)
    bottom_nav(draw, "Links")
    return img


# ─── Collage helper ────────────────────────────────────────────────────────

def make_collage(screens: List[Image.Image], cols: int = 3) -> Image.Image:
    """Create a tiled collage of all screens for easy preview."""
    rows = (len(screens) + cols - 1) // cols
    thumb_size = (W // 2, H // 2)
    cw = thumb_size[0] * cols
    ch = thumb_size[1] * rows
    collage = Image.new("RGB", (cw, ch), BG)

    for i, scr in enumerate(screens):
        r = i // cols
        c = i % cols
        thumb = scr.resize(thumb_size, Image.LANCZOS)
        collage.paste(thumb, (c * thumb_size[0], r * thumb_size[1]))
    return collage


# ─── Main entry point ──────────────────────────────────────────────────────

def generate_all(output_dir: Optional[str] = None) -> List[str]:
    """Generate all 6 screens and return list of file paths."""
    if output_dir is None:
        output_dir = ASSETS_DIR
    os.makedirs(output_dir, exist_ok=True)

    screens = {
        "01_bot_profile": screen_1,
        "02_start_menu": screen_2,
        "03_features_commands": screen_3,
        "04_how_to_create": screen_4,
        "05_capabilities_green": screen_5,
        "06_capabilities_purple": screen_6,
    }

    paths = []
    for name, fn in screens.items():
        path = os.path.join(output_dir, f"{name}.png")
        logger.info(f"Rendering {name}...")
        img = fn()
        img.save(path)
        paths.append(path)
        logger.info(f"  Saved ({img.size[0]}x{img.size[1]})")

    # Also generate a tile collage
    all_imgs = [fn() for fn in screens.values()]
    collage = make_collage(all_imgs, 3)
    collage_path = os.path.join(output_dir, "_collage_preview.png")
    collage.save(collage_path)
    paths.append(collage_path)
    logger.info(f"Collage saved: {collage_path}")

    return paths


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    print("=" * 50)
    print("  Mira Bot — Telegram Mini App Screen Generator")
    print("=" * 50)
    paths = generate_all()
    print("=" * 50)
    for p in paths:
        print(f"  ✓ {os.path.basename(p)}")
    print(f"\n  Saved to {ASSETS_DIR}")
    print("=" * 50)
