# Benchmark Audit Writeup

### 1. Measurement Flaws in the Original Setup
The original 71.4% vs 41.1% comparison was flawed:
- **Scoring logic:** `score.py` required exact string equality. Model-A output bare digits, but Model-B included markdown bolding, conversational phrases, and commas (`1,292`), causing correct answers to fail.
- **Flawed key:** `answer_key.csv` had three arithmetic errors: `q008` (4926 vs 4296), `q013` (2156 vs 2166), and `q027` (8339 vs 8340).
- **Inconsistent temperature:** Model-A used temperature 0.0 (fully deterministic across runs 1–3), while Model-B used 0.7.
- **Duplicate items:** Six questions (`q036, q049, q050, q051, q054, q056`) duplicated earlier items.

### 2. Changes and Corrected Numbers
We corrected the three key errors and extracted numeric values from responses:
- **Full benchmark (168 runs):** Model-A: **76.8%** (129/168); Model-B: **83.3%** (140/168).
- **Deduplicated benchmark (50 unique questions, 150 runs):** Model-A: **74.0%** (111/150); Model-B: **86.7%** (130/150).

### 3. Is Model-A Better Than Model-B?
No. The colleague's claim does not hold; Model-B achieved higher accuracy. However, we cannot conclude Model-B is genuinely superior. A McNemar test on paired trials yields $\chi^2 = 2.041$ ($p \approx 0.153$), which is not statistically significant at $\alpha = 0.05$. The temperature disparity also confounds the comparison.

### 4. What the Numbers Do Not Prove
- **Broad capability:** The test covers only simple two-operand arithmetic, not complex reasoning or domain tasks.
- **Operational suitability:** Model-B is ~57% slower (mean latency 1514 ms vs 964 ms), generates more tokens, and fails concise formatting constraints.
