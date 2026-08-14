-- Weekly signup-cohort retention: of users who converted (first_transaction=1),
-- what share are still transacting in each subsequent week?
-- Uses CTEs + window functions (ROW_NUMBER, running aggregation).

WITH signup_cohorts AS (
    SELECT
        user_id,
        variant,
        DATE(signup_date, 'weekday 0', '-6 days') AS cohort_week   -- start of ISO-ish week
    FROM users
    WHERE first_transaction = 1
),
txn_weeks AS (
    SELECT
        t.user_id,
        c.variant,
        c.cohort_week,
        CAST(
            (JULIANDAY(t.txn_date) - JULIANDAY(c.cohort_week)) / 7
            AS INTEGER
        ) AS week_number
    FROM transactions t
    JOIN signup_cohorts c ON c.user_id = t.user_id
),
weekly_actives AS (
    SELECT
        variant,
        cohort_week,
        week_number,
        COUNT(DISTINCT user_id) AS active_users
    FROM txn_weeks
    WHERE week_number BETWEEN 0 AND 8
    GROUP BY variant, cohort_week, week_number
),
cohort_size AS (
    SELECT variant, cohort_week, COUNT(DISTINCT user_id) AS cohort_users
    FROM signup_cohorts
    GROUP BY variant, cohort_week
)
SELECT
    w.variant,
    w.week_number,
    SUM(w.active_users) * 1.0 / SUM(c.cohort_users) AS retention_rate
FROM weekly_actives w
JOIN cohort_size c
    ON c.variant = w.variant AND c.cohort_week = w.cohort_week
GROUP BY w.variant, w.week_number
ORDER BY w.variant, w.week_number;
