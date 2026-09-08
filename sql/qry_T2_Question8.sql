/* qry_T2_Question8 -- Control 8 (student-defined): Alcohol is a prohibited purchase.
   Risk: cardholders buy alcohol for events/hospitality on the P-card.
   Test: 2014 transactions at merchants whose MCC is an alcohol category, or whose vendor
   name identifies a liquor / package store.  Description text is deliberately NOT searched
   for "alcohol" because laboratory reagents (ethyl alcohol, isopropyl) would flood the
   result with false positives. */
SELECT p.FullName        AS Name,
       p.Amount,
       p.Vendor,
       p.Description,
       p.TransactionDate,
       p.PostedDate,
       p.MCC,
       CASE WHEN p.MCC LIKE '%LIQUOR%'
              OR p.MCC LIKE '%DRINKING PLACES%' THEN 'Alcohol MCC'
            ELSE 'Vendor name' END AS FlagBasis
FROM pcards AS p
WHERE p.Year = 2014
  AND p.AgencyName = 'OKLAHOMA STATE UNIVERSITY'
  AND (   p.MCC LIKE '%LIQUOR%'
       OR p.MCC LIKE '%DRINKING PLACES%'
       OR UPPER(p.Vendor) LIKE '%BOTTLE SHOP%'
       OR UPPER(p.Vendor) LIKE '%LIQUOR%'
       OR UPPER(p.Vendor) LIKE '%BREWERY%'
       OR UPPER(p.Vendor) LIKE '%BREWING%'
       OR UPPER(p.Vendor) LIKE '%WINE CELLA%')
ORDER BY p.Amount DESC;
