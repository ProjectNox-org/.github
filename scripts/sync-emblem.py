#!/usr/bin/env python3
"""
Sync and build Project Nox institutional brand assets from the canonical
Official Emblem WebP embedded in Awerkori/Awerkori/assets/profile/hero.svg.

Requirements: Python >= 3.10, Pillow (see scripts/requirements.txt).
"""

import argparse
import base64
import hashlib
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

SOURCE_URL = "https://raw.githubusercontent.com/Awerkori/Awerkori/main/assets/profile/hero.svg"
EXPECTED_SHA256 = "1cb074291ead25c967861b69a9fcbf92b6b7a3b1fd9b1947e1f158843b06ae7b"
EXPECTED_SIZE = (280, 280)

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSETS = REPO_ROOT / "assets"
BRAND = ASSETS / "brand"
FONT_SANS = "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"


def atomic_write_bytes(target: Path, data: bytes) -> bool:
    """Write bytes atomically. Returns True if file content changed."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_bytes() == data:
        return False
    fd, tmp_name = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp_path, target)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise
    return True


def atomic_write_svg(target: Path, content: str) -> bool:
    """Validate XML well-formedness and write SVG atomically."""
    cleaned = content.strip() + "\n"
    ET.fromstring(cleaned)
    return atomic_write_bytes(target, cleaned.encode("utf-8"))


def fetch_source_svg(source_path: Path | None) -> str:
    if source_path is not None:
        if not source_path.is_file():
            raise FileNotFoundError(f"Local source SVG not found: {source_path}")
        return source_path.read_text(encoding="utf-8")
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "ProjectNox-SyncEmblem/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Unexpected HTTP status {resp.status} from {SOURCE_URL}")
            return resp.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to fetch canonical source SVG from {SOURCE_URL}: {exc}") from exc


def extract_and_validate_emblem(svg_text: str, allow_hash_mismatch: bool) -> tuple[str, bytes, str]:
    pattern = r'<!--\s*Official Emblem WebP[^>]*-->\s*<image\b[^>]*href="data:image/webp;base64,([^"]+)"[^>]*>'
    m = re.search(pattern, svg_text)
    if not m:
        m = re.search(r'<image\b[^>]*href="data:image/webp;base64,([^"]+)"[^>]*>', svg_text)
    if not m:
        raise ValueError("Official Emblem WebP <image> element not found in source SVG.")

    b64 = m.group(1).strip()
    try:
        raw = base64.b64decode(b64, validate=True)
    except Exception as exc:
        raise ValueError(f"Invalid Base64 payload in Official Emblem WebP: {exc}") from exc

    if raw[:4] != b"RIFF" or raw[8:12] != b"WEBP":
        raise ValueError("Extracted payload does not have a valid RIFF/WEBP header.")

    with Image.open(BytesIO(raw)) as img:
        if img.size != EXPECTED_SIZE:
            raise ValueError(f"Expected emblem size {EXPECTED_SIZE}, got {img.size}.")
        if "A" not in img.getbands():
            raise ValueError(f"Expected alpha channel in emblem, got mode {img.mode}.")

    sha256 = hashlib.sha256(raw).hexdigest()
    if sha256 != EXPECTED_SHA256 and not allow_hash_mismatch:
        raise ValueError(
            f"Emblem SHA-256 mismatch!\n"
            f"  Expected: {EXPECTED_SHA256}\n"
            f"  Actual:   {sha256}\n"
            f"Re-run with --allow-hash-update only if the upstream emblem was intentionally updated."
        )
    return b64, raw, sha256


def build_avatar_png_bytes(webp_bytes: bytes) -> bytes:
    """Build deterministic 512x512 1:1 cosmic avatar PNG using the exact extracted WebP."""
    size = 512
    canvas = Image.new("RGBA", (size, size), (9, 6, 16, 255))

    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    cx, cy = size // 2, size // 2
    for r in range(230, 0, -4):
        alpha_p = int(42 * (1 - r / 230) ** 1.8)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(147, 51, 234, alpha_p))
    for r in range(150, 0, -4):
        alpha_g = int(28 * (1 - r / 150) ** 2.0)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(251, 191, 36, alpha_g))
    canvas = Image.alpha_composite(canvas, glow)

    with Image.open(BytesIO(webp_bytes)) as emblem:
        emblem_rgba = emblem.convert("RGBA")
        target = 368
        emblem_resized = emblem_rgba.resize((target, target), Image.Resampling.LANCZOS)
        offset = (size - target) // 2
        canvas.alpha_composite(emblem_resized, (offset, offset))

    buf = BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def build_mark_svg(b64: str, mode: str) -> str:
    bg = "#090610" if mode == "dark" else "#FAFBFD"
    medallion = (
        ""
        if mode == "dark"
        else '<circle cx="128" cy="128" r="102" fill="#120A1F" stroke="#7A590C" stroke-width="1.5" stroke-opacity="0.45"/>'
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256" role="img" aria-labelledby="markTitle-{mode} markDesc-{mode}">
  <title id="markTitle-{mode}">Project Nox — Símbolo Oficial</title>
  <desc id="markDesc-{mode}">Emblema oficial do Project Nox em roxo e dourado.</desc>
  <defs>
    <radialGradient id="markNebula-{mode}" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#9333ea" stop-opacity="0.45"/>
      <stop offset="55%" stop-color="#581c87" stop-opacity="0.18"/>
      <stop offset="100%" stop-color="{bg}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="markGold-{mode}" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#fbbf24" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="{bg}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="256" height="256" rx="56" fill="{bg}"/>
  {medallion}
  <circle cx="128" cy="128" r="104" fill="url(#markNebula-{mode})"/>
  <circle cx="128" cy="128" r="76" fill="url(#markGold-{mode})"/>
  <image href="data:image/webp;base64,{b64}" x="36" y="36" width="184" height="184"/>
</svg>"""


