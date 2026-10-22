#!/usr/bin/env python3
"""Render compact, single-line step captions in tutorial GIF headers.

Run from any directory with Pillow installed. The adjacent JSON maps the actual
recording timeline to README steps; unnumbered sections use descriptive labels.
The displayed number is local to the README list, not its full section path.
Screenshot bodies, cursor guides and frame durations are retained exactly.
The GIF comment makes reruns replace the header rather than stack headers.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BAND = 44
OLD_MARKER = b"ac215-readme-step-ribbon-v1"
MARKER = b"ac215-compact-step-header-v2"


def caption_at(spec, milliseconds):
    if "period_ms" in spec:
        index = milliseconds // spec["period_ms"]
        label = spec["labels"][index]
    else:
        index = next(i for i in reversed(range(len(spec["timeline"])))
                     if milliseconds >= spec["timeline"][i]["at_ms"])
        label = spec["timeline"][index]["label"]
    if label.startswith("Section"):
        prefix = "Local development" if "3.3" in label else "Helper"
    else:
        prefix = re.sub(r"\d+\.\d+\.(\d+)", r"\1", label)
    return prefix + " — " + spec["captions"][index]


def fingerprint(image):
    return hashlib.sha256(image.tobytes()).digest()


def label_gif(item):
    name, spec = item
    path = ROOT / "images" / "console" / name
    output = path.with_suffix(".numbered.gif")
    frames, durations, originals = [], [], []
    with Image.open(path) as source:
        comment = source.info.get("comment", b"")
        old_header = BAND if MARKER in comment else spec["source_header_px"] + (
            36 if OLD_MARKER in comment else 0)
        elapsed = 0
        for n in range(source.n_frames):
            source.seek(n)
            rgb = source.convert("RGB")
            rgb = rgb.crop((0, old_header, rgb.width, rgb.height))
            duration = source.info["duration"]
            label = caption_at(spec, elapsed)
            # Reuse only colors already in this frame's palette. Drawing text
            # directly in palette mode adds no antialias colors and preserves
            # every screenshot pixel exactly, checked again after GIF encoding.
            palette_frame = rgb.quantize(colors=256, dither=Image.Dither.NONE)
            palette = palette_frame.getpalette()

            def closest(color):
                return min(range(len(palette) // 3), key=lambda i: sum(
                    (palette[3 * i + j] - color[j]) ** 2 for j in range(3)))

            background = closest((24, 24, 37))
            foreground = closest((205, 214, 244))
            canvas = Image.new("P", (rgb.width, rgb.height + BAND), background)
            canvas.putpalette(palette)
            canvas.paste(palette_frame, (0, BAND))
            draw = ImageDraw.Draw(canvas)
            size = 21 if rgb.width >= 1000 else 16
            while True:
                font = ImageFont.truetype("DejaVuSans.ttf", size)
                if draw.textbbox((12, 0), label, font=font)[2] <= rgb.width - 12:
                    break
                size -= 1
                assert size >= 13, (name, label, "shorten this caption")
            bounds = draw.textbbox((0, 0), label, font=font)
            y = (BAND - (bounds[3] - bounds[1])) // 2 - bounds[1]
            draw.text((12, y), label, font=font, fill=foreground)
            assert canvas.convert("RGB").crop((0, BAND, rgb.width, rgb.height + BAND)).tobytes() == rgb.tobytes()
            originals.append((fingerprint(rgb), duration))
            frames.append(canvas)
            durations.append(duration)
            elapsed += duration
        assert elapsed == spec["duration_ms"], (name, elapsed)
        loop = source.info.get("loop", 0)

    frames[0].save(output, save_all=True, append_images=frames[1:],
                   duration=durations, loop=loop, disposal=1, optimize=False,
                   comment=MARKER)
    # Verify the encoded animation, including its complete screenshot bodies
    # and timing. This must pass before replacing the published asset.
    with Image.open(output) as encoded:
        assert encoded.n_frames == len(originals), name
        for n, (body_hash, duration) in enumerate(originals):
            encoded.seek(n)
            rgb = encoded.convert("RGB")
            body = rgb.crop((0, BAND, rgb.width, rgb.height))
            assert fingerprint(body) == body_hash, (name, n, "body changed")
            assert encoded.info["duration"] == duration, (name, n, "timing changed")
    output.replace(path)
    return f"{name}: {len(frames)} frames; original pixels and timing verified"


if __name__ == "__main__":
    mapping = json.loads(Path(__file__).with_name("gif_steps.json").read_text())
    with ThreadPoolExecutor(max_workers=3) as workers:
        for result in workers.map(label_gif, mapping.items()):
            print(result, flush=True)
