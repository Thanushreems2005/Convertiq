# ConvertIQ — Fintech Incentive A/B Test & Profitability Analysis

**A SQL + statistics case study on whether a promotional cashback incentive
drives user conversion, and whether that conversion is actually profitable.**

> **Note on data:** This project uses a synthetically generated dataset built
> to model realistic fintech user/transaction behavior. It is not real user
> data — public fintech transaction data isn't available for this kind of
> analysis, so the dataset was designed with deliberately noisy, realistic
> effect sizes rather than an artificially clean signal.

---

## Business Question

A fintech product team is testing two account structures for new signups:

| | Variant A (control) | Variant B (treatment) |
|---|---|---|
| Interest rate | 2.0% | 1.5% |
| Cashback on spend | — | 3.0% |

**Does the cashback incentive (Variant B) increase user conversion and
retention — and if so, is the lift large enough to justify what the
incentive costs?**

This mirrors the kind of question a product/data analytics team evaluates
when weighing interest rate or incentive changes against profitability.

---

## Method

1. **Data generation** — 50,000 synthetic users across a 90-day signup
   window, randomly assigned to Variant A/B, with a simulated funnel
   (signup → KYC → first transaction → 30-day repeat activity) and a
   transaction stream for converted users. [`data/generate_data.py`](data/generate_data.py)

2. **SQL analysis** (SQLite; PostgreSQL-compatible syntax — CTEs, window
   functions, `NTILE`) — [`sql/`](sql/)
   - `funnel_conversion.sql` — conversion rate by variant and channel
   - `cohort_retention.sql` — weekly signup-cohort retention curves
   - `rfm_segmentation.sql` — Recency/Frequency/Monetary user segmentation

3. **Statistical testing** — [`analysis/ab_test_analysis.py`](analysis/ab_test_analysis.py)
   - Two-proportion z-test on conversion rate
   - Bootstrap 95% confidence interval on the conversion lift
   - Independent t-test + Cohen's d on average spend per user
   - Net revenue per signup, accounting for cashback payout cost

4. **Visualization** — [`analysis/visualizations.py`](analysis/visualizations.py)

---

## Results

### 1. Conversion — statistically significant lift

| | Variant A | Variant B |
|---|---|---|
| Conversion rate | 43.77% | 50.15% |

- **Absolute lift: +6.38pp** (relative lift: +14.6%)
- **z = 14.30, p < 0.001** — highly significant
- **95% bootstrap CI: [5.51pp, 7.24pp]** — the lift is real, not noise

![Funnel conversion](outputs/chart_funnel.png)

### 2. Retention — the lift holds up over time, not just at signup

Weekly active-user retention among converted users is consistently higher
for Variant B across all 8 observed weeks, not just at the first-transaction
moment — ruling out "the incentive just pulls forward a transaction that
would've happened anyway."

![Cohort retention](outputs/chart_retention.png)

### 3. Profitability — the incentive is not worth its cost, as priced

This is the critical finding: **despite the significant conversion lift,
Variant B is unprofitable.**

| | Variant A | Variant B |
|---|---|---|
| Net revenue per signup | +1.36 | **−1.05** |

The 3% cashback payout outweighs both the conversion lift and the lower
take-rate revenue per transaction. Variant B users also converted more
"cheaply" — average spend per converted user is *lower* in B (140.05 vs.
155.54), meaning the incentive attracts a higher volume of lower-value
transactors rather than proportionally better ones.

![Lift and profitability](outputs/chart_lift_and_profitability.png)

---

## Recommendation

**Do not roll out Variant B as priced.** The cashback incentive works as a
conversion lever — the lift is real and durable — but at a 3% cashback rate
it costs more than it returns. The recommended next step is a **follow-up
test at a lower cashback rate (1–1.5%)** to find the point where conversion
lift and incentive cost break even, rather than treating "conversion went
up" as sufficient justification on its own.

This is the core tension a pricing/incentive analyst has to hold: a metric
moving in the right direction isn't the same as a decision that's good for
the business.

---

## Tech Stack

`Python` · `SQL (SQLite, PostgreSQL-compatible)` · `Pandas` · `NumPy` ·
`SciPy` (hypothesis testing, bootstrap) · `Matplotlib`

## Repo Structure

```
convertiq/
├── data/
│   └── generate_data.py       # synthetic data generator
├── sql/
│   ├── schema.sql
│   ├── funnel_conversion.sql
│   ├── cohort_retention.sql
│   └── rfm_segmentation.sql
├── analysis/
│   ├── run_sql_queries.py
│   ├── ab_test_analysis.py
│   └── visualizations.py
├── outputs/                   # generated CSVs + charts
└── README.md
```