def theme_tokens(mode: str) -> dict:
    is_dark = mode == "dark"
    return {
        "is_dark": is_dark,
        "bg_0": "#090610" if is_dark else "#FAFBFD",
        "bg_1": "#120a1f" if is_dark else "#F1F5F9",
        "bg_2": "#08050e" if is_dark else "#EDF2F7",
        "border": "#382156" if is_dark else "#CBD5E1",
        "ambient_op": "0.18" if is_dark else "0.08",
        "nebula_op0": "0.45" if is_dark else "0.28",
        "nebula_op1": "0.20" if is_dark else "0.12",
        "gold_core_op": "0.25" if is_dark else "0.16",
        "orbit_ccw_stroke": "#a855f7" if is_dark else "#6D28D9",
        "orbit_ccw_op": "0.60" if is_dark else "0.45",
        # WCAG 2.2 AA (>= 4.5:1) compliant foregrounds
        "eyebrow_fill": "#fbbf24" if is_dark else "#7A590C",
        "title_main_fill": "#F8FAFC" if is_dark else "#0F172A",
        "title_nox_fill": "#B59AF5" if is_dark else "#6D28D9",
        "desc_fill": "#d4c6f7" if is_dark else "#334155",
        "rule_gold": "#fbbf24" if is_dark else "#7A590C",
        "rule_purple": "#a855f7" if is_dark else "#6D28D9",
        "star_white": "#ffffff" if is_dark else "#94A3B8",
        "star_gold": "#fef08a" if is_dark else "#9A741E",
        "star_violet": "#e9d5ff" if is_dark else "#7C3AED",
        "sweep_color": "#fef08a" if is_dark else "#a855f7",
        "sweep_op": "0.35" if is_dark else "0.14",
    }


