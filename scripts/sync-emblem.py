#!/usr/bin/env python3
"""
Sync and build Project Nox institutional brand assets from the canonical
Official Emblem WebP embedded in Awerkori/Awerkori/assets/profile/hero.svg.
"""

import base64
import hashlib
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image, ImageDraw

SOURCE_URL = "https://raw.githubusercontent.com/Awerkori/Awerkori/main/assets/profile/hero.svg"
REPO_ROOT = Path(__file__).resolve().parent.parent
ASSETS = REPO_ROOT / "assets"
BRAND = ASSETS / "brand"
BRAND.mkdir(parents=True, exist_ok=True)

FONT_SANS = "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"


def fetch_source_svg(local_path: Path | None = None) -> str:
    if local_path and local_path.exists():
        return local_path.read_text(encoding="utf-8")
    with urllib.request.urlopen(SOURCE_URL, timeout=15) as resp:
        return resp.read().decode("utf-8")


def extract_emblem_webp(svg_text: str) -> tuple[str, bytes, str]:
    m = re.search(r'<image\b[^>]*href="data:image/webp;base64,([^"]+)"[^>]*>', svg_text)
    if not m:
        raise ValueError("Official Emblem WebP <image> element not found in source SVG.")
    b64 = m.group(1)
    raw = base64.b64decode(b64)
    if raw[:4] != b"RIFF" or raw[8:12] != b"WEBP":
        raise ValueError("Extracted binary does not have a valid RIFF/WEBP header.")
    sha256 = hashlib.sha256(raw).hexdigest()
    return b64, raw, sha256


def save_svg(path: Path, content: str):
    cleaned = content.strip() + "\n"
    ET.fromstring(cleaned)
    path.write_text(cleaned, encoding="utf-8")


def build_avatar_png(webp_path: Path, out_png: Path):
    """Build a 512x512 1:1 cosmic avatar PNG using the exact extracted WebP."""
    size = 512
    canvas = Image.new("RGBA", (size, size), (9, 6, 16, 255))

    # Subtle cosmic nebula radial glow matching hero.svg (#9333ea + #fbbf24)
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

    emblem = Image.open(webp_path).convert("RGBA")
    target = 368
    emblem_resized = emblem.resize((target, target), Image.Resampling.LANCZOS)
    offset = (size - target) // 2
    canvas.alpha_composite(emblem_resized, (offset, offset))
    canvas.save(out_png, format="PNG", optimize=True)


