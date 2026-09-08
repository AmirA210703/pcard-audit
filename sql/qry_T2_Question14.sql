/* qry_T2_Question14 -- Control 14 (student-defined): maintenance, lease/rental and service
   agreements must be processed on a requisition with a purchase order when the total for the
   year exceeds $5,000; they may not be paid as regular monthly P-card charges.
   Test: find cardholder / vendor / amount combinations where the identical amount is charged
   in at least six different months of 2014 (the signature of a fixed monthly agreement) and
   the annual total for that cardholder-vendor pair exceeds $5,000. */
WITH recurring AS (
    SELECT FullName,
           Vendor,
           Amount                      AS RecurringAmount,
           COUNT(DISTINCT Month)       AS MonthsAtSameAmount,
           COUNT(*)                    AS Charges,
           MIN(MCC)                    AS MCC
    FROM pcards
    WHERE Year = 2014
      AND AgencyName = 'OKLAHOMA STATE UNIVERSITY'
      AND Amount > 0
    GROUP BY FullName, Vendor, Amount
    HAVING COUNT(DISTINCT Month) >= 6
),
vendor_year AS (
    SELECT FullName, Vendor,
           SUM(Amount)  AS AnnualTotalWithVendor,
           COUNT(*)     AS AnnualTransactions
    FROM pcards
    WHERE Year = 2014
      AND AgencyName = 'OKLAHOMA STATE UNIVERSITY'
    GROUP BY FullName, Vendor
)
SELECT r.FullName                              AS Name,
       r.Vendor,
       r.RecurringAmount,
       r.MonthsAtSameAmount,
       r.Charges,
       ROUND(r.RecurringAmount * r.Charges, 2) AS RecurringSpend,
       ROUND(v.AnnualTotalWithVendor, 2)       AS AnnualTotalWithVendor,
       v.AnnualTransactions,
       r.MCC
FROM recurring   AS r
JOIN vendor_year AS v
  ON v.FullName = r.FullName
 AND v.Vendor   = r.Vendor
WHERE v.AnnualTotalWithVendor > 5000
ORDER BY AnnualTotalWithVendor DESC;
