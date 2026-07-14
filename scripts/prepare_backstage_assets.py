#!/usr/bin/env python3
"""Remove baked checkerboard backgrounds from approved Backstage PNG artwork."""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from PIL import Image, ImageFilter


ASSET_NAMES = (
    "pass-ticket.png",
    "fretboard-activity.png",
    "melody-activity.png",
    "lessons-activity.png",
    "brain-activity.png",
    "connected-learning.png",
    "ai-assisted.png",
)


def removable_background(pixel: tuple[int, int, int]) -> bool:
    red, green, blue = pixel
    return min(pixel) >= 150 and max(pixel) - min(pixel) <= 18


def connected_background_mask(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()
    visited = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def add(x: int, y: int) -> None:
        index = y * width + x
        if visited[index] or not removable_background(pixels[x, y]):
            return
        visited[index] = 1
        queue.append((x, y))

    for x in range(width):
        add(x, 0)
        add(x, height - 1)
    for y in range(height):
        add(0, y)
        add(width - 1, y)

    while queue:
        x, y = queue.popleft()
        if x:
            add(x - 1, y)
        if x + 1 < width:
            add(x + 1, y)
        if y:
            add(x, y - 1)
        if y + 1 < height:
            add(x, y + 1)

    foreground = Image.new("L", (width, height), 255)
    alpha = foreground.load()
    for index, is_background in enumerate(visited):
        if is_background:
            alpha[index % width, index // width] = 0
    return foreground.filter(ImageFilter.GaussianBlur(radius=0.8))


def clean_asset(source: Path, destination: Path) -> None:
    image = Image.open(source).convert("RGBA")
    image.putalpha(connected_background_mask(image))
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="PNG", optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=Path("ui/assets/backstage/originals"))
    parser.add_argument("--output-dir", type=Path, default=Path("ui/assets/backstage"))
    args = parser.parse_args()
    for name in ASSET_NAMES:
        clean_asset(args.source_dir / name, args.output_dir / name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
