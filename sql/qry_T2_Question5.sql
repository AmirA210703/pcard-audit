/* qry_T2_Question5 -- Control 5: a purchase over $5,000 must not be split between two or
   more cardholders.  Simplified to exactly two cardholders; the COUNT(*) = 2 condition
   removes days on which one of the two cardholders made a double payment at that vendor. */
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
    SELECT Vendor, TxnDate,
           SUM(Amount) AS DayTotal
    FROM osu2014
    GROUP BY Vendor, TxnDate
    HAVING SUM(Amount) > 5000
       AND COUNT(DISTINCT FullName) = 2   /* split between two different cardholders */
       AND COUNT(*) = 2                   /* one transaction each -> not a double payment */
)
SELECT o.Vendor,
       o.TransactionDate,
       o.PostedDate,
       o.FullName            AS Name,
       o.Amount,
       o.Description,
       o.MCC,
       ROUND(f.DayTotal, 2)  AS CombinedVendorDayTotal
FROM osu2014 AS o
JOIN flagged AS f
  ON f.Vendor  = o.Vendor
 AND f.TxnDate = o.TxnDate
ORDER BY o.TxnDate ASC, o.Vendor, o.Amount DESC;
