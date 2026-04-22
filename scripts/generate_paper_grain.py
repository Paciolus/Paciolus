"""Generate a seamless 256×256 aged-paper noise PNG for Sprint 703.

Produces `frontend/public/backgrounds/paper-grain.png` — a tileable
grayscale noise texture applied at ~3% opacity via the `.paper-grain`
CSS utility. Rendered via 2D FFT with a 1/f^alpha (pink-noise-ish)
amplitude falloff, so the result is inherently periodic on the grid
(Fourier basis functions are periodic) and therefore genuinely
seamless when tiled.

Deterministic: fixed seed means the texture is stable across builds.
Re-run only when you want a different grain character.

Usage:
    python scripts/generate_paper_grain.py

Tunables:
    SIZE         — output edge length (default 256 — sprint spec)
    ALPHA_FINE   — fine-grain falloff; higher = softer (default 1.1)
    ALPHA_COARSE — coarse-blotch falloff (default 2.4)
    MIX          — fine/coarse blend weight (default 0.65 fine, 0.35 coarse)
    GAMMA        — post-normalisation gamma (default 1.2 — mildly softens
                   blown-out highlights so the texture feels aged, not crisp)
    SEED         — RNG seed for reproducibility (default 42)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

SIZE = 256
# Higher alphas = faster amplitude rolloff at high frequencies = smoother
# noise = vastly better PNG compression. Sandpaper-fine noise compresses
# terribly; aged paper reads as subtle *blotches* anyway, so we lean into
# mid-low frequencies deliberately.
ALPHA_FINE = 1.8
ALPHA_COARSE = 2.6
MIX = 0.45  # weight on fine grain — most of the character comes from coarse blotches
GAMMA = 1.2
SEED = 42
# Dynamic range (0..255 scale) — tighter range = better PNG compression.
# At 3% overlay opacity the human eye can't distinguish 16 levels from 256;
# we use 16 distinct values for sprint-budget compliance + aesthetic subtlety.
RANGE_LO = 115
RANGE_HI = 145
POSTERIZE_LEVELS = 16
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "frontend" / "public" / "backgrounds" / "paper-grain.png"


def _tileable_noise(size: int, alpha: float, seed: int) -> np.ndarray:
    """Generate size×size tileable noise with 1/f^alpha amplitude spectrum.

    The spectrum is built in the frequency domain with random phases and
    a radial amplitude falloff; inverse FFT produces a spatial field that
    is inherently periodic (because the Fourier basis is periodic on the
    sampling grid).
    """
    rng = np.random.default_rng(seed)

    # Radial frequency magnitude grid (cycles per pixel, centered)
    fx = np.fft.fftfreq(size).reshape(-1, 1)
    fy = np.fft.fftfreq(size).reshape(1, -1)
    freq = np.sqrt(fx**2 + fy**2)
    freq[0, 0] = 1.0  # avoid div-by-zero at DC

    amplitude = 1.0 / (freq**alpha)
    amplitude[0, 0] = 0.0  # zero out DC (no global bias)

    # Random phases; enforce Hermitian symmetry implicitly by taking real part.
    phase = rng.uniform(0.0, 2.0 * np.pi, (size, size))
    spectrum = amplitude * np.exp(1j * phase)

    noise = np.fft.ifft2(spectrum).real
    # Normalise to 0..1
    lo, hi = noise.min(), noise.max()
    noise = (noise - lo) / (hi - lo)
    return noise


def _render() -> Image.Image:
    fine = _tileable_noise(SIZE, ALPHA_FINE, SEED)
    coarse = _tileable_noise(SIZE, ALPHA_COARSE, SEED + 1)

    combined = MIX * fine + (1.0 - MIX) * coarse
    # Re-normalise after mixing
    lo, hi = combined.min(), combined.max()
    combined = (combined - lo) / (hi - lo)

    # Gentle gamma to soften the highlights — aged paper feels matte, not crisp.
    combined = np.power(combined, 1.0 / GAMMA)

    # Center around a neutral gray with a narrow dynamic range so the
    # overlay doesn't bias the underlying surface brightness at ~3%
    # opacity. Tight range also compresses far better in PNG.
    scaled = combined * (RANGE_HI - RANGE_LO) + RANGE_LO

    # Posterize to a small number of gray levels. At 3% opacity the eye
    # cannot distinguish 32 levels from 256, but the reduced entropy
    # drops the PNG size by ~70%.
    levels = POSTERIZE_LEVELS
    step = (RANGE_HI - RANGE_LO) / (levels - 1)
    # Quantize to the nearest step
    scaled = np.round((scaled - RANGE_LO) / step) * step + RANGE_LO
    scaled = scaled.clip(0, 255).astype(np.uint8)

    # Palette mode (P) caps the distinct pixel values to whatever the palette
    # holds, which PNG compresses much more aggressively than L-mode.
    img_l = Image.fromarray(scaled, mode="L")
    return img_l.quantize(colors=POSTERIZE_LEVELS, method=Image.Quantize.MEDIANCUT)


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    img = _render()
    img.save(OUTPUT_PATH, optimize=True, compress_level=9)
    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"Wrote {OUTPUT_PATH.relative_to(Path(__file__).resolve().parents[1])}")
    print(f"  dimensions: {img.width}×{img.height}  mode: {img.mode}")
    print(f"  size: {size_kb:.2f} KB  (sprint budget: < 15 KB)")
    if size_kb > 15:
        print(f"  WARNING: exceeds sprint budget — consider reducing range or SIZE")


if __name__ == "__main__":
    main()
