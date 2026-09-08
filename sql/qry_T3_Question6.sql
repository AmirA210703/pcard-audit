/* qry_T3_Question6 (student-defined) -- Weekend and public-holiday purchasing.
   Fraud risk / hypothesis: P-card purchases made when the University is closed are less
   likely to have been pre-approved by the department and are a recognised indicator of
   personal use of a business card.
   Test: 2014 positive transactions dated on a Saturday, a Sunday or a 2014 federal holiday.
   To keep the population meaningful, merchant categories where weekend activity is expected
   and legitimate (lodging, airlines, car rental, restaurants, fuel, tolls) are excluded, and
   only cardholders with at least five such charges are reported. */
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
),
closed_days AS (
    SELECT *,
           CASE WHEN CAST(strftime('%w', TxnDate) AS INTEGER) = 0 THEN 'Sunday'
                WHEN CAST(strftime('%w', TxnDate) AS INTEGER) = 6 THEN 'Saturday'
                ELSE 'Holiday' END AS DayType
    FROM osu2014
    WHERE CAST(strftime('%w', TxnDate) AS INTEGER) IN (0, 6)
       OR TxnDate IN ('2014-01-01','2014-01-20','2014-05-26','2014-07-04',
                      '2014-09-01','2014-11-27','2014-11-28','2014-12-24',
                      '2014-12-25','2014-12-31')
),
non_travel AS (
    SELECT * FROM closed_days
    WHERE MCC NOT LIKE '%HOTEL%'   AND MCC NOT LIKE '%MOTEL%'
      AND MCC NOT LIKE '%INN%'     AND MCC NOT LIKE '%RESORT%'
      AND MCC NOT LIKE '%LODGING%' AND MCC NOT LIKE '%SUITES%'
      AND MCC NOT LIKE '%AIRLINE%' AND MCC NOT LIKE '%AIR%'
      AND MCC NOT LIKE '%CAR RENTAL%' AND MCC NOT LIKE '%AUTOMOBILE RENTAL%'
      AND MCC NOT LIKE '%RESTAURANT%' AND MCC NOT LIKE '%EATING%'
      AND MCC NOT LIKE '%FOOD%'    AND MCC NOT LIKE '%CATER%'
      AND MCC NOT LIKE '%SERVICE STATION%' AND MCC NOT LIKE '%FUEL%'
      AND MCC NOT LIKE '%TOLL%'    AND MCC NOT LIKE '%TAXI%'
      AND MCC NOT LIKE '%TRANSPORTATION%' AND MCC NOT LIKE '%TRAVEL%'
      AND MCC NOT LIKE '%PARKING%'
)
SELECT FullName                                                AS Name,
       COUNT(*)                                                AS ClosedDayCharges,
       ROUND(SUM(Amount), 2)                                   AS ClosedDayValue,
       SUM(CASE WHEN DayType = 'Holiday'  THEN 1 ELSE 0 END)    AS OnHolidays,
       SUM(CASE WHEN DayType = 'Saturday' THEN 1 ELSE 0 END)    AS OnSaturdays,
       SUM(CASE WHEN DayType = 'Sunday'   THEN 1 ELSE 0 END)    AS OnSundays,
       COUNT(DISTINCT Vendor)                                   AS DistinctVendors,
       ROUND(MAX(Amount), 2)                                    AS LargestCharge
FROM non_travel
GROUP BY FullName
HAVING COUNT(*) >= 5
ORDER BY ClosedDayValue DESC;