def build_mark_svg(b64: str, mode: str):
    bg = "#090610" if mode == "dark" else "#FAFBFD"
    medallion = (
        ""
        if mode == "dark"
        else '<circle cx="128" cy="128" r="102" fill="#120A1F" stroke="#D4AF37" stroke-width="1.5" stroke-opacity="0.45"/>'
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256" role="img" aria-label="Emblema oficial do Project Nox">
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
    save_svg(BRAND / f"nox-mark-{mode}.svg", svg)


def build_hero_svg(b64: str, mode: str):
    is_dark = mode == "dark"
    bg_0 = "#090610" if is_dark else "#FAFBFD"
    bg_1 = "#120a1f" if is_dark else "#F1F5F9"
    bg_2 = "#08050e" if is_dark else "#EDF2F7"
    border = "#382156" if is_dark else "#CBD5E1"
    ambient_op = "0.18" if is_dark else "0.08"
    nebula_op0 = "0.45" if is_dark else "0.28"
    nebula_op1 = "0.20" if is_dark else "0.12"
    gold_core_op = "0.25" if is_dark else "0.16"
    orbit_ccw_stroke = "#a855f7" if is_dark else "#7c3aed"
    orbit_ccw_op = "0.60" if is_dark else "0.45"

    eyebrow_fill = "#fbbf24" if is_dark else "#9A741E"
    title_main_fill = "#F8FAFC" if is_dark else "#0F172A"
    title_nox_fill = "#B59AF5" if is_dark else "#6D28D9"
    desc_fill = "#d4c6f7" if is_dark else "#334155"
    rule_gold = "#fbbf24" if is_dark else "#A67C1E"
    rule_purple = "#a855f7" if is_dark else "#6D28D9"

    star_white = "#ffffff" if is_dark else "#94A3B8"
    star_gold = "#fef08a" if is_dark else "#B45309"
    star_violet = "#e9d5ff" if is_dark else "#7C3AED"
    sweep_color = "#fef08a" if is_dark else "#a855f7"
    sweep_op = "0.35" if is_dark else "0.14"

    # Subtle cosmic medallion behind the WebP on light theme so the golden/purple emblem pops cleanly
    light_medallion = (
        ""
        if is_dark
        else '<circle cx="180" cy="150" r="82" fill="#120a1f" opacity="0.96" stroke="#A67C1E" stroke-width="1" stroke-opacity="0.35"/>'
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="300" viewBox="0 0 1200 300" role="img" aria-labelledby="heroTitle-{mode} heroDesc-{mode}">
  <title id="heroTitle-{mode}">Project Nox — Identidade Institucional Oficial</title>
  <desc id="heroDesc-{mode}">Banner institucional do Project Nox com o emblema oficial, animação orbital e atmosfera cósmica em roxo e dourado.</desc>

  <defs>
    <!-- Background Gradient -->
    <linearGradient id="heroBg-{mode}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{bg_0}"/>
      <stop offset="48%" stop-color="{bg_1}"/>
      <stop offset="100%" stop-color="{bg_2}"/>
    </linearGradient>

    <!-- Cosmic Nebula Radial Glows -->
    <radialGradient id="symbolNebula-{mode}" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#9333ea" stop-opacity="{nebula_op0}"/>
      <stop offset="50%" stop-color="#581c87" stop-opacity="{nebula_op1}"/>
      <stop offset="100%" stop-color="{bg_0}" stop-opacity="0"/>
    </radialGradient>

    <radialGradient id="goldCoreGlow-{mode}" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#fbbf24" stop-opacity="{gold_core_op}"/>
      <stop offset="60%" stop-color="#d97706" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="{bg_0}" stop-opacity="0"/>
    </radialGradient>

    <radialGradient id="ambientRight-{mode}" cx="90%" cy="30%" r="60%">
      <stop offset="0%" stop-color="#7c3aed" stop-opacity="{ambient_op}"/>
      <stop offset="100%" stop-color="{bg_0}" stop-opacity="0"/>
    </radialGradient>

    <!-- Orbital Ring Gradient -->
    <linearGradient id="orbitStroke-{mode}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#fbbf24" stop-opacity="0.85"/>
      <stop offset="50%" stop-color="#a855f7" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="#f59e0b" stop-opacity="0.85"/>
    </linearGradient>

    <!-- Rule Gradient -->
    <linearGradient id="ruleGrad-{mode}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{rule_gold}"/>
      <stop offset="48%" stop-color="{rule_purple}"/>
      <stop offset="100%" stop-color="{rule_purple}" stop-opacity="0"/>
    </linearGradient>

    <!-- Light Sweep Gradient -->
    <linearGradient id="sweepBeam-{mode}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="50%" stop-color="{sweep_color}" stop-opacity="{sweep_op}"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>

    <!-- Glow Filters -->
    <filter id="goldGlow-{mode}" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <filter id="softGlow-{mode}" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="2" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <!-- Mask for light sweep -->
    <mask id="heroMask-{mode}">
      <rect x="0.5" y="0.5" width="1199" height="299" rx="16" fill="#ffffff"/>
    </mask>
  </defs>

  <style>
    text {{
      font-family: {FONT_SANS};
    }}
    .eyebrow {{
      font-size: 12.5px;
      font-weight: 700;
      letter-spacing: 3.4px;
      fill: {eyebrow_fill};
    }}
    .hero-title {{
      font-size: 58px;
      font-weight: 800;
      letter-spacing: 2.8px;
    }}
    .hero-desc {{
      font-size: 19px;
      font-weight: 400;
      fill: {desc_fill};
      letter-spacing: 0.1px;
    }}

    /* Orbital and Nebula Animations (matching Awerkori/Awerkori/assets/profile/hero.svg) */
    .aurora-pulse {{
      animation: nebulaBreathe 8s ease-in-out infinite alternate;
      transform-origin: 180px 150px;
    }}
    .orbit-cw {{
      animation: spinCW 32s linear infinite;
      transform-origin: 180px 150px;
    }}
    .orbit-ccw {{
      animation: spinCCW 24s linear infinite;
      transform-origin: 180px 150px;
    }}
    .satellite {{
      animation: spinCW 18s linear infinite;
      transform-origin: 180px 150px;
    }}
    .satellite-sub {{
      animation: spinCCW 28s linear infinite;
      transform-origin: 180px 150px;
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
      75%, 100% {{ transform: translateX(1550px) skewX(-20deg); opacity: 0; }}
    }}
    @keyframes twinkle {{
      0% {{ opacity: 0.15; transform: scale(0.8); }}
      100% {{ opacity: 0.95; transform: scale(1.3); }}
    }}

    @media (prefers-reduced-motion: reduce) {{
      .aurora-pulse, .orbit-cw, .orbit-ccw, .satellite, .satellite-sub, .sweep-move, .star-twinkle-1, .star-twinkle-2, .star-twinkle-3 {{
        animation: none !important;
      }}
    }}
  </style>

  <!-- Canvas Surface -->
  <rect x="0.5" y="0.5" width="1199" height="299" rx="16" fill="url(#heroBg-{mode})" stroke="{border}" stroke-width="1.25"/>
  <rect x="1" y="1" width="1198" height="298" rx="15" fill="url(#ambientRight-{mode})"/>

  <!-- Celestial Stars -->
  <g class="star-twinkle-1">
    <circle cx="360" cy="46" r="1.4" fill="{star_white}"/>
    <circle cx="780" cy="54" r="1.1" fill="{star_gold}"/>
    <circle cx="1060" cy="200" r="1.5" fill="{star_white}"/>
    <circle cx="540" cy="248" r="1.2" fill="{star_violet}"/>
  </g>
  <g class="star-twinkle-2">
    <circle cx="320" cy="238" r="1.1" fill="{star_white}"/>
    <circle cx="690" cy="38" r="1.4" fill="{star_gold}"/>
    <circle cx="960" cy="82" r="1.1" fill="#c084fc"/>
    <circle cx="1120" cy="140" r="1.3" fill="{star_white}"/>
  </g>
  <g class="star-twinkle-3">
    <text x="470" y="42" font-size="10" fill="{rule_gold}" opacity="0.65">✦</text>
    <text x="1030" y="102" font-size="9" fill="{rule_purple}" opacity="0.55">✦</text>
    <text x="860" y="246" font-size="10" fill="{rule_gold}" opacity="0.65">✦</text>
  </g>

  <!-- Left: Official Project Nox Symbol and Celestial Orbits -->
  <g id="symbolSection">
    <!-- Nebula Auroras -->
    <circle cx="180" cy="150" r="118" fill="url(#symbolNebula-{mode})" class="aurora-pulse"/>
    <circle cx="180" cy="150" r="82" fill="url(#goldCoreGlow-{mode})" class="aurora-pulse"/>

    {light_medallion}

    <!-- Outer Orbit Ring -->
    <circle cx="180" cy="150" r="94" fill="none" stroke="url(#orbitStroke-{mode})" stroke-width="1.3" stroke-dasharray="14 10 3 10" class="orbit-cw"/>
    <!-- Inner Orbit Ring -->
    <circle cx="180" cy="150" r="78" fill="none" stroke="{orbit_ccw_stroke}" stroke-width="0.9" stroke-dasharray="6 8" opacity="{orbit_ccw_op}" class="orbit-ccw"/>

    <!-- Orbital Satellite Node 1 (Golden Planet) -->
    <g class="satellite">
      <circle cx="180" cy="56" r="3.6" fill="#fef08a" filter="url(#goldGlow-{mode})"/>
      <circle cx="180" cy="56" r="1.6" fill="#ffffff"/>
    </g>
    <!-- Orbital Satellite Node 2 (Violet Planet) -->
    <g class="satellite-sub">
      <circle cx="180" cy="228" r="2.8" fill="#d946ef" filter="url(#softGlow-{mode})"/>
    </g>

    <!-- Official Emblem WebP (Golden Omega with Alpha inside) -->
    <image href="data:image/webp;base64,{b64}" x="106" y="76" width="148" height="148"/>
  </g>

  <!-- Right: Institutional Typography -->
  <g transform="translate(345, 0)">
    <text x="0" y="108" class="eyebrow">
      <tspan fill="{rule_gold}" filter="url(#softGlow-{mode})">✦</tspan><tspan dx="8">INICIATIVA INDEPENDENTE · CÓDIGO ABERTO</tspan>
    </text>

    <text x="0" y="170" class="hero-title">
      <tspan fill="{title_main_fill}">PROJECT </tspan><tspan fill="{title_nox_fill}">NOX</tspan>
    </text>

    <rect x="0" y="190" width="490" height="1.5" rx="1" fill="url(#ruleGrad-{mode})"/>

    <text x="0" y="226" class="hero-desc">
      Tecnologia, software e soluções digitais em evolução contínua.
    </text>
  </g>

  <!-- Masked Light Sweep Beam -->
  <g mask="url(#heroMask-{mode})">
    <rect x="0" y="0" width="180" height="300" fill="url(#sweepBeam-{mode})" class="sweep-move"/>
  </g>
</svg>"""
    save_svg(ASSETS / f"nox-hero-{mode}.svg", svg)


def main():
    local_ref = Path("/home/awerkori/.gemini/antigravity-cli/brain/c6ba7772-9d65-4841-ae33-2505dd7c7518/scratch/awerkori-hero.svg")
    svg_text = fetch_source_svg(local_ref if local_ref.exists() else None)
    b64, raw, sha256 = extract_emblem_webp(svg_text)

    webp_path = BRAND / "nox-emblem.webp"
    webp_path.write_bytes(raw)

    build_avatar_png(webp_path, BRAND / "nox-avatar.png")
    build_mark_svg(b64, "dark")
    build_mark_svg(b64, "light")
    build_hero_svg(b64, "dark")
    build_hero_svg(b64, "light")

    print(f"Synced Official Emblem WebP ({len(raw)} bytes, sha256={sha256})")
    print("Built: nox-emblem.webp, nox-avatar.png, nox-mark-{dark,light}.svg, nox-hero-{dark,light}.svg")


if __name__ == "__main__":
    main()
