/* qry_T2_Question7 -- Control 7: food (and mileage) while in travel status is prohibited on
   the P-card; it must be claimed as per diem on a travel voucher.
   Travel status is inferred from a lodging MCC (hotel / motel / resort / inn) on the same
   day for the same cardholder; the rows returned are that day's food / restaurant charges. */
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
lodging_days AS (                  /* cardholder-days that look like travel status */
    SELECT DISTINCT FullName, TxnDate
    FROM osu2014
    WHERE MCC LIKE '%hotel%'
       OR MCC LIKE '%motel%'
       OR MCC LIKE '%resort%'
       OR MCC LIKE '%inn%'
)
SELECT o.FullName        AS Name,
       o.Amount,
       o.Vendor,
       o.Description,
       o.TransactionDate,
       o.PostedDate,
       o.MCC
FROM osu2014 AS o
JOIN lodging_days AS l
  ON l.FullName = o.FullName
 AND l.TxnDate  = o.TxnDate
WHERE o.MCC LIKE '%food%'
   OR o.MCC LIKE '%restaurant%'
ORDER BY o.FullName ASC, o.Amount ASC;
