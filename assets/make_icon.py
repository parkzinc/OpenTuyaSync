"""Genera un icono simple (no es diseño real, placeholder funcional: un
circulo tipo foco). Se corre una sola vez para generar assets/icon.ico."""

from pathlib import Path
from PIL import Image, ImageDraw

sizes = [16, 32, 48, 64, 128, 256]
imgs = []

for size in sizes:
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = size * 0.08
    d.ellipse([pad, pad, size - pad, size - pad], fill=(255, 170, 60, 255))
    # un rectangulo abajo, como la base de un foco
    bw = size * 0.28
    d.rectangle([size / 2 - bw / 2, size - size * 0.22, size / 2 + bw / 2, size - size * 0.06],
                fill=(120, 120, 120, 255))
    imgs.append(img)

out = Path(__file__).parent / 'icon.ico'
imgs[-1].save(out, format='ICO', sizes=[(s, s) for s in sizes])
print(f'icono guardado en {out}')
