-- RFM segmentation (Recency, Frequency, Monetary) for converted users,
-- scored into quartiles per variant using window functions (NTILE).
-- Answers: does the incentive attract higher-value users, or just more
-- low-value, one-off transactors?

WITH user_txn_stats AS (
    SELECT
        u.user_id,
        u.variant,
        u.channel,
        JULIANDAY('2026-06-01') - JULIANDAY(MAX(t.txn_date)) AS recency_days,
        COUNT(t.user_id)                                     AS frequency,
        SUM(t.amount)                                        AS monetary
    FROM users u
    JOIN transactions t ON t.user_id = u.user_id
    WHERE u.first_transaction = 1
    GROUP BY u.user_id, u.variant, u.channel
),
rfm_scores AS (
    SELECT
        *,
        NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,   -- lower recency_days = better
        NTILE(4) OVER (ORDER BY frequency ASC)      AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC)       AS m_score
    FROM user_txn_stats
)
SELECT
    variant,
    CASE
        WHEN r_score + f_score + m_score >= 10 THEN 'High Value'
        WHEN r_score + f_score + m_score >= 7  THEN 'Mid Value'
        ELSE 'Low Value'
    END AS segment,
    COUNT(*)                       AS users,
    ROUND(AVG(monetary), 2)        AS avg_monetary,
    ROUND(AVG(frequency), 2)       AS avg_frequency
FROM rfm_scores
GROUP BY variant, segment
ORDER BY variant, segment;
