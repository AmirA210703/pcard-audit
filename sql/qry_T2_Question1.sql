/* qry_T2_Question1 -- Control 1: cardholder shall not spend more than $50,000 per year */
SELECT p.FullName                    AS Cardholder,
       ROUND(SUM(p.Amount), 2)       AS TotalSpent2014,
       COUNT(*)                      AS Transactions
FROM pcards AS p
WHERE p.Year = 2014
  AND p.AgencyName = 'OKLAHOMA STATE UNIVERSITY'
GROUP BY p.FullName
HAVING SUM(p.Amount) > 50000
ORDER BY TotalSpent2014 DESC;
