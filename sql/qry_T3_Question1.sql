/* qry_T3_Question1 -- Benford's Law: distribution of the first digit of OSU 2014 transaction
   amounts, excluding amounts below $1.00 (which also removes credits/returns).
   Expected Benford percentages are shown beside the observed ones so that the deviation for
   each digit can be read directly from the single output. */
WITH population AS (
    SELECT CAST(substr(CAST(CAST(p.Amount AS INTEGER) AS TEXT), 1, 1) AS INTEGER) AS FirstDigit
    FROM pcards AS p
    WHERE p.Year = 2014
      AND p.AgencyName = 'OKLAHOMA STATE UNIVERSITY'
      AND p.Amount >= 1.00
),
total AS (SELECT COUNT(*) AS n FROM population)
SELECT FirstDigit                                                            AS Digit,
       COUNT(*)                                                              AS Transactions,
       ROUND(100.0 * COUNT(*) / (SELECT n FROM total), 3)                     AS ObservedPct,
       ROUND(100.0 * (LOG10(FirstDigit + 1.0) - LOG10(FirstDigit)), 3)        AS BenfordExpectedPct,
       ROUND(100.0 * COUNT(*) / (SELECT n FROM total)
             - 100.0 * (LOG10(FirstDigit + 1.0) - LOG10(FirstDigit)), 3)      AS DifferencePct
FROM population
WHERE FirstDigit BETWEEN 1 AND 9
GROUP BY FirstDigit
ORDER BY FirstDigit;
