import time
from typing import List, Dict, Any, Tuple, Optional
from vault.brand_vault import BrandVault
import config as config
from .worker_visual import hex_to_rgb, srgb_to_linear

def calculate_relative_luminance(r: int, g: int, b: int) -> float:
    """Calculates WCAG relative luminance: L = 0.2126*R + 0.7152*G + 0.0722*B"""
    r_lin = srgb_to_linear(r)
    g_lin = srgb_to_linear(g)
    b_lin = srgb_to_linear(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

def calculate_contrast_ratio(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
    """Calculates WCAG contrast ratio: (L1 + 0.05) / (L2 + 0.05)"""
    l1 = calculate_relative_luminance(*rgb1)
    l2 = calculate_relative_luminance(*rgb2)
    l_max = max(l1, l2)
    l_min = min(l1, l2)
    return (l_max + 0.05) / (l_min + 0.05)

class WCAGAccessibilityWorker:
    def __init__(self, vault: BrandVault):
        self.vault = vault
        vis_config = self.vault.get_visual_config()
        wcag_cfg = vis_config.get("wcag_accessibility", {})
        self.aa_normal_min = wcag_cfg.get("aa_normal_text_min_contrast", config.WCAG_AA_NORMAL_TEXT_CONTRAST)
        self.aa_large_min = wcag_cfg.get("aa_large_text_min_contrast", config.WCAG_AA_LARGE_TEXT_CONTRAST)
        self.aaa_min = wcag_cfg.get("aaa_normal_text_min_contrast", config.WCAG_AAA_CONTRAST)
        self.min_alt_len = wcag_cfg.get("min_alt_text_length", 15)

    def evaluate_contrast(self, fg_hex: str, bg_hex: str, is_large_text: bool = False) -> Dict[str, Any]:
        fg_rgb = hex_to_rgb(fg_hex)
        bg_rgb = hex_to_rgb(bg_hex)
        ratio = round(calculate_contrast_ratio(fg_rgb, bg_rgb), 2)
        required_min = self.aa_large_min if is_large_text else self.aa_normal_min

        passed_aa = ratio >= required_min
        passed_aaa = ratio >= self.aaa_min

        flag = None
        if not passed_aa:
            flag = {
                "flag_id": "ACC-CONTRAST",
                "dimension": "accessibility",
                "category": "color_contrast_failure",
                "severity": "CRITICAL",
                "snippet": f"FG: {fg_hex} on BG: {bg_hex} (Ratio: {ratio}:1)",
                "issue": f"WCAG 2.1 AA Contrast Failure. Measured contrast ratio is {ratio}:1, which is below the mandatory minimum {required_min}:1.",
                "suggested_rewrite": f"Increase lightness contrast: use high-contrast foreground (e.g. #FFFFFF on dark backgrounds or #0F172A on light backgrounds).",
                "cited_source": "Brand Book v2, Page 14, Section 5.1: WCAG Accessibility Standards",
                "worker_source": "Static Worker #4 (Accessibility)",
                "measured_ratio": ratio,
                "required_minimum": required_min,
                "confidence_score": 1.0
            }

        return {
            "ratio": ratio,
            "required_min": required_min,
            "passed_aa": passed_aa,
            "passed_aaa": passed_aaa,
            "flag": flag
        }

    def check_alt_text(self, alt_text: Optional[str], asset_name: str = "visual_banner") -> Optional[Dict[str, Any]]:
        vague_placeholders = ["image", "banner", "picture", "photo", "graphic", "screenshot", "logo", "asset.png"]
        
        if not alt_text or not alt_text.strip():
            return {
                "flag_id": "ACC-ALT-MISSING",
                "dimension": "accessibility",
                "category": "missing_alt_text",
                "severity": "CRITICAL",
                "snippet": f"Asset: {asset_name} (alt: None)",
                "issue": f"Missing alt-text on visual asset '{asset_name}'. Screen readers cannot interpret this creative.",
                "suggested_rewrite": f"Add descriptive alt-text outlining image contents, text overlays, and key takeaway.",
                "cited_source": "Brand Book v2, Page 14, Section 5.1: WCAG Accessibility Standards",
                "worker_source": "Static Worker #4 (Accessibility)",
                "confidence_score": 1.0
            }
        
        clean_alt = alt_text.strip().lower()
        if clean_alt in vague_placeholders or len(clean_alt) < self.min_alt_len:
            return {
                "flag_id": "ACC-ALT-VAGUE",
                "dimension": "accessibility",
                "category": "vague_alt_text",
                "severity": "WARNING",
                "snippet": f"alt='{alt_text}' ({len(clean_alt)} chars)",
                "issue": f"Alt-text '{alt_text}' is too brief or generic (< {self.min_alt_len} chars). Fails WCAG descriptive context criteria.",
                "suggested_rewrite": f"Provide meaningful description (e.g., 'Promotional banner announcing Zuard automated pre-screening dashboard').",
                "cited_source": "Brand Book v2, Page 14, Section 5.1: WCAG Accessibility Standards",
                "worker_source": "Static Worker #4 (Accessibility)",
                "confidence_score": 0.95
            }

        return None

    def analyze(self, 
                color_pairs: Optional[List[Tuple[str, str]]] = None,
                alt_texts: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        start_time = time.perf_counter()
        flags = []

        # Default checks if color pairs provided
        contrast_results = []
        if color_pairs:
            for fg, bg in color_pairs:
                res = self.evaluate_contrast(fg, bg)
                contrast_results.append(res)
                if res["flag"]:
                    flags.append(res["flag"])

        # Check alt-texts
        if alt_texts:
            for item in alt_texts:
                alt = item.get("alt")
                name = item.get("asset_name", "asset")
                flag = self.check_alt_text(alt, name)
                if flag:
                    flags.append(flag)

        exec_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "worker": "Static Worker #4 (Accessibility)",
            "execution_ms": exec_ms,
            "flags": flags,
            "contrast_evaluations": contrast_results
        }
