/* qry_T2_Question12 -- Control 12 (student-defined): personal / individual memberships and
   dues are a violation of State statutes; recreational and personal-service merchants also
   indicate personal use.
   Test: 2014 transactions at membership-club, spa, golf, recreation and personal-service
   MCCs, ranked by amount.  General "MEMBERSHIP ORGANIZATIONS" (professional associations,
   which are usually institutional and allowable) is reported separately. */
SELECT p.FullName        AS Name,
       p.Amount,
       p.Vendor,
       p.Description,
       p.TransactionDate,
       p.MCC
FROM pcards AS p
WHERE p.Year = 2014
  AND p.AgencyName = 'OKLAHOMA STATE UNIVERSITY'
  AND (   p.MCC LIKE '%MEMBERSHIP CLUBS%'
       OR p.MCC LIKE '%HEALTH AND BEAUTY SPAS%'
       OR p.MCC LIKE '%GOLF%'
       OR p.MCC LIKE '%RECREATION SERVICES%'
       OR p.MCC LIKE '%BEAUTY AND BARBER%'
       OR UPPER(p.Description) LIKE '%MEMBERSHIP%'
       OR UPPER(p.Description) LIKE '%DUES%')
ORDER BY p.Amount DESC;
