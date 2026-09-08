/* qry_T2_Question3 -- Control 3: single transaction limit of $5,000 */
SELECT p.Amount,
       p.FullName          AS Name,
       p.Description,
       p.Vendor,
       p.TransactionDate,
       p.PostedDate,
       p.MCC
FROM pcards AS p
WHERE p.Year = 2014
  AND p.AgencyName = 'OKLAHOMA STATE UNIVERSITY'
  AND p.Amount > 5000
ORDER BY p.Amount DESC;
