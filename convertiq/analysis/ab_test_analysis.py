"""
ConvertIQ — Statistical Analysis
==================================
Runs the actual hypothesis tests behind the "did the incentive work?"
question, and quantifies whether the conversion lift is worth its cost.

Tests:
  1. Two-proportion z-test (chi-square equivalent) on conversion rate
  2. Independent t-test on average transaction value (spend per user)
  3. Bootstrap confidence interval on the conversion rate lift
  4. Incentive profitability: net revenue impact per user, A vs B
"""

import sqlite3
import numpy as np
import pandas as pd
from scipy import stats

conn = sqlite3.connect("/home/claude/convertiq/data/convertiq.db")
users = pd.read_sql_query("SELECT * FROM users", conn)
txns = pd.read_sql_query("SELECT * FROM transactions", conn)
conn.close()

results = {}

# ---------------------------------------------------------------------------
# 1. TWO-PROPORTION Z-TEST — is the conversion rate difference significant?
# ---------------------------------------------------------------------------

a = users[users.variant == "A"]
b = users[users.variant == "B"]

n_a, n_b = len(a), len(b)
conv_a, conv_b = a.first_transaction.sum(), b.first_transaction.sum()
p_a, p_b = conv_a / n_a, conv_b / n_b

p_pool = (conv_a + conv_b) / (n_a + n_b)
se = np.sqrt(p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b))
z = (p_b - p_a) / se
p_value = 2 * (1 - stats.norm.cdf(abs(z)))

results["conversion_rate_A"] = round(p_a, 4)
results["conversion_rate_B"] = round(p_b, 4)
results["absolute_lift_pp"] = round((p_b - p_a) * 100, 2)
results["relative_lift_pct"] = round((p_b - p_a) / p_a * 100, 2)
results["z_statistic"] = round(z, 3)
results["p_value_conversion"] = round(p_value, 6)
results["significant_at_95"] = bool(p_value < 0.05)

# ---------------------------------------------------------------------------
# 2. BOOTSTRAP 95% CONFIDENCE INTERVAL ON THE LIFT
# ---------------------------------------------------------------------------

np.random.seed(1)
n_boot = 2000
boot_lifts = []
a_conv = a.first_transaction.values
b_conv = b.first_transaction.values

for _ in range(n_boot):
    sample_a = np.random.choice(a_conv, size=len(a_conv), replace=True)
    sample_b = np.random.choice(b_conv, size=len(b_conv), replace=True)
    boot_lifts.append(sample_b.mean() - sample_a.mean())

ci_low, ci_high = np.percentile(boot_lifts, [2.5, 97.5])
results["lift_ci_95_low_pp"] = round(ci_low * 100, 2)
results["lift_ci_95_high_pp"] = round(ci_high * 100, 2)

# ---------------------------------------------------------------------------
# 3. INDEPENDENT T-TEST — avg transaction value per converted user
# ---------------------------------------------------------------------------

user_spend = txns.groupby("user_id")["amount"].sum().reset_index()
user_spend = user_spend.merge(users[["user_id", "variant"]], on="user_id")

spend_a = user_spend[user_spend.variant == "A"]["amount"]
spend_b = user_spend[user_spend.variant == "B"]["amount"]

t_stat, t_pvalue = stats.ttest_ind(spend_b, spend_a, equal_var=False)

results["avg_spend_A"] = round(spend_a.mean(), 2)
results["avg_spend_B"] = round(spend_b.mean(), 2)
results["t_statistic_spend"] = round(t_stat, 3)
results["p_value_spend"] = round(t_pvalue, 6)

# Effect size (Cohen's d)
pooled_std = np.sqrt(((spend_a.std() ** 2) + (spend_b.std() ** 2)) / 2)
cohens_d = (spend_b.mean() - spend_a.mean()) / pooled_std
results["cohens_d_spend"] = round(cohens_d, 3)

# ---------------------------------------------------------------------------
# 4. INCENTIVE PROFITABILITY — net revenue impact per signed-up user
# ---------------------------------------------------------------------------

txns_a = txns[txns.user_id.isin(a.user_id)]
txns_b = txns[txns.user_id.isin(b.user_id)]

gross_revenue_a = txns_a["amount"].sum() * 0.02   # 2% take-rate proxy, variant A
gross_revenue_b = txns_b["amount"].sum() * 0.015  # 1.5% take-rate proxy, variant B
cashback_cost_b = txns_b["cashback_cost"].sum()

net_revenue_a = gross_revenue_a
net_revenue_b = gross_revenue_b - cashback_cost_b

revenue_per_signup_a = net_revenue_a / n_a
revenue_per_signup_b = net_revenue_b / n_b

results["gross_revenue_A"] = round(gross_revenue_a, 2)
results["gross_revenue_B"] = round(gross_revenue_b, 2)
results["cashback_cost_B"] = round(cashback_cost_b, 2)
results["net_revenue_A"] = round(net_revenue_a, 2)
results["net_revenue_B"] = round(net_revenue_b, 2)
results["net_revenue_per_signup_A"] = round(revenue_per_signup_a, 3)
results["net_revenue_per_signup_B"] = round(revenue_per_signup_b, 3)
results["net_revenue_lift_per_signup"] = round(revenue_per_signup_b - revenue_per_signup_a, 3)
results["incentive_worth_it"] = bool(revenue_per_signup_b > revenue_per_signup_a)

# ---------------------------------------------------------------------------
# SAVE RESULTS
# ---------------------------------------------------------------------------

results_df = pd.DataFrame(list(results.items()), columns=["metric", "value"])
results_df.to_csv("/home/claude/convertiq/outputs/ab_test_results.csv", index=False)

print("=" * 60)
print("A/B TEST RESULTS SUMMARY")
print("=" * 60)
for k, v in results.items():
    print(f"{k:35s}: {v}")
