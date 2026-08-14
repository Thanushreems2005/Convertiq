"""
ConvertIQ — Synthetic Data Generator
=====================================
Simulates a fintech A/B test: two incentive structures offered to new users
signing up for a savings/spending product.

  Variant A (control):    standard 2.0% interest rate, no cashback
  Variant B (treatment):  1.5% interest rate + 3% cashback on spend

Business question this supports:
  "Does the promotional cashback incentive (Variant B) drive more users to
   convert (complete first transaction) and stay active, and is the lift
   large enough to justify the incentive cost?"

This is a SYNTHETIC dataset built to practice the kind of analysis a fintech
analytics/data science team runs. It is not real user or transaction data.
"""

import numpy as np
import pandas as pd
import sqlite3
from datetime import timedelta

np.random.seed(42)

N_USERS = 50_000
SIGNUP_WINDOW_DAYS = 90
START_DATE = pd.Timestamp("2026-01-01")

# ---------------------------------------------------------------------------
# 1. USERS: signup date, variant assignment, acquisition channel, geography
# ---------------------------------------------------------------------------

user_ids = np.arange(1, N_USERS + 1)

signup_offsets = np.random.randint(0, SIGNUP_WINDOW_DAYS, size=N_USERS)
signup_dates = START_DATE + pd.to_timedelta(signup_offsets, unit="D")

variant = np.random.choice(["A", "B"], size=N_USERS, p=[0.5, 0.5])

channel = np.random.choice(
    ["organic", "paid_social", "referral", "paid_search"],
    size=N_USERS,
    p=[0.35, 0.30, 0.15, 0.20],
)

country = np.random.choice(
    ["UK", "Poland", "Portugal", "Spain", "UAE"],
    size=N_USERS,
    p=[0.40, 0.20, 0.15, 0.15, 0.10],
)

users = pd.DataFrame({
    "user_id": user_ids,
    "signup_date": signup_dates,
    "variant": variant,
    "channel": channel,
    "country": country,
})

# ---------------------------------------------------------------------------
# 2. FUNNEL EVENTS: signup -> kyc_complete -> first_transaction -> repeat
#    Variant B gets a realistic conversion lift at each stage, with noise.
# ---------------------------------------------------------------------------

# Base conversion probabilities (Variant A / control)
p_kyc_A = 0.78
p_first_txn_A = 0.55   # conditional on KYC complete
p_repeat_30d_A = 0.40  # conditional on first transaction

# Variant B lift (the incentive is designed to nudge activation & first spend)
p_kyc_B = 0.80             # small lift — KYC isn't incentive-sensitive
p_first_txn_B = 0.61       # meaningful lift — cashback drives first spend
p_repeat_30d_B = 0.43      # modest lift — habit formation partially incentive-driven

# Channel modifier (referral users convert better regardless of variant)
channel_modifier = users["channel"].map({
    "referral": 0.06, "organic": 0.03, "paid_search": 0.0, "paid_social": -0.03
}).values

def bernoulli(p_arr):
    p_arr = np.clip(p_arr, 0.01, 0.99)
    return np.random.binomial(1, p_arr)

is_B = (users["variant"] == "B").values

p_kyc = np.where(is_B, p_kyc_B, p_kyc_A) + channel_modifier
kyc_complete = bernoulli(p_kyc)

p_first = np.where(is_B, p_first_txn_B, p_first_txn_A) + channel_modifier * 0.5
first_txn = bernoulli(p_first) * kyc_complete  # can't transact without KYC

p_repeat = np.where(is_B, p_repeat_30d_B, p_repeat_30d_A) + channel_modifier * 0.3
repeat_30d = bernoulli(p_repeat) * first_txn  # can't repeat without first txn

users["kyc_complete"] = kyc_complete
users["first_transaction"] = first_txn
users["repeat_30d"] = repeat_30d

# ---------------------------------------------------------------------------
# 3. TRANSACTIONS: for converted users, simulate a stream of transactions
#    over the 60 days following signup (for RFM / retention analysis)
# ---------------------------------------------------------------------------

txn_rows = []
converted = users[users["first_transaction"] == 1]

for row in converted.itertuples():
    # Number of transactions in the 60-day observation window
    base_txn_count = np.random.poisson(6 if row.repeat_30d else 1.5)
    n_txns = max(1, base_txn_count)

    # Variant B users spend slightly less per-txn (lower rate) but transact
    # more often (cashback habit-loop) — realistic profitability tension
    avg_amount = np.random.normal(45 if row.variant == "A" else 39, 12)
    avg_amount = max(5, avg_amount)

    txn_offsets = np.sort(np.random.randint(0, 60, size=n_txns))
    for offset in txn_offsets:
        txn_date = row.signup_date + timedelta(days=int(offset))
        amount = max(1, np.random.normal(avg_amount, 15))
        txn_rows.append((row.user_id, txn_date, round(amount, 2)))

transactions = pd.DataFrame(txn_rows, columns=["user_id", "txn_date", "amount"])

# ---------------------------------------------------------------------------
# 4. INCENTIVE COST: cashback paid out (Variant B only) — needed for the
#    profitability side of the analysis (cost vs. lift)
# ---------------------------------------------------------------------------

transactions = transactions.merge(users[["user_id", "variant"]], on="user_id")
transactions["cashback_cost"] = np.where(
    transactions["variant"] == "B", transactions["amount"] * 0.03, 0.0
)
transactions = transactions.drop(columns=["variant"])

# ---------------------------------------------------------------------------
# 5. WRITE TO SQLITE (portable, no server required — SQL is standard/
#    Postgres-compatible: same CTEs, window functions, joins apply 1:1
#    if migrated to a real Postgres instance later)
# ---------------------------------------------------------------------------

conn = sqlite3.connect("/home/claude/convertiq/data/convertiq.db")
users.to_sql("users", conn, if_exists="replace", index=False)
transactions.to_sql("transactions", conn, if_exists="replace", index=False)
conn.close()

users.to_csv("/home/claude/convertiq/data/users.csv", index=False)
transactions.to_csv("/home/claude/convertiq/data/transactions.csv", index=False)

print(f"Users: {len(users):,}")
print(f"Transactions: {len(transactions):,}")
print(f"Conversion rate A: {users[users.variant=='A'].first_transaction.mean():.3%}")
print(f"Conversion rate B: {users[users.variant=='B'].first_transaction.mean():.3%}")
print("Data written to convertiq.db, users.csv, transactions.csv")
