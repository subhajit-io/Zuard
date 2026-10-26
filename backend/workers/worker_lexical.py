import re
import time
from typing import List, Dict, Any
import textstat
from vault.brand_vault import BrandVault
import config as config

class LexicalStyleWorker:
    def __init__(self, vault: BrandVault):
        self.vault = vault
        self._compile_patterns()
        # Warm up textstat cache once during initialization
        try:
            textstat.flesch_reading_ease("Warmup")
        except Exception:
            pass

    def _compile_patterns(self):
        terms = self.vault.get_terms()
        # Sort terms by length descending to prioritize longer phrases (e.g. 'super cheap' before 'cheap')
        sorted_terms = sorted(terms, key=lambda x: len(x["term"]), reverse=True)
        self.compiled_rules = []
        for item in sorted_terms:
            term = item["term"]
            pattern = re.compile(rf"(?:\b|(?<=\s)|(?<=^)){re.escape(term)}\b", re.IGNORECASE)
            self.compiled_rules.append({
                "rule": item,
                "pattern": pattern
            })

    def analyze(self, text: str) -> Dict[str, Any]:
        start_time = time.perf_counter()
        flags: List[Dict[str, Any]] = []

        if not text or not text.strip():
            return {
                "worker": "Static Worker #1 (Lexical & Style)",
                "execution_ms": 0.0,
                "flags": [],
                "metrics": {}
            }

        # 1. Banned & Deprecated Terminology Scanning (Deterministic Regex)
        flag_counter = 1
        occupied_spans = []

        for cr in self.compiled_rules:
            rule = cr["rule"]
            pattern = cr["pattern"]
            for match in pattern.finditer(text):
                start_idx = match.start()
                end_idx = match.end()

                # Check if this span is already covered by a longer term
                is_subspan = any(
                    (start_idx >= o_start and end_idx <= o_end)
                    for o_start, o_end in occupied_spans
                )
                if is_subspan:
                    continue

                matched_snippet = match.group(0)
                occupied_spans.append((start_idx, end_idx))
                
                # Context sentence
                s_start = max(0, text.rfind(".", 0, start_idx) + 1)
                s_end = text.find(".", end_idx)
                if s_end == -1:
                    s_end = len(text)
                sentence = text[s_start:s_end].strip()

                cited_doc = rule.get("cited_doc", "Brand Guide v2")
                page = rule.get("page", 4)
                sec = rule.get("section", "Terminology Standards")
                citation = f"{cited_doc}, Page {page}, {sec}"

                flags.append({
                    "flag_id": f"LEX-{flag_counter:02d}",
                    "dimension": "terminology" if rule.get("category") != "pricing_tone" else "tone",
                    "category": rule.get("category", "banned_terms"),
                    "severity": rule.get("severity", "WARNING"),
                    "snippet": matched_snippet,
                    "context_sentence": sentence,
                    "start_idx": start_idx,
                    "end_idx": end_idx,
                    "issue": f"Forbidden term detected: '{matched_snippet}'. {rule.get('rationale', '')}",
                    "preferred_replacement": rule.get("preferred", ""),
                    "suggested_rewrite": rule.get("preferred", ""),
                    "cited_source": citation,
                    "worker_source": "Static Worker #1 (Lexical & Style)",
                    "confidence_score": 1.0
                })
                flag_counter += 1

        # 2. Tone & Readability Metrics (Textstat)
        flesch_reading_ease = textstat.flesch_reading_ease(text)
        flesch_kincaid_grade = textstat.flesch_kincaid_grade(text)
        sentence_count = max(1, textstat.sentence_count(text))
        avg_sentence_length = textstat.lexicon_count(text, removepunct=True) / sentence_count

        readability_flags = []
        if flesch_kincaid_grade > config.DEFAULT_READING_GRADE_MAX:
            readability_flags.append({
                "flag_id": f"LEX-{flag_counter:02d}",
                "dimension": "tone",
                "category": "reading_complexity",
                "severity": "WARNING",
                "snippet": f"Overall text reading grade: {flesch_kincaid_grade:.1f}",
                "context_sentence": "Entire draft",
                "start_idx": 0,
                "end_idx": min(len(text), 80),
                "issue": f"Reading grade level ({flesch_kincaid_grade:.1f}) exceeds enterprise guideline ceiling (Grade {config.DEFAULT_READING_GRADE_MAX}). Simplify phrasing.",
                "preferred_replacement": "Simpler sentence structures",
                "suggested_rewrite": "Target clear, concise language (Grade 8-11).",
                "cited_source": "Brand Book v2, Page 3, Section 1.2: Reading Level & Sentence Complexity",
                "worker_source": "Static Worker #1 (Lexical & Style)",
                "confidence_score": 0.95
            })
            flag_counter += 1
        elif flesch_reading_ease < config.DEFAULT_READING_EASE_MIN and len(text) > 100:
            readability_flags.append({
                "flag_id": f"LEX-{flag_counter:02d}",
                "dimension": "tone",
                "category": "reading_ease",
                "severity": "WARNING",
                "snippet": f"Flesch Reading Ease: {flesch_reading_ease:.1f}",
                "context_sentence": "Entire draft",
                "start_idx": 0,
                "end_idx": min(len(text), 80),
                "issue": f"Text reading ease ({flesch_reading_ease:.1f}) is below minimum target ({config.DEFAULT_READING_EASE_MIN}). Text is overly dense.",
                "preferred_replacement": "Break long compound sentences into shorter statements.",
                "suggested_rewrite": "Target Reading Ease score 55.0 to 75.0.",
                "cited_source": "Brand Book v2, Page 3, Section 1.2: Reading Level & Sentence Complexity",
                "worker_source": "Static Worker #1 (Lexical & Style)",
                "confidence_score": 0.90
            })
            flag_counter += 1

        flags.extend(readability_flags)
        exec_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "worker": "Static Worker #1 (Lexical & Style)",
            "execution_ms": exec_ms,
            "flags": flags,
            "metrics": {
                "flesch_reading_ease": round(flesch_reading_ease, 2),
                "flesch_kincaid_grade": round(flesch_kincaid_grade, 2),
                "sentence_count": sentence_count,
                "avg_sentence_length": round(avg_sentence_length, 2)
            }
        }
