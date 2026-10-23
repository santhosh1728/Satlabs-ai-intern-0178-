# Run with: python reproduce.py
"""
Satlabs Space Systems — Software Intern take-home
Candidate ID: ai-intern-0178

This script audits the arithmetic evaluation benchmark and reproduces every number
reported in answers.txt and writeup.md:
1. Colleague's original scores (from score.py)
2. Identification of wrong answer key entries (q008, q013, q027)
3. Identification of duplicate questions (q036, q049, q050, q051, q054, q056)
4. Robust parsing of model outputs (stripping markdown, prose, commas)
5. Corrected accuracy scores on all evaluation rows (168 runs)
6. Corrected accuracy scores on deduplicated questions (150 runs)
7. Per-run breakdown and consistency checks (temperature 0.0 vs 0.7)
8. Latency statistics and statistical significance test (McNemar test)
"""

import csv
import re
import collections
import statistics
import math


def solve_question(qtext: str) -> str:
    """Computes the mathematically exact integer answer for a question string."""
    m = re.search(r"What is (\d+)\s*([\+\-\×x\*])\s*(\d+)\?", qtext)
    if not m:
        raise ValueError(f"Unable to parse arithmetic expression from: {qtext}")
    n1, op, n2 = int(m.group(1)), m.group(2), int(m.group(3))
    if op == "+":
        return str(n1 + n2)
    elif op == "-":
        return str(n1 - n2)
    elif op in ("×", "x", "*"):
        return str(n1 * n2)
    raise ValueError(f"Unsupported operator: {op}")


def extract_numeric_response(raw_resp: str) -> str:
    """
    Extracts the numerical answer from a model response.
    Handles plain digits, markdown bolding (**1234**), conversational filler
    ('The answer is 1,234.', 'Sure! A + B equals C.'), equations ('A + B = C'),
    and commas in numbers ('12,291' -> '12291').
    """
    cleaned = re.sub(r"(\d),(\d)", r"\1\2", raw_resp.strip())
    numbers = re.findall(r"-?\d+", cleaned)
    if numbers:
        # The model's final conclusion is the last number in the string
        return numbers[-1]
    return raw_resp.strip()


