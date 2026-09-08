/* qry_T2_Question9 -- Control 9 (student-defined): Gasoline is a prohibited P-card purchase;
   fuel must be bought from Transportation Services or with the vehicle's gasoline card.
   Test: 2014 transactions at fuel-selling MCCs, summarised by cardholder so that the
   auditor can see who is using the P-card for fuel repeatedly. */
SELECT p.FullName                  AS Name,
       COUNT(*)                    AS FuelTransactions,
       ROUND(SUM(p.Amount), 2)     AS TotalFuelSpend,
       ROUND(MAX(p.Amount), 2)     AS LargestSingleCharge,
       COUNT(DISTINCT p.Vendor)    AS DistinctFuelVendors
FROM pcards AS p
WHERE p.Year = 2014
  AND p.AgencyName = 'OKLAHOMA STATE UNIVERSITY'
  AND (   p.MCC LIKE '%SERVICE STATION%'
       OR p.MCC LIKE '%AUTOMATED FUEL DISPENSER%'
       OR p.MCC LIKE '%FUEL DEALERS%')
GROUP BY p.FullName
ORDER BY TotalFuelSpend DESC;
