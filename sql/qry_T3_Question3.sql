/* qry_T3_Question3 -- Employees repeatedly associated with possible duplicate payments.
   Built on the Question 2 population; an "occasion" is one date / vendor / amount cluster,
   not one transaction row, so a triple charge still counts as a single occasion. */
WITH osu2014 AS (
    SELECT *
    FROM pcards
    WHERE Year = 2014
      AND AgencyName = 'OKLAHOMA STATE UNIVERSITY'
      AND Amount > 0
),
dup_occasions AS (
    SELECT FullName,
           TransactionDate,
           Vendor,
           Amount,
           COUNT(*)    AS ChargesInOccasion,
           SUM(Amount) AS OccasionValue
    FROM osu2014
    GROUP BY TransactionDate, Vendor, CardholderFirstInitial, CardholderLastName, Amount
    HAVING COUNT(*) > 1
)
SELECT FullName                                          AS Employee,
       COUNT(*)                                          AS DuplicateOccasions,
       SUM(ChargesInOccasion)                            AS DuplicateCharges,
       ROUND(SUM(OccasionValue), 2)                      AS TotalValueOfOccasions,
       ROUND(SUM(OccasionValue - Amount), 2)             AS PotentialOverpayment
FROM dup_occasions
GROUP BY FullName
ORDER BY DuplicateOccasions DESC, PotentialOverpayment DESC;
