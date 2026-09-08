/* qry_T2_Question11 -- Control 11 (student-defined): gifts, gift cards, gift certificates,
   flowers and decorations serve no business purpose and are prohibited.
   Test: 2014 transactions at gift-shop or florist MCCs, or whose description mentions a
   gift card / gift certificate / flowers / decorations.
   MCC "FLORISTS SUPPLIES, NURSERY STOCK & FLOWERS" is excluded from the flagged population
   because at an agricultural university it is dominated by legitimate nursery stock bought
   by Grounds and Horticulture; it is quantified separately in the conclusion. */
SELECT p.FullName        AS Name,
       p.Amount,
       p.Vendor,
       p.Description,
       p.TransactionDate,
       p.MCC,
       CASE WHEN p.MCC LIKE '%GIFT,CARD,NOVELTY%'          THEN 'Gift / novelty MCC'
            WHEN p.MCC = 'FLORISTS'                        THEN 'Florist MCC'
            ELSE 'Description keyword' END                 AS FlagBasis
FROM pcards AS p
WHERE p.Year = 2014
  AND p.AgencyName = 'OKLAHOMA STATE UNIVERSITY'
  AND (   p.MCC LIKE '%GIFT,CARD,NOVELTY%'
       OR p.MCC = 'FLORISTS'
       OR UPPER(p.Description) LIKE '%GIFT CARD%'
       OR UPPER(p.Description) LIKE '%GIFT CERTIF%'
       OR UPPER(p.Description) LIKE '%FLOWER%'
       OR UPPER(p.Description) LIKE '%DECORAT%')
ORDER BY p.Amount DESC;
