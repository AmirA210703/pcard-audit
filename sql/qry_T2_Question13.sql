/* qry_T2_Question13 -- Control 13 (student-defined): the P-card may not be used for cash,
   cash advances or ATM transactions, for insurance, or for late fees / finance charges.
   Test: 2014 transactions whose MCC is a cash-disbursing or insurance category, or whose
   description indicates a late fee, finance charge or interest.  Each hit is labelled with
   the prohibition it relates to so the auditor can route the follow-up. */
SELECT CASE WHEN p.MCC LIKE '%CASH%' OR p.MCC LIKE '%ATM%'
              OR p.MCC LIKE '%FINANCIAL INSTITUTION%'
              OR p.MCC LIKE '%MONEY%' OR p.MCC LIKE '%WIRE TRANSFER%'
              OR p.MCC LIKE '%QUASI CASH%'                     THEN 'Cash / cash advance / ATM'
            WHEN p.MCC LIKE '%INSURANCE%'
              OR UPPER(p.Description) LIKE '%INSURANCE%'        THEN 'Insurance'
            ELSE 'Late fee / finance charge / interest' END     AS Prohibition,
       p.FullName        AS Name,
       p.Amount,
       p.Vendor,
       p.Description,
       p.TransactionDate,
       p.MCC
FROM pcards AS p
WHERE p.Year = 2014
  AND p.AgencyName = 'OKLAHOMA STATE UNIVERSITY'
  AND (   p.MCC LIKE '%CASH%'
       OR p.MCC LIKE '%ATM%'
       OR p.MCC LIKE '%FINANCIAL INSTITUTION%'
       OR p.MCC LIKE '%MONEY%'
       OR p.MCC LIKE '%WIRE TRANSFER%'
       OR p.MCC LIKE '%QUASI CASH%'
       OR p.MCC LIKE '%INSURANCE%'
       OR UPPER(p.Description) LIKE '%INSURANCE%'
       OR UPPER(p.Description) LIKE '%LATE FEE%'
       OR UPPER(p.Description) LIKE '%LATE CHARGE%'
       OR UPPER(p.Description) LIKE '%FINANCE CHARGE%'
       OR UPPER(p.Description) LIKE '%INTEREST CHARGE%')
ORDER BY Prohibition, p.Amount DESC;
