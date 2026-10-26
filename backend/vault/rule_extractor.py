import re
from typing import List, Dict, Any, Tuple

class DynamicRuleExtractor:
    """
    Analyzes ingested guideline text chunks to automatically extract:
    1. Banned and preferred terminology
    2. Quantitative factual claims and metrics
    3. Brand hex colors and visual guidelines (approved palette & prohibited colors)
    """

    def __init__(self):
        # Hex color pattern (#FFFFFF or #0F172A)
        self.hex_pattern = re.compile(r'(#[0-9A-Fa-f]{6})')

        # Factual claims patterns (percentages, SLAs, customer counts, turnaround time, currency)
        self.claim_patterns = [
            # Uptime / SLA / Availability
            re.compile(r'(\d+(?:\.\d+)?%)\s*(?:core\s+ledger\s+transaction\s+availability|enterprise\s+platform\s+uptime|uptime|sla|availability)', re.IGNORECASE),
            # Fraud reduction / Cost reduction / Generic reduction
            re.compile(r'(\d+(?:\.\d+)?%)\s*(?:average\s+)?(?:operational\s+)?(?:cost\s+reduction|reduction\s+in\s+[^".\n,;]+)', re.IGNORECASE),
            # Turnaround time
            re.compile(r'(\d+(?:\.\d+)?\s*(?:seconds?|s|ms|minutes?))\s*(?:average\s+)?(?:turnaround|response|pre-screening)', re.IGNORECASE),
            # Financial Volume / Currency
            re.compile(r'(\$\d+(?:\.\d+)?\s*(?:billion|million|trillion|B|M))(?:\s+in\s+[^".\n,;]+)?', re.IGNORECASE),
            # Customer traction
            re.compile(r'over\s+(\d+\+?|\d+,\d+)\s+enterprise\s+customers', re.IGNORECASE)
        ]

    def extract_from_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        extracted_terms = []
        extracted_facts = []
        extracted_colors = []
        extracted_prohibited_colors = []
        delta_e_override = None

        seen_terms = set()
        seen_facts = set()
        seen_hex = set()
        seen_prohibited_hex = set()

        for chunk in chunks:
            text = chunk.get("content", "")
            doc_name = chunk.get("doc_name", "Uploaded_Guide.pdf")
            page_num = chunk.get("page_number", 1)
            section = chunk.get("section", "Guidelines")

            # -------------------------------------------------------------
            # 1. EXTRACT TERMINOLOGY RULES
            # -------------------------------------------------------------
            # Instead of "X", use "Y"
            for m in re.finditer(r'instead\s+of\s+["\']([^"\']+)["\']\s*,\s*use\s+["\']([^"\']+)["\']', text, re.IGNORECASE):
                banned = m.group(1).strip()
                pref = m.group(2).strip()
                if banned.lower() not in seen_terms:
                    seen_terms.add(banned.lower())
                    extracted_terms.append({
                        "term": banned,
                        "category": "dynamic_guideline",
                        "severity": "WARNING",
                        "preferred": pref,
                        "rationale": f"Explicitly replaced in {section}.",
                        "cited_doc": doc_name,
                        "page": page_num,
                        "section": section
                    })

            # Replace "X" with "Y"
            for m in re.finditer(r'replace\s+["\']([^"\']+)["\']\s+with\s+["\']([^"\']+)["\']', text, re.IGNORECASE):
                banned = m.group(1).strip()
                pref = m.group(2).strip()
                if banned.lower() not in seen_terms:
                    seen_terms.add(banned.lower())
                    extracted_terms.append({
                        "term": banned,
                        "category": "dynamic_guideline",
                        "severity": "WARNING",
                        "preferred": pref,
                        "rationale": f"Rule from {section}.",
                        "cited_doc": doc_name,
                        "page": page_num,
                        "section": section
                    })

            # "X" is permanently retired / deprecated; use "Y" instead
            for m in re.finditer(r'["\']([^"\']+)["\']\s+is\s+(?:permanently\s+)?(?:retired|deprecated|phased out).*?(?:use|replace with)\s+["\']([^"\']+)["\']', text, re.IGNORECASE):
                banned = m.group(1).strip()
                pref = m.group(2).strip()
                if banned.lower() not in seen_terms:
                    seen_terms.add(banned.lower())
                    extracted_terms.append({
                        "term": banned,
                        "category": "deprecated_product",
                        "severity": "CRITICAL",
                        "preferred": pref,
                        "rationale": f"Legacy product retired. Replace with official title '{pref}'.",
                        "cited_doc": doc_name,
                        "page": page_num,
                        "section": section
                    })

            # Legacy product / architecture "X" is retired ... use "Y"
            for m in re.finditer(r'(?:legacy|former)\s+(?:product|architecture|name)?\s*["\']([^"\']+)["\'].*?(?:retired|deprecated).*?(?:use|replace with)\s+["\']([^"\']+)["\']', text, re.IGNORECASE):
                banned = m.group(1).strip()
                pref = m.group(2).strip()
                if banned.lower() not in seen_terms:
                    seen_terms.add(banned.lower())
                    extracted_terms.append({
                        "term": banned,
                        "category": "deprecated_product",
                        "severity": "CRITICAL",
                        "preferred": pref,
                        "rationale": f"Legacy architecture retired in {section}. Replace with '{pref}'.",
                        "cited_doc": doc_name,
                        "page": page_num,
                        "section": section
                    })

            # Terms like "X", "Y" are strictly forbidden / prohibited (optional: use "Z")
            for m in re.finditer(r'terms?\s+like\s+["\']([^"\']+)["\'](?:\s*,\s*["\']([^"\']+)["\'])?.*?are\s+(?:strictly\s+)?(?:forbidden|banned|prohibited)(?:[^\n.;]*?(?:use|replace with)\s+["\']([^"\']+)["\'])?', text, re.IGNORECASE):
                t1 = m.group(1).strip()
                t2 = m.group(2).strip() if m.group(2) else None
                pref = m.group(3).strip() if m.group(3) else "professional enterprise alternative"

                if t1.lower() not in seen_terms:
                    seen_terms.add(t1.lower())
                    extracted_terms.append({
                        "term": t1,
                        "category": "pricing_tone" if "cheap" in t1.lower() else "banned_terms",
                        "severity": "CRITICAL",
                        "preferred": pref,
                        "rationale": f"Declared strictly forbidden in {section}.",
                        "cited_doc": doc_name,
                        "page": page_num,
                        "section": section
                    })
                if t2 and t2.lower() not in seen_terms:
                    seen_terms.add(t2.lower())
                    extracted_terms.append({
                        "term": t2,
                        "category": "pricing_tone" if "cheap" in t2.lower() else "banned_terms",
                        "severity": "CRITICAL",
                        "preferred": pref,
                        "rationale": f"Declared strictly forbidden in {section}.",
                        "cited_doc": doc_name,
                        "page": page_num,
                        "section": section
                    })

            # -------------------------------------------------------------
            # 2. EXTRACT FACTS (Percentages, SLAs, Metrics, Volume)
            # -------------------------------------------------------------
            lines = text.split("\n")
            for line in lines:
                for cp in self.claim_patterns:
                    for match in cp.finditer(line):
                        metric_val = match.group(1).strip()
                        claim_snippet = match.group(0).strip()
                        
                        # Check for Study ID / SLA ID / Metric ID in line
                        id_match = re.search(r'(?:Study|Metric|Fact|SLA)\s+ID\s*#?([A-Za-z0-9\-]+)', line, re.IGNORECASE)
                        if id_match:
                            fact_id = id_match.group(1).strip()
                        else:
                            fact_id = f"F-AUTO-{len(extracted_facts)+1:02d}"

                        if fact_id not in seen_facts:
                            seen_facts.add(fact_id)
                            
                            # Determine category and metric_key
                            cat = "performance"
                            metric_key = "benchmark"
                            line_lower = line.lower()
                            if "fraud" in line_lower:
                                cat = "security_benchmark"
                                metric_key = "fraud_reduction"
                            elif "cost" in line_lower or "save" in line_lower:
                                cat = "financial_impact"
                                metric_key = "cost_reduction"
                            elif "uptime" in line_lower or "sla" in line_lower or "availability" in line_lower:
                                cat = "infrastructure_sla"
                                metric_key = "uptime_sla"
                            elif "volume" in line_lower or "$" in metric_val:
                                cat = "scale_metrics"
                                metric_key = "transaction_volume"

                            # Clean approved claim
                            clean_claim = line.strip().lstrip("0123456789.-*\" ").rstrip("\" ")
                            if len(clean_claim) > 100:
                                clean_claim = clean_claim[:100] + "..."

                            extracted_facts.append({
                                "fact_id": fact_id,
                                "category": cat,
                                "metric_key": metric_key,
                                "approved_claim": clean_claim,
                                "approved_value": metric_val,
                                "unit": "percent" if "%" in metric_val else ("currency" if "$" in metric_val else "metric"),
                                "source_doc": doc_name,
                                "page_number": page_num,
                                "section": section,
                                "verified_date": "Dynamic Ingestion",
                                "notes": f"Auto-extracted from {doc_name}."
                            })

            # -------------------------------------------------------------
            # 3. EXTRACT VISUAL RULES & COLORS
            # -------------------------------------------------------------
            # Check for Delta-E tolerance override
            de_match = re.search(r'delta[- ]e\s+tolerance\s+is\s+(?:fixed\s+at\s+)?(\d+(?:\.\d+)?)', text, re.IGNORECASE)
            if de_match:
                try:
                    delta_e_override = float(de_match.group(1))
                except ValueError:
                    pass

            # Prohibited colors vs Approved palette
            is_prohibited_section = any(k in section.lower() or k in text.lower() for k in ["prohibited color", "banned color", "forbidden color"])
            
            for line in lines:
                line_lower = line.lower()
                is_line_prohibited = any(k in line_lower for k in ["prohibited", "banned", "forbidden", "conflict"])
                
                for m in re.finditer(r'(#[0-9A-Fa-f]{6})', line):
                    hex_code = m.group(1).upper()
                    
                    # Extract descriptive name if present before hex
                    start_pos = max(0, m.start() - 35)
                    prev_text = line[start_pos:m.start()].strip()
                    color_name = "Brand Hue"
                    name_match = re.search(r'([A-Za-z\s]+)(?:is|\(|:|-)?$', prev_text)
                    if name_match:
                        cand = name_match.group(1).strip().lstrip("-:* ")
                        if len(cand) > 2 and len(cand) < 25:
                            color_name = cand.title()

                    if is_prohibited_section or is_line_prohibited:
                        if hex_code not in seen_prohibited_hex:
                            seen_prohibited_hex.add(hex_code)
                            extracted_prohibited_colors.append({
                                "name": color_name,
                                "hex": hex_code,
                                "reason": f"Prohibited color specified in {section}."
                            })
                    else:
                        if hex_code not in seen_hex and hex_code not in ["#000000", "#FFFFFF"]:
                            seen_hex.add(hex_code)
                            extracted_colors.append({
                                "name": color_name,
                                "hex": hex_code,
                                "usage": f"Extracted from {doc_name} ({section})"
                            })

        return {
            "terms": extracted_terms,
            "facts": extracted_facts,
            "colors": extracted_colors,
            "prohibited_colors": extracted_prohibited_colors,
            "delta_e_threshold": delta_e_override
        }