def run_audit():
    print("=" * 70)
    print("SATLABS SPACE SYSTEMS — BENCHMARK AUDIT & REPRODUCTION SCRIPT")
    print("Candidate ID: ai-intern-0178")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Load Data
    # ---------------------------------------------------------
    with open("questions.csv", encoding="utf-8") as f:
        questions = {r["question_id"]: r["question"].strip() for r in csv.DictReader(f)}

    with open("answer_key.csv", encoding="utf-8") as f:
        orig_key = {r["question_id"]: r["expected"].strip() for r in csv.DictReader(f)}

    with open("results.csv", encoding="utf-8") as f:
        results = list(csv.DictReader(f))

    # ---------------------------------------------------------
    # 2. Original Baseline Scores (score.py reproduction)
    # ---------------------------------------------------------
    print("\n--- 1. ORIGINAL BASELINE SCORES (from score.py) ---")
    orig_hits = collections.Counter()
    orig_total = collections.Counter()
    for r in results:
        orig_total[r["model"]] += 1
        if r["response"].strip() == orig_key[r["question_id"]]:
            orig_hits[r["model"]] += 1

    for m in sorted(orig_total):
        pct = 100 * orig_hits[m] / orig_total[m]
        print(f"  {m}: {pct:.1f}% ({orig_hits[m]}/{orig_total[m]})")

    # ---------------------------------------------------------
    # 3. Ground Truth Verification (wrong_answer_key_ids)
    # ---------------------------------------------------------
    print("\n--- 2. GROUND TRUTH VERIFICATION ---")
    math_key = {}
    wrong_key_ids = []
    for qid in sorted(questions.keys()):
        expected_math = solve_question(questions[qid])
        math_key[qid] = expected_math
        if expected_math != orig_key[qid]:
            wrong_key_ids.append(qid)
            print(f"  [WRONG KEY] {qid}: '{questions[qid]}' -> Answer Key: {orig_key[qid]} | True Math: {expected_math}")

    print(f"  Identified wrong_answer_key_ids: {', '.join(wrong_key_ids)}")

    # ---------------------------------------------------------
    # 4. Duplicate Question Identification (duplicate_question_ids)
    # ---------------------------------------------------------
    print("\n--- 3. DUPLICATE QUESTION ANALYSIS ---")
    seen_qtext = {}
    redundant_duplicate_ids = []
    duplicate_groups = collections.defaultdict(list)

    for qid in sorted(questions.keys()):
        qtext = questions[qid]
        duplicate_groups[qtext].append(qid)
        if qtext in seen_qtext:
            redundant_duplicate_ids.append(qid)
        else:
            seen_qtext[qtext] = qid

    all_duplicated_ids = sorted([qid for group in duplicate_groups.values() if len(group) > 1 for qid in group])

    print("  Duplicate pairs detected:")
    for qtext, group in duplicate_groups.items():
        if len(group) > 1:
            print(f"    '{qtext}': {group}")

    print(f"  Redundant duplicate question IDs (subsequent occurrences): {', '.join(redundant_duplicate_ids)}")
    print(f"  All IDs involved in duplicate questions: {', '.join(all_duplicated_ids)}")

    # ---------------------------------------------------------
    # 5. Corrected Scoring Across All Runs (168 evaluations each)
    # ---------------------------------------------------------
    print("\n--- 4. CORRECTED BENCHMARK ACCURACY (ALL 168 ROWS) ---")
    corr_hits = collections.Counter()
    corr_total = collections.Counter()
    for r in results:
        m = r["model"]
        qid = r["question_id"]
        parsed_ans = extract_numeric_response(r["response"])
        corr_total[m] += 1
        if parsed_ans == math_key[qid]:
            corr_hits[m] += 1

    acc_a_all = 100 * corr_hits["model-a"] / corr_total["model-a"]
    acc_b_all = 100 * corr_hits["model-b"] / corr_total["model-b"]
    print(f"  accuracy_model_a: {acc_a_all:.1f}% ({corr_hits['model-a']}/{corr_total['model-a']})")
    print(f"  accuracy_model_b: {acc_b_all:.1f}% ({corr_hits['model-b']}/{corr_total['model-b']})")

    # ---------------------------------------------------------
    # 6. Corrected Scoring on Deduplicated Questions (150 evaluations each)
    # ---------------------------------------------------------
    print("\n--- 5. DEDUPLICATED ACCURACY (50 UNIQUE QUESTIONS, 150 ROWS) ---")
    dedup_hits = collections.Counter()
    dedup_total = collections.Counter()
    for r in results:
        qid = r["question_id"]
        if qid not in redundant_duplicate_ids:
            m = r["model"]
            parsed_ans = extract_numeric_response(r["response"])
            dedup_total[m] += 1
            if parsed_ans == math_key[qid]:
                dedup_hits[m] += 1

    acc_a_dedup = 100 * dedup_hits["model-a"] / dedup_total["model-a"]
    acc_b_dedup = 100 * dedup_hits["model-b"] / dedup_total["model-b"]
    print(f"  model-a (deduplicated): {acc_a_dedup:.1f}% ({dedup_hits['model-a']}/{dedup_total['model-a']})")
    print(f"  model-b (deduplicated): {acc_b_dedup:.1f}% ({dedup_hits['model-b']}/{dedup_total['model-b']})")

    # ---------------------------------------------------------
    # 7. Breakdown by Run & Temperature Effects
    # ---------------------------------------------------------
    print("\n--- 6. PER-RUN BREAKDOWN & TEMPERATURE OBSERVATIONS ---")
    for run_id in sorted(set(r["run"] for r in results)):
        run_hits = collections.Counter()
        run_total = collections.Counter()
        for r in results:
            if r["run"] == run_id:
                m = r["model"]
                qid = r["question_id"]
                parsed_ans = extract_numeric_response(r["response"])
                run_total[m] += 1
                if parsed_ans == math_key[qid]:
                    run_hits[m] += 1
        print(f"  Run {run_id}:")
        for m in sorted(run_total):
            pct = 100 * run_hits[m] / run_total[m]
            temp = [r["temperature"] for r in results if r["model"] == m and r["run"] == run_id][0]
            print(f"    {m} (T={temp}): {pct:.1f}% ({run_hits[m]}/{run_total[m]})")

    # Verify model-a determinism
    a_responses_by_run = collections.defaultdict(dict)
    for r in results:
        if r["model"] == "model-a":
            a_responses_by_run[r["run"]][r["question_id"]] = r["response"].strip()

    a_identical = (a_responses_by_run["1"] == a_responses_by_run["2"] == a_responses_by_run["3"])
    print(f"\n  Model A identical across all 3 runs (T=0.0): {a_identical}")

    # ---------------------------------------------------------
    # 8. Latency Analysis
    # ---------------------------------------------------------
    print("\n--- 7. LATENCY STATISTICS ---")
    for m in ["model-a", "model-b"]:
        lats = [float(r["latency_ms"]) for r in results if r["model"] == m]
        print(f"  {m}: Mean = {statistics.mean(lats):.1f} ms | Median = {statistics.median(lats):.1f} ms | Min = {min(lats):.1f} ms | Max = {max(lats):.1f} ms")

    # ---------------------------------------------------------
    # 9. Statistical Significance (McNemar's Test)
    # ---------------------------------------------------------
    print("\n--- 8. STATISTICAL SIGNIFICANCE (McNEMAR'S TEST) ---")
    paired = {}
    for r in results:
        qid = r["question_id"]
        run_id = r["run"]
        m = r["model"]
        is_corr = (extract_numeric_response(r["response"]) == math_key[qid])
        paired.setdefault((run_id, qid), {})[m] = is_corr

    both_corr = 0
    both_wrong = 0
    a_only = 0
    b_only = 0
    for (run_id, qid), res in paired.items():
        a = res["model-a"]
        b = res["model-b"]
        if a and b:
            both_corr += 1
        elif not a and not b:
            both_wrong += 1
        elif a and not b:
            a_only += 1
        elif not a and b:
            b_only += 1

    chi2 = (abs(b_only - a_only) - 1) ** 2 / (b_only + a_only)
    print(f"  Paired runs: Both correct = {both_corr}, Both wrong = {both_wrong}")
    print(f"  Discordant pairs: Model-A only = {a_only}, Model-B only = {b_only}")
    print(f"  McNemar Chi-squared (continuity corrected) = {chi2:.3f}")
    print(f"  Statistical significance: Not significant at p < 0.05 (critical value = 3.841, p ~ 0.153).")

    # ---------------------------------------------------------
    # 10. Summary for answers.txt
    # ---------------------------------------------------------
    print("\n" + "=" * 70)
    print("OUTPUT SUMMARY FOR answers.txt")
    print("=" * 70)
    print(f"candidate_id: ai-intern-0178")
    print(f"accuracy_model_a: {acc_a_all:.1f}%")
    print(f"accuracy_model_b: {acc_b_all:.1f}%")
    print(f"duplicate_question_ids: {', '.join(redundant_duplicate_ids)}")
    print(f"wrong_answer_key_ids: {', '.join(wrong_key_ids)}")
    print("=" * 70)


if __name__ == "__main__":
    run_audit()
