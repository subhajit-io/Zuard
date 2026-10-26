import math
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from PIL import Image
import cv2
from vault.brand_vault import BrandVault
import config as config

def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"

def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    clean = hex_str.lstrip("#")
    if len(clean) == 3:
        clean = "".join([c*2 for c in clean])
    return int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)

def srgb_to_linear(c: float) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def rgb_to_cielab(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """Converts sRGB [0..255] to standard CIE L*a*b* space."""
    r_lin = srgb_to_linear(r)
    g_lin = srgb_to_linear(g)
    b_lin = srgb_to_linear(b)

    # Standard Observer 2°, D65 Illuminant
    X = (r_lin * 0.4124564 + g_lin * 0.3575761 + b_lin * 0.1804375) / 0.95047
    Y = (r_lin * 0.2126729 + g_lin * 0.7151522 + b_lin * 0.0721750) / 1.00000
    Z = (r_lin * 0.0193339 + g_lin * 0.1191920 + b_lin * 0.9503041) / 1.08883

    def f(t: float) -> float:
        return t ** (1.0 / 3.0) if t > 0.008856 else (7.787 * t) + (16.0 / 116.0)

    fx = f(X)
    fy = f(Y)
    fz = f(Z)

    L = (116.0 * fy) - 16.0
    a = 500.0 * (fx - fy)
    b_val = 200.0 * (fy - fz)
    return L, a, b_val

def delta_e_cie76(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
    """Euclidean distance in CIE L*a*b* space (ΔE CIE76)."""
    return math.sqrt(
        (lab1[0] - lab2[0]) ** 2 +
        (lab1[1] - lab2[1]) ** 2 +
        (lab1[2] - lab2[2]) ** 2
    )

class VisualAuditWorker:
    def __init__(self, vault: BrandVault):
        self.vault = vault
        self._init_brand_palette()

    def _init_brand_palette(self):
        palette = self.vault.get_palette()
        self.approved_colors = []
        for key, info in palette.items():
            hex_val = info["hex"]
            rgb = hex_to_rgb(hex_val)
            lab = rgb_to_cielab(*rgb)
            self.approved_colors.append({
                "name": info.get("name", key),
                "hex": hex_val,
                "rgb": rgb,
                "lab": lab
            })
        
        vis_config = self.vault.get_visual_config()
        self.delta_e_threshold = vis_config.get("color_audit", {}).get("delta_e_threshold", config.DEFAULT_DELTA_E_THRESHOLD)
        self.prohibited_colors = vis_config.get("color_audit", {}).get("flagged_prohibited_colors", [])

    def extract_dominant_colors(self, image_path: Path, k: int = 5) -> List[Dict[str, Any]]:
        img = cv2.imread(str(image_path))
        if img is None:
            # Try PIL
            pil_img = Image.open(image_path).convert("RGB")
            img = np.array(pil_img)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # Resize for fast clustering
        small_img = cv2.resize(img_rgb, (150, 150), interpolation=cv2.INTER_AREA)
        pixels = small_img.reshape(-1, 3).astype(np.float32)

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.2)
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        counts = np.bincount(labels.flatten())
        total_pixels = len(labels.flatten())

        dominant = []
        for i in range(k):
            rgb = (int(centers[i][0]), int(centers[i][1]), int(centers[i][2]))
            hex_code = rgb_to_hex(*rgb)
            lab = rgb_to_cielab(*rgb)
            pct = round((counts[i] / total_pixels) * 100, 2)
            dominant.append({
                "hex": hex_code,
                "rgb": rgb,
                "lab": lab,
                "percentage": pct
            })

        dominant.sort(key=lambda x: x["percentage"], reverse=True)
        return dominant

    def check_colors(self, dominant_colors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        flags = []
        flag_counter = 1

        for cluster in dominant_colors:
            cluster_hex = cluster["hex"]
            cluster_lab = cluster["lab"]
            pct = cluster["percentage"]

            # Compute min Delta-E to all approved brand colors
            min_delta = float("inf")
            nearest_brand_color = None
            for approved in self.approved_colors:
                dE = delta_e_cie76(cluster_lab, approved["lab"])
                if dE < min_delta:
                    min_delta = dE
                    nearest_brand_color = approved

            # Check explicit prohibited list (e.g. #FF0055)
            is_explicit_prohibited = False
            prohibited_reason = ""
            for p in self.prohibited_colors:
                p_rgb = hex_to_rgb(p["hex"])
                p_lab = rgb_to_cielab(*p_rgb)
                if delta_e_cie76(cluster_lab, p_lab) < 15.0:
                    is_explicit_prohibited = True
                    prohibited_reason = p.get("reason", "Forbidden signature color.")
                    break

            if is_explicit_prohibited:
                flags.append({
                    "flag_id": f"VIS-{flag_counter:02d}",
                    "dimension": "visual",
                    "category": "prohibited_color",
                    "severity": "CRITICAL",
                    "snippet": f"Off-Brand Hex {cluster_hex} ({pct}% coverage)",
                    "issue": f"Forbidden color detected ({cluster_hex}). {prohibited_reason}",
                    "suggested_rewrite": f"Replace with official primary Brand Navy ({self.approved_colors[0]['hex']}) or Electric Blue ({self.approved_colors[1]['hex']}).",
                    "cited_source": "Brand Book v2, Page 13, Section 5.0: Visual Identity & Color Harmony",
                    "worker_source": "Static Worker #3 (Visual Audit)",
                    "delta_e": round(min_delta, 2),
                    "confidence_score": 1.0
                })
                flag_counter += 1
            elif min_delta > self.delta_e_threshold and pct >= 5.0:
                flags.append({
                    "flag_id": f"VIS-{flag_counter:02d}",
                    "dimension": "visual",
                    "category": "off_palette_color",
                    "severity": "WARNING",
                    "snippet": f"Unapproved Hex {cluster_hex} ({pct}% coverage, ΔE={min_delta:.1f})",
                    "issue": f"Extracted color {cluster_hex} deviates significantly (ΔE = {min_delta:.1f} > threshold {self.delta_e_threshold}) from approved palette.",
                    "suggested_rewrite": f"Map to closest brand tone: {nearest_brand_color['name']} ({nearest_brand_color['hex']}).",
                    "cited_source": "Brand Book v2, Page 13, Section 5.0: Visual Identity & Color Harmony",
                    "worker_source": "Static Worker #3 (Visual Audit)",
                    "delta_e": round(min_delta, 2),
                    "confidence_score": 0.92
                })
                flag_counter += 1

        return flags

    def check_logo_geometry(self, image_path: Path) -> List[Dict[str, Any]]:
        flags = []
        try:
            with Image.open(image_path) as img:
                w, h = img.size
                actual_ratio = w / max(1, h)
                
            expected_ratio = 3.5 # Standard Zuard horizontal logo
            tolerance_pct = config.LOGO_ASPECT_RATIO_TOLERANCE_PCT
            diff_pct = abs(actual_ratio - expected_ratio) / expected_ratio * 100.0

            if diff_pct > tolerance_pct and "logo" in image_path.name.lower():
                flags.append({
                    "flag_id": "VIS-LOGO",
                    "dimension": "visual",
                    "category": "logo_distortion",
                    "severity": "CRITICAL",
                    "snippet": f"Logo Aspect Ratio {actual_ratio:.2f}:1 (Deviation: {diff_pct:.1f}%)",
                    "issue": f"Official logo is distorted. Measured aspect ratio is {actual_ratio:.2f}:1; standard is {expected_ratio}:1 (allowed tolerance ±{tolerance_pct}%).",
                    "suggested_rewrite": f"Maintain locked aspect ratio of {expected_ratio}:1 and at least 16px clear space.",
                    "cited_source": "Brand Book v2, Page 15, Section 5.2: Visual Asset Protection & Geometry",
                    "worker_source": "Static Worker #3 (Visual Audit)",
                    "confidence_score": 0.98
                })
        except Exception:
            pass
        return flags

    def analyze_image(self, image_path: Path) -> Dict[str, Any]:
        start_time = time.perf_counter()
        if not image_path.exists():
            return {
                "worker": "Static Worker #3 (Visual Audit)",
                "execution_ms": 0.0,
                "flags": [],
                "error": "Image file not found"
            }

        dominant = self.extract_dominant_colors(image_path)
        color_flags = self.check_colors(dominant)
        logo_flags = self.check_logo_geometry(image_path)
        
        all_flags = color_flags + logo_flags
        exec_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "worker": "Static Worker #3 (Visual Audit)",
            "execution_ms": exec_ms,
            "flags": all_flags,
            "dominant_colors": dominant,
            "image_filename": image_path.name
        }
