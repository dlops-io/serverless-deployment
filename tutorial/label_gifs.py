#!/usr/bin/env python3
"""Add changing README step references above the existing tutorial GIF headers.

Run from any directory with Pillow installed. The adjacent JSON maps the actual
recording timeline to README steps; unnumbered sections use section references.
Existing captions, screenshots, cursor guides and frame durations are retained.
The GIF comment makes reruns replace this ribbon rather than stack ribbons.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BAND = 36
MARKER = b"ac215-readme-step-ribbon-v1"
FONT = ImageFont.truetype("DejaVuSans.ttf", 21)


def label_at(spec, milliseconds):
    if "period_ms" in spec:
        return spec["labels"][milliseconds // spec["period_ms"]]
    return next(item["label"] for item in reversed(spec["timeline"])
                if milliseconds >= item["at_ms"])


def fingerprint(image):
    return hashlib.sha256(image.tobytes()).digest()


def label_gif(item):
    name, spec = item
    path = ROOT / "images" / "console" / name
    output = path.with_suffix(".numbered.gif")
    frames, durations, originals = [], [], []
    with Image.open(path) as source:
        already_labeled = MARKER in source.info.get("comment", b"")
        elapsed = 0
        for n in range(source.n_frames):
            source.seek(n)
            rgb = source.convert("RGB")
            if already_labeled:
                rgb = rgb.crop((0, BAND, rgb.width, rgb.height))
            duration = source.info["duration"]
            label = label_at(spec, elapsed)
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
            assert draw.textbbox((12, 4), label, font=FONT)[2] < rgb.width - 12
            draw.text((12, 4), label, font=FONT, fill=foreground)
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
