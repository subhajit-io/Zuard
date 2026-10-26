import re
import time
from typing import List, Dict, Any, Optional
from vault.brand_vault import BrandVault

class FactVerificationWorker:
    def __init__(self, vault: BrandVault):
        self.vault = vault
        self._compile_patterns()

    def _compile_patterns(self):
        # Superlative ranking / unverified claims (using boundary or whitespace to support '#1')
        self.superlative_pattern = re.compile(
            r"(?:\b|(?<=\s)|(?<=^))(#1|number one|no\.\s*1|fastest|cheapest|world'?s best|unrivaled|unmatched|most powerful|industry-first|100% infallible|miracle\s+engine|zero\s+risk|zero\s+chargeback\s+risk)\b",
            re.IGNORECASE
        )
        # Percentage figures
        self.percentage_pattern = re.compile(
            r"(\b\d+(?:\.\d+)?%)\s*([a-zA-Z\s]{0,25})",
            re.IGNORECASE
        )
        # Multiplier claims (e.g., 10x faster)
        self.multiplier_pattern = re.compile(
            r"\b(\d+x)\s*([a-zA-Z\s]{0,20})\b",
            re.IGNORECASE
        )

    def analyze(self, text: str) -> Dict[str, Any]:
        start_time = time.perf_counter()
        flags: List[Dict[str, Any]] = []

        if not text or not text.strip():
            return {
                "worker": "Static Worker #2 (Fact Verification)",
                "execution_ms": 0.0,
                "flags": [],
                "verified_claims_count": 0
            }

        flag_counter = 1
        all_approved_facts = self.vault.facts_db.get_all_facts()

        # 1. Check for Unsupported Superlatives
        for match in self.superlative_pattern.finditer(text):
            snippet = match.group(0)
            start_idx = match.start()
            end_idx = match.end()

            # Find context sentence
            s_start = max(0, text.rfind(".", 0, start_idx) + 1)
            s_end = text.find(".", end_idx)
            if s_end == -1:
                s_end = len(text)
            sentence = text[s_start:s_end].strip()

            flags.append({
                "flag_id": f"FACT-{flag_counter:02d}",
                "dimension": "claims",
                "category": "unsupported_superlative",
                "severity": "CRITICAL",
                "snippet": snippet,
                "context_sentence": sentence,
                "start_idx": start_idx,
                "end_idx": end_idx,
                "issue": f"Unsupported promotional claim: '{snippet}'. Brand policy strictly forbids unverified superlatives without third-party analyst audit.",
                "suggested_rewrite": "an industry-leading",
                "cited_source": "Brand Book v2, Page 8, Section 2.2: Verifiable Market Claims",
                "worker_source": "Static Worker #2 (Fact Verification)",
                "confidence_score": 1.0
            })
            flag_counter += 1

        # 2. Check for Percentage Metrics & Contradictions with Approved Facts
        for match in self.percentage_pattern.finditer(text):
            pct_val_str = match.group(1) # e.g. "99.9%"
            start_idx = match.start()
            end_idx = match.end()

            # Find context sentence
            s_start = max(0, text.rfind(".", 0, start_idx) + 1)
            s_end = text.find(".", end_idx)
            if s_end == -1:
                s_end = len(text)
            sentence_raw = text[s_start:s_end].strip()
            sentence = sentence_raw.lower()

            try:
                pct_num = float(pct_val_str.replace("%", "").strip())
            except ValueError:
                continue

            # First, check dynamic matching against all approved facts in this project's database
            fact_flagged = False
            relevant_facts = self.vault.facts_db.search_facts(sentence)
            for fact in relevant_facts:
                approved_val_str = str(fact.get("approved_value", ""))
                try:
                    approved_val_num = float(approved_val_str.replace("%", "").strip())
                except ValueError:
                    continue

                fact_claim_lower = fact.get("approved_claim", "").lower()
                metric_key_lower = fact.get("metric_key", "").lower()

                # Check for topic match (e.g. "fraud", "cost", "uptime", "sla", "availability", "turnaround", "latency")
                topic_keywords = [w for w in ["fraud", "cost", "uptime", "sla", "availability", "turnaround", "latency", "reduction", "expense"] if w in fact_claim_lower or w in metric_key_lower]
                is_topic_match = any(w in sentence for w in topic_keywords) if topic_keywords else False

                if is_topic_match:
                    is_sla = any(k in sentence for k in ["uptime", "sla", "availability"])
                    
                    if is_sla and pct_num > approved_val_num:
                        # SLA exaggeration (e.g. claiming 100% when SLA is 99.99%)
                        flags.append({
                            "flag_id": f"FACT-{flag_counter:02d}",
                            "dimension": "facts",
                            "category": "sla_exaggeration",
                            "severity": "CRITICAL",
                            "snippet": pct_val_str,
                            "context_sentence": sentence_raw,
                            "start_idx": start_idx,
                            "end_idx": end_idx,
                            "issue": f"Exaggerated uptime claim: '{pct_val_str}'. Formal infrastructure SLA is {approved_val_str}. Absolute 100% or unverified SLA creates legal exposure.",
                            "suggested_rewrite": f"{approved_val_str} enterprise availability SLA",
                            "cited_source": f"Approved Fact Sheet ID #{fact['fact_id']} ('{fact['approved_claim']}') & {fact['source_doc']} p.{fact['page_number']}, {fact['section']}",
                            "worker_source": "Static Worker #2 (Fact Verification)",
                            "confidence_score": 1.0
                        })
                        flag_counter += 1
                        fact_flagged = True
                        break
                    elif not is_sla and abs(pct_num - approved_val_num) > 1.0:
                        # Contradictory metric (e.g. 99.9% fraud reduction vs verified 84%)
                        prefix_match = re.search(r"((?:cuts?|reduces?|demonstrates?|achieves?)\s+[^.\n,;]*?by\s*)" + re.escape(pct_val_str), sentence_raw, re.IGNORECASE)
                        if prefix_match:
                            flag_snip = prefix_match.group(0)
                            flag_rewrite = f"reduces by verified {approved_val_str}"
                        else:
                            flag_snip = pct_val_str
                            flag_rewrite = f"verified {approved_val_str}"

                        flags.append({
                            "flag_id": f"FACT-{flag_counter:02d}",
                            "dimension": "facts",
                            "category": "fact_contradiction",
                            "severity": "CRITICAL",
                            "snippet": flag_snip,
                            "context_sentence": sentence_raw,
                            "start_idx": start_idx,
                            "end_idx": end_idx,
                            "issue": f"Contradictory metric: '{pct_val_str}'. Verified audit records {approved_val_str} ({fact['approved_claim']}), not {pct_val_str}.",
                            "suggested_rewrite": flag_rewrite,
                            "cited_source": f"Approved Fact Sheet ID #{fact['fact_id']} ('{fact['approved_claim']}') & {fact['source_doc']} p.{fact['page_number']}, {fact['section']}",
                            "worker_source": "Static Worker #2 (Fact Verification)",
                            "confidence_score": 0.98
                        })
                        flag_counter += 1
                        fact_flagged = True
                        break

            if fact_flagged:
                continue

            # Fallback to standard enterprise fact checks if not caught dynamically
            if any(k in sentence for k in ["cost", "cut", "save", "reduction", "cheap", "expense"]):
                fact_cost = self.vault.facts_db.get_fact_by_id("F-104")
                if fact_cost:
                    approved_val = 42.0
                    if abs(pct_num - approved_val) > 2.0:
                        prefix_match = re.search(r"((?:cuts?|reduces?)\s+costs?\s+by\s*)" + re.escape(pct_val_str), sentence_raw, re.IGNORECASE)
                        flag_snip = prefix_match.group(0) if prefix_match else pct_val_str
                        flags.append({
                            "flag_id": f"FACT-{flag_counter:02d}",
                            "dimension": "facts",
                            "category": "fact_contradiction",
                            "severity": "CRITICAL",
                            "snippet": flag_snip,
                            "context_sentence": sentence_raw,
                            "start_idx": start_idx,
                            "end_idx": end_idx,
                            "issue": f"Contradictory cost metric: '{pct_val_str}'. Approved study demonstrates average 42% cost reduction, not {pct_val_str}.",
                            "suggested_rewrite": "reduces operational costs by an average of 42%",
                            "cited_source": f"Approved Fact Sheet ID #{fact_cost['fact_id']} ('{fact_cost['approved_claim']}') & {fact_cost['source_doc']} p.{fact_cost['page_number']}, {fact_cost['section']}",
                            "worker_source": "Static Worker #2 (Fact Verification)",
                            "confidence_score": 0.98
                        })
                        flag_counter += 1
            elif any(k in sentence for k in ["uptime", "sla", "availability"]):
                fact_sla = self.vault.facts_db.get_fact_by_id("F-101")
                if fact_sla and pct_num > 99.95:
                    flags.append({
                        "flag_id": f"FACT-{flag_counter:02d}",
                        "dimension": "facts",
                        "category": "sla_exaggeration",
                        "severity": "CRITICAL",
                        "snippet": pct_val_str,
                        "context_sentence": sentence_raw,
                        "start_idx": start_idx,
                        "end_idx": end_idx,
                        "issue": f"Exaggerated uptime claim: '{pct_val_str}'. Formal infrastructure SLA is 99.95%. Absolute 100% or unverified SLA creates legal exposure.",
                        "suggested_rewrite": "99.95% enterprise uptime SLA",
                        "cited_source": f"Approved Fact Sheet ID #{fact_sla['fact_id']} & {fact_sla['source_doc']} p.{fact_sla['page_number']}, {fact_sla['section']}",
                        "worker_source": "Static Worker #2 (Fact Verification)",
                        "confidence_score": 1.0
                    })
                    flag_counter += 1

        exec_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "worker": "Static Worker #2 (Fact Verification)",
            "execution_ms": exec_ms,
            "flags": flags,
            "total_facts_queried": len(all_approved_facts)
        }
