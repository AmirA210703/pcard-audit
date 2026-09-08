/* qry_T3_Question2 -- Possible duplicate payments in the OSU 2014 data.
   A positive charge is a possible duplicate when another charge shares the same transaction
   date, vendor, cardholder first initial, cardholder last name and amount.  Credits/returns
   (negative amounts) are excluded; when more than two charges match, all of them are shown. */
WITH parsed AS (
    SELECT p.*,
           substr(p.TransactionDate, 1, instr(p.TransactionDate, '/') - 1) AS m_raw,
           substr(p.TransactionDate, instr(p.TransactionDate, '/') + 1)    AS rest
    FROM pcards AS p
    WHERE p.Year = 2014
      AND p.AgencyName = 'OKLAHOMA STATE UNIVERSITY'
      AND p.Amount > 0
),
osu2014 AS (
    SELECT parsed.*,
           printf('%04d-%02d-%02d',
                  CAST(substr(rest, instr(rest, '/') + 1, 4) AS INTEGER),
                  CAST(m_raw AS INTEGER),
                  CAST(substr(rest, 1, instr(rest, '/') - 1) AS INTEGER)) AS TxnDate
    FROM parsed
)
SELECT o.TransactionDate,
       o.Vendor,
       o.FullName,
       o.Amount
FROM osu2014 AS o
JOIN (
        SELECT TransactionDate, Vendor, CardholderFirstInitial, CardholderLastName, Amount
        FROM osu2014
        GROUP BY TransactionDate, Vendor, CardholderFirstInitial, CardholderLastName, Amount
        HAVING COUNT(*) > 1
     ) AS d
  ON  d.TransactionDate        = o.TransactionDate
  AND d.Vendor                 = o.Vendor
  AND d.CardholderFirstInitial = o.CardholderFirstInitial
  AND d.CardholderLastName     = o.CardholderLastName
  AND d.Amount                 = o.Amount
ORDER BY o.TxnDate ASC, o.Vendor ASC;