def shared_animation_css(cx: int, cy: int, sweep_end: int) -> str:
    return f"""
    .aurora-pulse {{
      animation: nebulaBreathe 8s ease-in-out infinite alternate;
      transform-origin: {cx}px {cy}px;
    }}
    .orbit-cw {{
      animation: spinCW 32s linear infinite;
      transform-origin: {cx}px {cy}px;
    }}
    .orbit-ccw {{
      animation: spinCCW 24s linear infinite;
      transform-origin: {cx}px {cy}px;
    }}
    .satellite {{
      animation: spinCW 18s linear infinite;
      transform-origin: {cx}px {cy}px;
    }}
    .satellite-sub {{
      animation: spinCCW 28s linear infinite;
      transform-origin: {cx}px {cy}px;
    }}
    .sweep-move {{
      animation: sweepCycle 14s ease-in-out infinite;
    }}
    .star-twinkle-1 {{
      animation: twinkle 4.2s ease-in-out infinite alternate;
    }}
    .star-twinkle-2 {{
      animation: twinkle 5.8s ease-in-out infinite alternate 1.5s;
    }}
    .star-twinkle-3 {{
      animation: twinkle 6.5s ease-in-out infinite alternate 3s;
    }}

    @keyframes spinCW {{
      from {{ transform: rotate(0deg); }}
      to {{ transform: rotate(360deg); }}
    }}
    @keyframes spinCCW {{
      from {{ transform: rotate(360deg); }}
      to {{ transform: rotate(0deg); }}
    }}
    @keyframes nebulaBreathe {{
      0% {{ opacity: 0.35; transform: scale(0.95); }}
      50% {{ opacity: 0.85; transform: scale(1.08); }}
      100% {{ opacity: 0.45; transform: scale(0.98); }}
    }}
    @keyframes sweepCycle {{
      0%, 15% {{ transform: translateX(-350px) skewX(-20deg); opacity: 0; }}
      40% {{ opacity: 0.7; }}
      75%, 100% {{ transform: translateX({sweep_end}px) skewX(-20deg); opacity: 0; }}
    }}
    @keyframes twinkle {{
      0% {{ opacity: 0.15; transform: scale(0.8); }}
      100% {{ opacity: 0.95; transform: scale(1.3); }}
    }}

    @media (prefers-reduced-motion: reduce) {{
      .aurora-pulse, .orbit-cw, .orbit-ccw, .satellite, .satellite-sub, .sweep-move, .star-twinkle-1, .star-twinkle-2, .star-twinkle-3 {{
        animation: none !important;
      }}
    }}"""


def shared_hero_defs(id_suffix: str, w: int, h: int, t: dict) -> str:
    return f"""
    <linearGradient id="heroBg-{id_suffix}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{t['bg_0']}"/>
      <stop offset="48%" stop-color="{t['bg_1']}"/>
      <stop offset="100%" stop-color="{t['bg_2']}"/>
    </linearGradient>

    <radialGradient id="symbolNebula-{id_suffix}" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#9333ea" stop-opacity="{t['nebula_op0']}"/>
      <stop offset="50%" stop-color="#581c87" stop-opacity="{t['nebula_op1']}"/>
      <stop offset="100%" stop-color="{t['bg_0']}" stop-opacity="0"/>
    </radialGradient>

    <radialGradient id="goldCoreGlow-{id_suffix}" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#fbbf24" stop-opacity="{t['gold_core_op']}"/>
      <stop offset="60%" stop-color="#d97706" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="{t['bg_0']}" stop-opacity="0"/>
    </radialGradient>

    <radialGradient id="ambientRight-{id_suffix}" cx="90%" cy="30%" r="60%">
      <stop offset="0%" stop-color="#7c3aed" stop-opacity="{t['ambient_op']}"/>
      <stop offset="100%" stop-color="{t['bg_0']}" stop-opacity="0"/>
    </radialGradient>

    <linearGradient id="orbitStroke-{id_suffix}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#fbbf24" stop-opacity="0.85"/>
      <stop offset="50%" stop-color="#a855f7" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="#f59e0b" stop-opacity="0.85"/>
    </linearGradient>

    <linearGradient id="ruleGrad-{id_suffix}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{t['rule_gold']}"/>
      <stop offset="48%" stop-color="{t['rule_purple']}"/>
      <stop offset="100%" stop-color="{t['rule_purple']}" stop-opacity="0"/>
    </linearGradient>

    <linearGradient id="sweepBeam-{id_suffix}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="50%" stop-color="{t['sweep_color']}" stop-opacity="{t['sweep_op']}"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>

    <filter id="goldGlow-{id_suffix}" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <filter id="softGlow-{id_suffix}" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="2" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <mask id="heroMask-{id_suffix}">
      <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="#ffffff"/>
    </mask>"""


