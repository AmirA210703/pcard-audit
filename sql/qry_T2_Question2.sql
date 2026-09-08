/* qry_T2_Question2 -- Control 2: cardholder shall not spend more than $10,000 per month
   without approval (monthly credit limit / justification threshold) */
SELECT p.FullName                                  AS Cardholder,
       p.Month                                     AS MonthNo,
       CASE p.Month WHEN 1  THEN 'January'  WHEN 2  THEN 'February' WHEN 3  THEN 'March'
                    WHEN 4  THEN 'April'    WHEN 5  THEN 'May'      WHEN 6  THEN 'June'
                    WHEN 7  THEN 'July'     WHEN 8  THEN 'August'   WHEN 9  THEN 'September'
                    WHEN 10 THEN 'October'  WHEN 11 THEN 'November' WHEN 12 THEN 'December'
       END                                         AS MonthName,
       ROUND(SUM(p.Amount), 2)                     AS MonthlyTotal,
       COUNT(*)                                    AS Transactions
FROM pcards AS p
WHERE p.Year = 2014
  AND p.AgencyName = 'OKLAHOMA STATE UNIVERSITY'
GROUP BY p.FullName, p.Month
HAVING SUM(p.Amount) > 10000
ORDER BY p.Month ASC, MonthlyTotal DESC;
