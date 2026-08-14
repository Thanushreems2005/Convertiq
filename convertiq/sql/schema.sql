-- ConvertIQ schema
-- Note: built on SQLite for portability (no server dependency), but written
-- in standard/PostgreSQL-compatible SQL. Window functions, CTEs, and joins
-- below run unmodified on PostgreSQL if migrated (swap sqlite3 -> psycopg2).

CREATE TABLE users (
    user_id           INTEGER PRIMARY KEY,
    signup_date       DATE NOT NULL,
    variant           TEXT NOT NULL,        -- 'A' (control) or 'B' (treatment)
    channel           TEXT NOT NULL,        -- organic / paid_social / referral / paid_search
    country           TEXT NOT NULL,
    kyc_complete      INTEGER NOT NULL,     -- 0/1
    first_transaction INTEGER NOT NULL,     -- 0/1 — primary conversion event
    repeat_30d        INTEGER NOT NULL      -- 0/1 — repeat activity within 30 days
);

CREATE TABLE transactions (
    user_id        INTEGER NOT NULL REFERENCES users(user_id),
    txn_date       DATE NOT NULL,
    amount         REAL NOT NULL,
    cashback_cost  REAL NOT NULL DEFAULT 0  -- incentive payout for this txn (Variant B only)
);
