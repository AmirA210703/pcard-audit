/* qry_T3_Question8 (student-defined) -- Credits and returns that cannot be matched to an
   original charge.
   Fraud risk / hypothesis: the procedure requires the cardholder to check the Bank Statement
   so that returned goods are credited properly and to keep documentation of every credit.
   A credit with no corresponding charge on the same card at the same vendor can mean the
   goods were bought on a different card (or with personal funds) while the University card
   received the refund, that a merchant-side adjustment was never investigated, or simply that
   the original charge fell in the prior year.  Either way it is unsupported money movement.
   Test: every 2014 credit (negative amount), matched against the same cardholder's positive
   charges at the same vendor in 2014; report the credits with no charge of equal or larger
   value, ranked by size, plus each cardholder's overall credit activity for context. */
WITH osu2014 AS (
    SELECT * FROM pcards
    WHERE Year = 2014
      AND AgencyName = 'OKLAHOMA STATE UNIVERSITY'
),
credits AS (
    SELECT FullName, Vendor, Amount, Description, TransactionDate, PostedDate, MCC
    FROM osu2014
    WHERE Amount < 0
),
holder_activity AS (
    SELECT FullName,
           SUM(CASE WHEN Amount < 0 THEN 1 ELSE 0 END)            AS CreditsInYear,
           ROUND(SUM(CASE WHEN Amount < 0 THEN -Amount ELSE 0 END), 2) AS CreditValueInYear,
           COUNT(*)                                               AS TransactionsInYear
    FROM osu2014
    GROUP BY FullName
)
SELECT c.FullName                 AS Name,
       ROUND(-c.Amount, 2)        AS CreditAmount,
       c.Vendor,
       c.Description,
       c.TransactionDate,
       c.MCC,
       h.CreditsInYear,
       h.CreditValueInYear,
       h.TransactionsInYear
FROM credits        AS c
JOIN holder_activity AS h ON h.FullName = c.FullName
WHERE NOT EXISTS (
        SELECT 1
        FROM osu2014 AS o
        WHERE o.FullName = c.FullName
          AND o.Vendor   = c.Vendor
          AND o.Amount  >= -c.Amount      /* a charge at least as large as the credit */
      )
ORDER BY CreditAmount DESC;
