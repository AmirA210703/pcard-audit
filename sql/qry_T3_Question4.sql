/* qry_T3_Question4 -- Four-digit round-number transactions.
   Round amounts are a classic indicator of negotiated, estimated or fabricated charges
   rather than priced goods.  Returns every positive 2014 OSU transaction whose whole-dollar
   amount is four digits and ends in 000 (i.e. $1,000, $2,000 ... $9,000), cents ignored. */
SELECT p.Amount,
       p.Vendor,
       p.Description,
       p.FullName
FROM pcards AS p
WHERE p.Year = 2014
  AND p.AgencyName = 'OKLAHOMA STATE UNIVERSITY'
  AND p.Amount > 0
  AND CAST(p.Amount AS INTEGER) BETWEEN 1000 AND 9999
  AND CAST(p.Amount AS INTEGER) % 1000 = 0
ORDER BY p.Vendor ASC, p.FullName ASC;
