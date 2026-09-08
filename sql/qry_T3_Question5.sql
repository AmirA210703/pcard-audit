/* qry_T3_Question5 (student-defined) -- Structuring just below the single-transaction limit.
   Fraud risk / hypothesis: a cardholder who repeatedly charges an amount just under the
   $5,000 single-transaction limit may be pricing purchases to stay inside the limit (or
   splitting a larger purchase) so the transaction never reaches the requisition / bid route.
   Test: 2014 positive transactions between $4,500 and $4,999.99, aggregated per cardholder,
   showing how many "near-limit" charges each cardholder made and how much of their total
   annual spend sits in that band.  To reduce false positives only cardholders with at least
   two near-limit charges are returned -- one such charge is normal pricing, a pattern is not. */
WITH near_limit AS (
    SELECT FullName,
           COUNT(*)                AS NearLimitCharges,
           ROUND(SUM(Amount), 2)   AS NearLimitValue,
           ROUND(MAX(Amount), 2)   AS LargestNearLimitCharge,
           COUNT(DISTINCT Vendor)  AS DistinctVendors
    FROM pcards
    WHERE Year = 2014
      AND AgencyName = 'OKLAHOMA STATE UNIVERSITY'
      AND Amount BETWEEN 4500 AND 4999.99
    GROUP BY FullName
    HAVING COUNT(*) >= 2
),
annual AS (
    SELECT FullName,
           SUM(Amount) AS AnnualSpend,
           COUNT(*)    AS AnnualTransactions
    FROM pcards
    WHERE Year = 2014
      AND AgencyName = 'OKLAHOMA STATE UNIVERSITY'
    GROUP BY FullName
)
SELECT n.FullName                    AS Name,
       n.NearLimitCharges,
       n.NearLimitValue,
       n.LargestNearLimitCharge,
       n.DistinctVendors,
       ROUND(a.AnnualSpend, 2)       AS AnnualSpend,
       a.AnnualTransactions,
       ROUND(100.0 * n.NearLimitValue / a.AnnualSpend, 1) AS PctOfAnnualSpendNearLimit
FROM near_limit AS n
JOIN annual     AS a ON a.FullName = n.FullName
ORDER BY n.NearLimitCharges DESC, n.NearLimitValue DESC;