def build_hero_desktop_svg(b64: str, mode: str) -> str:
    t = theme_tokens(mode)
    s = mode
    light_medallion = (
        ""
        if t["is_dark"]
        else '<circle cx="180" cy="150" r="82" fill="#120a1f" opacity="0.96" stroke="#7A590C" stroke-width="1" stroke-opacity="0.35"/>'
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="300" viewBox="0 0 1200 300" role="img" aria-labelledby="heroTitle-{s} heroDesc-{s}">
  <title id="heroTitle-{s}">Project Nox — Identidade Institucional Oficial</title>
  <desc id="heroDesc-{s}">Banner institucional do Project Nox com o emblema oficial, animação orbital e atmosfera cósmica em roxo e dourado.</desc>

  <defs>{shared_hero_defs(s, 1200, 300, t)}</defs>

  <style>
    text {{ font-family: {FONT_SANS}; }}
    .eyebrow {{ font-size: 12.5px; font-weight: 700; letter-spacing: 3.4px; fill: {t['eyebrow_fill']}; }}
    .hero-title {{ font-size: 58px; font-weight: 800; letter-spacing: 2.8px; }}
    .hero-desc {{ font-size: 19px; font-weight: 400; fill: {t['desc_fill']}; letter-spacing: 0.1px; }}
    {shared_animation_css(180, 150, 1550)}
  </style>

  <rect x="0.5" y="0.5" width="1199" height="299" rx="16" fill="url(#heroBg-{s})" stroke="{t['border']}" stroke-width="1.25"/>
  <rect x="1" y="1" width="1198" height="298" rx="15" fill="url(#ambientRight-{s})"/>

  <g class="star-twinkle-1">
    <circle cx="360" cy="46" r="1.4" fill="{t['star_white']}"/>
    <circle cx="780" cy="54" r="1.1" fill="{t['star_gold']}"/>
    <circle cx="1060" cy="200" r="1.5" fill="{t['star_white']}"/>
    <circle cx="540" cy="248" r="1.2" fill="{t['star_violet']}"/>
  </g>
  <g class="star-twinkle-2">
    <circle cx="320" cy="238" r="1.1" fill="{t['star_white']}"/>
    <circle cx="690" cy="38" r="1.4" fill="{t['star_gold']}"/>
    <circle cx="960" cy="82" r="1.1" fill="#c084fc"/>
    <circle cx="1120" cy="140" r="1.3" fill="{t['star_white']}"/>
  </g>
  <g class="star-twinkle-3">
    <text x="470" y="42" font-size="10" fill="{t['rule_gold']}" opacity="0.65">✦</text>
    <text x="1030" y="102" font-size="9" fill="{t['rule_purple']}" opacity="0.55">✦</text>
    <text x="860" y="246" font-size="10" fill="{t['rule_gold']}" opacity="0.65">✦</text>
  </g>

  <g id="symbolSection-{s}">
    <circle cx="180" cy="150" r="118" fill="url(#symbolNebula-{s})" class="aurora-pulse"/>
    <circle cx="180" cy="150" r="82" fill="url(#goldCoreGlow-{s})" class="aurora-pulse"/>
    {light_medallion}
    <circle cx="180" cy="150" r="94" fill="none" stroke="url(#orbitStroke-{s})" stroke-width="1.3" stroke-dasharray="14 10 3 10" class="orbit-cw"/>
    <circle cx="180" cy="150" r="78" fill="none" stroke="{t['orbit_ccw_stroke']}" stroke-width="0.9" stroke-dasharray="6 8" opacity="{t['orbit_ccw_op']}" class="orbit-ccw"/>
    <g class="satellite">
      <circle cx="180" cy="56" r="3.6" fill="#fef08a" filter="url(#goldGlow-{s})"/>
      <circle cx="180" cy="56" r="1.6" fill="#ffffff"/>
    </g>
    <g class="satellite-sub">
      <circle cx="180" cy="228" r="2.8" fill="#d946ef" filter="url(#softGlow-{s})"/>
    </g>
    <image href="data:image/webp;base64,{b64}" x="106" y="76" width="148" height="148"/>
  </g>

  <g transform="translate(345, 0)">
    <text x="0" y="108" class="eyebrow">
      <tspan fill="{t['rule_gold']}" filter="url(#softGlow-{s})">✦</tspan><tspan dx="8">INICIATIVA INDEPENDENTE · CÓDIGO ABERTO</tspan>
    </text>
    <text x="0" y="170" class="hero-title">
      <tspan fill="{t['title_main_fill']}">PROJECT </tspan><tspan fill="{t['title_nox_fill']}">NOX</tspan>
    </text>
    <rect x="0" y="190" width="490" height="1.5" rx="1" fill="url(#ruleGrad-{s})"/>
    <text x="0" y="226" class="hero-desc">
      Tecnologia, software e soluções digitais em evolução contínua.
    </text>
  </g>

  <g mask="url(#heroMask-{s})">
    <rect x="0" y="0" width="180" height="300" fill="url(#sweepBeam-{s})" class="sweep-move"/>
  </g>
</svg>"""


def build_hero_mobile_svg(b64: str, mode: str) -> str:
    t = theme_tokens(mode)
    s = f"mobile-{mode}"
    cx, cy = 210, 114
    light_medallion = (
        ""
        if t["is_dark"]
        else f'<circle cx="{cx}" cy="{cy}" r="68" fill="#120a1f" opacity="0.96" stroke="#7A590C" stroke-width="1" stroke-opacity="0.35"/>'
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="420" height="370" viewBox="0 0 420 370" role="img" aria-labelledby="heroTitle-{s} heroDesc-{s}">
  <title id="heroTitle-{s}">Project Nox — Identidade Institucional Oficial</title>
  <desc id="heroDesc-{s}">Banner institucional móvel do Project Nox com o emblema oficial, animação orbital e atmosfera cósmica em roxo e dourado.</desc>

  <defs>
    {shared_hero_defs(s, 420, 370, t)}
    <linearGradient id="ruleGradCentered-{s}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{t['rule_purple']}" stop-opacity="0"/>
      <stop offset="25%" stop-color="{t['rule_gold']}"/>
      <stop offset="75%" stop-color="{t['rule_purple']}"/>
      <stop offset="100%" stop-color="{t['rule_purple']}" stop-opacity="0"/>
    </linearGradient>
  </defs>

  <style>
    text {{ font-family: {FONT_SANS}; }}
    .eyebrow {{ font-size: 11.5px; font-weight: 700; letter-spacing: 2.2px; fill: {t['eyebrow_fill']}; }}
    .hero-title {{ font-size: 40px; font-weight: 800; letter-spacing: 2px; }}
    .hero-desc {{ font-size: 15.5px; font-weight: 400; fill: {t['desc_fill']}; }}
    {shared_animation_css(cx, cy, 780)}
  </style>

  <rect x="0.5" y="0.5" width="419" height="369" rx="16" fill="url(#heroBg-{s})" stroke="{t['border']}" stroke-width="1.25"/>
  <rect x="1" y="1" width="418" height="368" rx="15" fill="url(#ambientRight-{s})"/>

  <g class="star-twinkle-1">
    <circle cx="54" cy="44" r="1.3" fill="{t['star_white']}"/>
    <circle cx="364" cy="62" r="1.2" fill="{t['star_gold']}"/>
    <circle cx="378" cy="316" r="1.3" fill="{t['star_white']}"/>
  </g>
  <g class="star-twinkle-2">
    <circle cx="42" cy="312" r="1.1" fill="{t['star_violet']}"/>
    <circle cx="352" cy="176" r="1.2" fill="#c084fc"/>
    <circle cx="72" cy="182" r="1.1" fill="{t['star_gold']}"/>
  </g>
  <g class="star-twinkle-3">
    <text x="64" y="96" font-size="9" fill="{t['rule_gold']}" opacity="0.65">✦</text>
    <text x="348" y="122" font-size="9" fill="{t['rule_purple']}" opacity="0.55">✦</text>
  </g>

  <g id="symbolSection-{s}">
    <circle cx="{cx}" cy="{cy}" r="96" fill="url(#symbolNebula-{s})" class="aurora-pulse"/>
    <circle cx="{cx}" cy="{cy}" r="68" fill="url(#goldCoreGlow-{s})" class="aurora-pulse"/>
    {light_medallion}
    <circle cx="{cx}" cy="{cy}" r="78" fill="none" stroke="url(#orbitStroke-{s})" stroke-width="1.2" stroke-dasharray="12 9 3 9" class="orbit-cw"/>
    <circle cx="{cx}" cy="{cy}" r="64" fill="none" stroke="{t['orbit_ccw_stroke']}" stroke-width="0.9" stroke-dasharray="5 7" opacity="{t['orbit_ccw_op']}" class="orbit-ccw"/>
    <g class="satellite">
      <circle cx="{cx}" cy="{cy - 78}" r="3.2" fill="#fef08a" filter="url(#goldGlow-{s})"/>
      <circle cx="{cx}" cy="{cy - 78}" r="1.4" fill="#ffffff"/>
    </g>
    <g class="satellite-sub">
      <circle cx="{cx}" cy="{cy + 64}" r="2.5" fill="#d946ef" filter="url(#softGlow-{s})"/>
    </g>
    <image href="data:image/webp;base64,{b64}" x="{cx - 60}" y="{cy - 60}" width="120" height="120"/>
  </g>

  <g text-anchor="middle">
    <text x="210" y="230" class="eyebrow">
      <tspan fill="{t['rule_gold']}" filter="url(#softGlow-{s})">✦</tspan><tspan dx="6">INICIATIVA INDEPENDENTE · CÓDIGO ABERTO</tspan>
    </text>
    <text x="210" y="276" class="hero-title">
      <tspan fill="{t['title_main_fill']}">PROJECT </tspan><tspan fill="{t['title_nox_fill']}">NOX</tspan>
    </text>
    <rect x="65" y="290" width="290" height="1.5" rx="1" fill="url(#ruleGradCentered-{s})"/>
    <text x="210" y="318" class="hero-desc">Tecnologia, software e soluções digitais</text>
    <text x="210" y="340" class="hero-desc">em evolução contínua.</text>
  </g>

  <g mask="url(#heroMask-{s})">
    <rect x="0" y="0" width="130" height="370" fill="url(#sweepBeam-{s})" class="sweep-move"/>
  </g>
</svg>"""


def build_philosophy_desktop_svg(mode: str) -> str:
    is_dark = mode == "dark"
    line_col = "#22263D" if is_dark else "#E2E8F0"
    main_col = "#F8FAFC" if is_dark else "#0F172A"
    purple_col = "#B59AF5" if is_dark else "#6D28D9"
    sub_col = "#CBD5E1" if is_dark else "#475569"
    dot_col = "#D4AF37" if is_dark else "#7A590C"
    s = mode

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 840 96" width="840" height="96" role="img" aria-labelledby="philTitle-{s} philDesc-{s}">
  <title id="philTitle-{s}">Princípios do Project Nox</title>
  <desc id="philDesc-{s}">Construir: software sólido para uso real. Compartilhar: código aberto e transparente. Evoluir: melhoria contínua com a comunidade.</desc>
  <defs>
    <linearGradient id="philLine-{s}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{line_col}" stop-opacity="0"/>
      <stop offset="20%" stop-color="{line_col}" stop-opacity="1"/>
      <stop offset="80%" stop-color="{line_col}" stop-opacity="1"/>
      <stop offset="100%" stop-color="{line_col}" stop-opacity="0"/>
    </linearGradient>
  </defs>

  <rect x="0" y="1" width="840" height="1" fill="url(#philLine-{s})"/>
  <rect x="0" y="94" width="840" height="1" fill="url(#philLine-{s})"/>

  <g transform="translate(140, 0)" text-anchor="middle">
    <text x="0" y="37" font-family="{FONT_SANS}" font-size="15.5" font-weight="700" letter-spacing="1.4" fill="{main_col}">CONSTRUIR</text>
    <text x="0" y="63" font-family="{FONT_SANS}" font-size="13" font-weight="400" fill="{sub_col}">Software sólido para uso real</text>
  </g>
  <circle cx="280" cy="48" r="2.2" fill="{dot_col}" opacity="0.8"/>

  <g transform="translate(420, 0)" text-anchor="middle">
    <text x="0" y="37" font-family="{FONT_SANS}" font-size="15.5" font-weight="700" letter-spacing="1.4" fill="{purple_col}">COMPARTILHAR</text>
    <text x="0" y="63" font-family="{FONT_SANS}" font-size="13" font-weight="400" fill="{sub_col}">Código aberto e transparente</text>
  </g>
  <circle cx="560" cy="48" r="2.2" fill="{dot_col}" opacity="0.8"/>

  <g transform="translate(700, 0)" text-anchor="middle">
    <text x="0" y="37" font-family="{FONT_SANS}" font-size="15.5" font-weight="700" letter-spacing="1.4" fill="{main_col}">EVOLUIR</text>
    <text x="0" y="63" font-family="{FONT_SANS}" font-size="13" font-weight="400" fill="{sub_col}">Melhoria contínua com a comunidade</text>
  </g>
</svg>"""


def build_philosophy_mobile_svg(mode: str) -> str:
    is_dark = mode == "dark"
    line_col = "#22263D" if is_dark else "#E2E8F0"
    main_col = "#F8FAFC" if is_dark else "#0F172A"
    purple_col = "#B59AF5" if is_dark else "#6D28D9"
    sub_col = "#CBD5E1" if is_dark else "#475569"
    dot_col = "#D4AF37" if is_dark else "#7A590C"
    s = f"mobile-{mode}"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 236" width="380" height="236" role="img" aria-labelledby="philTitle-{s} philDesc-{s}">
  <title id="philTitle-{s}">Princípios do Project Nox</title>
  <desc id="philDesc-{s}">Construir: software sólido para uso real. Compartilhar: código aberto e transparente. Evoluir: melhoria contínua com a comunidade.</desc>
  <defs>
    <linearGradient id="philLine-{s}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{line_col}" stop-opacity="0"/>
      <stop offset="20%" stop-color="{line_col}" stop-opacity="1"/>
      <stop offset="80%" stop-color="{line_col}" stop-opacity="1"/>
      <stop offset="100%" stop-color="{line_col}" stop-opacity="0"/>
    </linearGradient>
  </defs>

  <rect x="0" y="1" width="380" height="1" fill="url(#philLine-{s})"/>
  <rect x="0" y="234" width="380" height="1" fill="url(#philLine-{s})"/>

  <g transform="translate(190, 36)" text-anchor="middle">
    <text x="0" y="0" font-family="{FONT_SANS}" font-size="16" font-weight="700" letter-spacing="1.5" fill="{main_col}">CONSTRUIR</text>
    <text x="0" y="22" font-family="{FONT_SANS}" font-size="13.5" font-weight="400" fill="{sub_col}">Software sólido para uso real</text>
  </g>
  <circle cx="190" cy="79" r="2" fill="{dot_col}" opacity="0.8"/>

  <g transform="translate(190, 112)" text-anchor="middle">
    <text x="0" y="0" font-family="{FONT_SANS}" font-size="16" font-weight="700" letter-spacing="1.5" fill="{purple_col}">COMPARTILHAR</text>
    <text x="0" y="22" font-family="{FONT_SANS}" font-size="13.5" font-weight="400" fill="{sub_col}">Código aberto e transparente</text>
  </g>
  <circle cx="190" cy="155" r="2" fill="{dot_col}" opacity="0.8"/>

  <g transform="translate(190, 188)" text-anchor="middle">
    <text x="0" y="0" font-family="{FONT_SANS}" font-size="16" font-weight="700" letter-spacing="1.5" fill="{main_col}">EVOLUIR</text>
    <text x="0" y="22" font-family="{FONT_SANS}" font-size="13.5" font-weight="400" fill="{sub_col}">Melhoria contínua com a comunidade</text>
  </g>
</svg>"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync Project Nox brand assets from Awerkori/Awerkori.")
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Optional explicit local path to hero.svg (defaults to canonical GitHub raw URL).",
    )
    parser.add_argument(
        "--allow-hash-update",
        action="store_true",
        help="Allow updating assets even if the extracted WebP SHA-256 differs from EXPECTED_SHA256.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    svg_text = fetch_source_svg(args.source)
    b64, raw, sha256 = extract_and_validate_emblem(svg_text, args.allow_hash_update)

    outputs: list[tuple[Path, bool]] = []
    outputs.append((BRAND / "nox-emblem.webp", atomic_write_bytes(BRAND / "nox-emblem.webp", raw)))
    outputs.append((BRAND / "nox-avatar.png", atomic_write_bytes(BRAND / "nox-avatar.png", build_avatar_png_bytes(raw))))

    for mode in ("dark", "light"):
        outputs.append((BRAND / f"nox-mark-{mode}.svg", atomic_write_svg(BRAND / f"nox-mark-{mode}.svg", build_mark_svg(b64, mode))))
        outputs.append((ASSETS / f"nox-hero-{mode}.svg", atomic_write_svg(ASSETS / f"nox-hero-{mode}.svg", build_hero_desktop_svg(b64, mode))))
        outputs.append((ASSETS / f"nox-hero-mobile-{mode}.svg", atomic_write_svg(ASSETS / f"nox-hero-mobile-{mode}.svg", build_hero_mobile_svg(b64, mode))))
        outputs.append((ASSETS / f"nox-philosophy-{mode}.svg", atomic_write_svg(ASSETS / f"nox-philosophy-{mode}.svg", build_philosophy_desktop_svg(mode))))
        outputs.append((ASSETS / f"nox-philosophy-mobile-{mode}.svg", atomic_write_svg(ASSETS / f"nox-philosophy-mobile-{mode}.svg", build_philosophy_mobile_svg(mode))))

    changed = [str(p.relative_to(REPO_ROOT)) for p, c in outputs if c]
    unchanged = [str(p.relative_to(REPO_ROOT)) for p, c in outputs if not c]
    print(f"Verified Official Emblem WebP ({len(raw)} bytes, sha256={sha256})")
    print(f"Updated ({len(changed)}): {', '.join(changed) if changed else 'none'}")
    print(f"Unchanged ({len(unchanged)}): {', '.join(unchanged) if unchanged else 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
