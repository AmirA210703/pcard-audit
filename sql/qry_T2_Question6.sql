/* qry_T2_Question6 -- Control 6: a purchase over $5,000 must not be split between two or
   more vendors.  Simplified to exactly two vendors; COUNT(*) = 2 removes days on which the
   cardholder made a double payment at one vendor. */
WITH parsed AS (
    SELECT p.*,
           substr(p.TransactionDate, 1, instr(p.TransactionDate, '/') - 1) AS m_raw,
           substr(p.TransactionDate, instr(p.TransactionDate, '/') + 1)    AS rest
    FROM pcards AS p
    WHERE p.Year = 2014
      AND p.AgencyName = 'OKLAHOMA STATE UNIVERSITY'
),
osu2014 AS (
    SELECT parsed.*,
           printf('%04d-%02d-%02d',
                  CAST(substr(rest, instr(rest, '/') + 1, 4) AS INTEGER),
                  CAST(m_raw AS INTEGER),
                  CAST(substr(rest, 1, instr(rest, '/') - 1) AS INTEGER)) AS TxnDate
    FROM parsed
),
flagged AS (
    SELECT FullName, TxnDate,
           SUM(Amount) AS DayTotal
    FROM osu2014
    GROUP BY FullName, TxnDate
    HAVING SUM(Amount) > 5000
       AND COUNT(DISTINCT Vendor) = 2   /* split between two different vendors */
       AND COUNT(*) = 2                 /* one transaction each -> not a double payment */
)
SELECT o.FullName            AS Name,
       o.TransactionDate,
       o.PostedDate,
       o.Vendor,
       o.Amount,
       o.Description,
       o.MCC,
       ROUND(f.DayTotal, 2)  AS CombinedDayTotal
FROM osu2014 AS o
JOIN flagged AS f
  ON f.FullName = o.FullName
 AND f.TxnDate  = o.TxnDate
ORDER BY o.TxnDate ASC, o.FullName, o.Amount DESC;
