/* qry_T2_Question10 -- Control 10 (student-defined): Mail and postage are prohibited; all
   U.S. mail (incl. parcel post, certified, registered) must go through University Mailing.
   Test: 2014 transactions at postal MCCs or postal/postage-meter vendors.  Commercial
   couriers (FedEx/UPS freight) are reported separately because inbound freight on a
   purchase is normally allowable, whereas outbound mail is not. */
SELECT p.FullName        AS Name,
       p.Amount,
       p.Vendor,
       p.Description,
       p.TransactionDate,
       p.MCC,
       CASE WHEN p.MCC LIKE '%POSTAGE%'
              OR UPPER(p.Vendor) LIKE '%USPS%'
              OR UPPER(p.Vendor) LIKE '%POSTAL%'
              OR UPPER(p.Vendor) LIKE '%POST OFFICE%'
              OR UPPER(p.Vendor) LIKE '%PITNEY%'  THEN 'Postage / post office'
            ELSE 'Commercial courier' END          AS FlagBasis
FROM pcards AS p
WHERE p.Year = 2014
  AND p.AgencyName = 'OKLAHOMA STATE UNIVERSITY'
  AND (   p.MCC LIKE '%POSTAGE%'
       OR UPPER(p.Vendor) LIKE '%USPS%'
       OR UPPER(p.Vendor) LIKE '%POSTAL%'
       OR UPPER(p.Vendor) LIKE '%POST OFFICE%'
       OR UPPER(p.Vendor) LIKE '%PITNEY%')
ORDER BY p.Amount DESC;
