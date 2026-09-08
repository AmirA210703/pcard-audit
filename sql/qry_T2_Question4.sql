/* qry_T2_Question4 -- Control 4: an amount over $5,000 must not be split between two or
   more swipes of the same card at the same vendor on the same day. */
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
flagged AS (                       /* cardholder + vendor + day groups that break the rule */
    SELECT FullName, Vendor, TxnDate,
           COUNT(*)    AS SwipesThatDay,
           SUM(Amount) AS DayTotal
    FROM osu2014
    GROUP BY FullName, Vendor, TxnDate
    HAVING COUNT(*) > 1
       AND SUM(Amount) > 5000
)
SELECT o.FullName            AS Name,
       o.Vendor,
       o.TransactionDate,
       o.PostedDate,
       o.Amount,
       o.Description,
       o.MCC,
       f.SwipesThatDay,
       ROUND(f.DayTotal, 2)  AS CombinedDayTotal
FROM osu2014 AS o
JOIN flagged AS f
  ON f.FullName = o.FullName
 AND f.Vendor   = o.Vendor
 AND f.TxnDate  = o.TxnDate
ORDER BY o.TxnDate ASC, o.FullName, o.Vendor, o.Amount DESC;
