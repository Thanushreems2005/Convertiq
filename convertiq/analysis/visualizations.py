"""Builds the 3 core charts for the ConvertIQ write-up."""

import pandas as pd
import matplotlib.pyplot as plt

OUT = "/home/claude/convertiq/outputs"

plt.rcParams.update({"font.size": 10, "figure.dpi": 150})

# ---------------------------------------------------------------------------
# 1. Funnel conversion by variant
# ---------------------------------------------------------------------------
funnel = pd.read_csv(f"{OUT}/funnel_1.csv")

fig, ax = plt.subplots(figsize=(6, 4))
stages = ["kyc_rate_pct", "conversion_rate_pct", "repeat_rate_pct_of_converted"]
labels = ["KYC Complete", "First Transaction", "Repeat (30d)\n% of converted"]
x = range(len(stages))
width = 0.35

for i, variant in enumerate(["A", "B"]):
    row = funnel[funnel.variant == variant].iloc[0]
    vals = [row[s] for s in stages]
    offset = -width / 2 if variant == "A" else width / 2
    ax.bar([xi + offset for xi in x], vals, width, label=f"Variant {variant}")

ax.set_xticks(list(x))
ax.set_xticklabels(labels)
ax.set_ylabel("Rate (%)")
ax.set_title("Funnel Conversion: Variant A (control) vs B (incentive)")
ax.legend()
plt.tight_layout()
plt.savefig(f"{OUT}/chart_funnel.png")
plt.close()

# ---------------------------------------------------------------------------
# 2. Retention curves by variant
# ---------------------------------------------------------------------------
retention = pd.read_csv(f"{OUT}/retention_1.csv")

fig, ax = plt.subplots(figsize=(6, 4))
for variant in ["A", "B"]:
    sub = retention[retention.variant == variant].sort_values("week_number")
    ax.plot(sub.week_number, sub.retention_rate * 100, marker="o", label=f"Variant {variant}")

ax.set_xlabel("Weeks Since Signup")
ax.set_ylabel("Active Users (%)")
ax.set_title("Cohort Retention: Weekly Active Rate by Variant")
ax.legend()
plt.tight_layout()
plt.savefig(f"{OUT}/chart_retention.png")
plt.close()

# ---------------------------------------------------------------------------
# 3. Conversion lift with 95% CI + net revenue comparison (two-panel)
# ---------------------------------------------------------------------------
ab = pd.read_csv(f"{OUT}/ab_test_results.csv").set_index("metric")["value"]

fig, axes = plt.subplots(1, 2, figsize=(9, 4))

# Panel 1: lift with CI
lift = float(ab["absolute_lift_pp"])
ci_low = float(ab["lift_ci_95_low_pp"])
ci_high = float(ab["lift_ci_95_high_pp"])
axes[0].errorbar([0], [lift], yerr=[[lift - ci_low], [ci_high - lift]],
                  fmt="o", markersize=10, capsize=8, color="#004F90")
axes[0].axhline(0, color="gray", linestyle="--", linewidth=1)
axes[0].set_xlim(-1, 1)
axes[0].set_xticks([])
axes[0].set_ylabel("Conversion Lift (pp)")
axes[0].set_title(f"Conversion Lift: +{lift}pp\n95% CI [{ci_low}, {ci_high}]")

# Panel 2: net revenue per signup
rev_a = float(ab["net_revenue_per_signup_A"])
rev_b = float(ab["net_revenue_per_signup_B"])
colors = ["#004F90", "#D62728" if rev_b < 0 else "#2CA02C"]
axes[1].bar(["Variant A", "Variant B"], [rev_a, rev_b], color=colors)
axes[1].axhline(0, color="gray", linestyle="-", linewidth=0.8)
axes[1].set_ylabel("Net Revenue per Signup (currency units)")
axes[1].set_title("Unit Economics: Conversion Lift vs. Incentive Cost")

plt.tight_layout()
plt.savefig(f"{OUT}/chart_lift_and_profitability.png")
plt.close()

print("Saved: chart_funnel.png, chart_retention.png, chart_lift_and_profitability.png")
