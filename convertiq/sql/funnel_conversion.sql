-- Funnel conversion by variant: signup -> KYC -> first transaction -> repeat (30d)
-- Answers: at which stage does the incentive (Variant B) actually move the needle?

SELECT
    variant,
    COUNT(*)                                            AS signups,
    SUM(kyc_complete)                                   AS kyc_completed,
    ROUND(100.0 * SUM(kyc_complete) / COUNT(*), 2)      AS kyc_rate_pct,
    SUM(first_transaction)                              AS converted,
    ROUND(100.0 * SUM(first_transaction) / COUNT(*), 2) AS conversion_rate_pct,
    SUM(repeat_30d)                                     AS repeat_active,
    ROUND(100.0 * SUM(repeat_30d) / NULLIF(SUM(first_transaction), 0), 2)
                                                         AS repeat_rate_pct_of_converted
FROM users
GROUP BY variant
ORDER BY variant;


-- Same funnel broken down by acquisition channel, to check whether the
-- incentive lift is consistent across channels or concentrated in one.

SELECT
    channel,
    variant,
    COUNT(*)                                            AS signups,
    ROUND(100.0 * SUM(first_transaction) / COUNT(*), 2) AS conversion_rate_pct
FROM users
GROUP BY channel, variant
ORDER BY channel, variant;
