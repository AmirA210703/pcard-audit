/* qry_T3_Question7 (student-defined) -- Sole-cardholder vendor concentration.
   Fraud risk / hypothesis: the procedure forbids purchases from friends and family, from a
   company owned by a University employee, and from any company in which the cardholder has a
   financial interest.  A shell or related-party vendor typically shows up as a vendor that
   only ONE cardholder in the whole University ever uses, that receives a material amount of
   money, and that is billed repeatedly through the year.
   Test: 2014 vendors used by exactly one cardholder, with three or more charges and more
   than $10,000 of spend.  National chains and government/utility payees are the main false
   positives, so the vendor's MCC and the share of the cardholder's annual spend are shown to
   let the auditor triage; the round-amount count highlights invoices without priced detail. */
WITH vendor_use AS (
    SELECT Vendor,
           COUNT(DISTINCT FullName)                             AS Cardholders,
           MIN(FullName)                                        AS SoleCardholder,
           COUNT(*)                                             AS Charges,
           SUM(Amount)                                          AS VendorSpend,
           MIN(MCC)                                             AS MCC,
           SUM(CASE WHEN Amount = CAST(Amount AS INTEGER)
                     AND CAST(Amount AS INTEGER) % 100 = 0
                    THEN 1 ELSE 0 END)                          AS RoundHundredCharges
    FROM pcards
    WHERE Year = 2014
      AND AgencyName = 'OKLAHOMA STATE UNIVERSITY'
      AND Amount > 0
    GROUP BY Vendor
    HAVING COUNT(DISTINCT FullName) = 1
       AND COUNT(*) >= 3
       AND SUM(Amount) > 10000
),
annual AS (
    SELECT FullName, SUM(Amount) AS AnnualSpend
    FROM pcards
    WHERE Year = 2014
      AND AgencyName = 'OKLAHOMA STATE UNIVERSITY'
    GROUP BY FullName
)
SELECT v.SoleCardholder                                     AS Name,
       v.Vendor,
       v.Charges,
       ROUND(v.VendorSpend, 2)                              AS VendorSpend,
       ROUND(v.VendorSpend / v.Charges, 2)                   AS AverageCharge,
       v.RoundHundredCharges,
       ROUND(100.0 * v.VendorSpend / a.AnnualSpend, 1)       AS PctOfCardholderAnnualSpend,
       v.MCC
FROM vendor_use AS v
JOIN annual     AS a ON a.FullName = v.SoleCardholder
ORDER BY v.VendorSpend DESC;
