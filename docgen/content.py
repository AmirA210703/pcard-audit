# -*- coding: utf-8 -*-
"""Answers for Parts II and III of the P-card assignment."""

# ---------------------------------------------------------------- Part II ----
# Titles for the seven student-defined controls (Controls 8-14).
T2_TITLES = {
    8:  "Alcohol may not be purchased with a P-Card.",
    9:  "Gasoline must be bought from Transportation Services, not on a P-Card.",
    10: "Mail and postage must be sent through University Mailing.",
    11: "Gifts, gift cards, flowers and decorations are prohibited.",
    12: "Personal and individual memberships, clubs and personal services are prohibited.",
    13: "Cash, cash advances, ATM transactions, insurance and late fees are prohibited.",
    14: "Regular monthly payments over $5,000 per fiscal year require a requisition and PO.",
}

# "Test to perform and desired output" text for Controls 8-14.
T2_TESTS = {
8: "Control requirement: the prohibited-purchase list states plainly that a P-Card may not "
   "be used for alcohol. Risk: alcohol is bought for departmental events or hospitality and "
   "hidden behind a generic description such as GENERAL PURCHASE. Test: return every 2014 "
   "transaction whose MCC is an alcohol category (package stores, drinking places) or whose "
   "vendor name identifies a liquor store, bottle shop, brewery or wine merchant. The "
   "description field is deliberately not searched for the word “alcohol” because "
   "laboratory reagents (ethyl alcohol, isopropyl alcohol) would swamp the result with false "
   "positives. Output: Name, Amount, Vendor, Description, TransactionDate, PostedDate, MCC and "
   "the basis on which the row was flagged, sorted by Amount with the largest first.",
9: "Control requirement: gasoline is a prohibited purchase — it must be bought from "
   "Transportation Services or with the gasoline credit card issued with each University "
   "vehicle. Risk: cardholders fuel University (or personal) vehicles on the P-Card, which "
   "bypasses the fleet-fuel controls. Test: identify all 2014 transactions at fuel-selling "
   "merchant categories (service stations, automated fuel dispensers and fuel dealers) and "
   "summarise them by cardholder so repeat use is visible rather than one-off use. Output: "
   "Name, number of fuel transactions, total fuel spend, largest single charge and the number "
   "of distinct fuel vendors, sorted by total fuel spend with the largest first.",
10: "Control requirement: all U.S. mail, including parcel post, certified and registered mail, "
    "must be sent through University Mailing; mail and postage are prohibited on the P-Card. "
    "Risk: departments buy stamps or refill their own postage meters directly, defeating the "
    "central mailing contract and its rates. Test: return every 2014 transaction at a postage "
    "MCC or at a postal / postage-meter vendor (USPS, postal outlets, post offices, Pitney "
    "Bowes). Output: Name, Amount, Vendor, Description, TransactionDate, MCC and the flag basis, "
    "sorted by Amount with the largest first.",
11: "Control requirement: gifts, gift cards and gift certificates violate State statutes, and "
    "items that serve no business purpose — flowers, candy, greeting cards — and "
    "decorations are separately prohibited. Risk: recognition and hospitality spending is run "
    "through the card as a GENERAL PURCHASE. Test: return every 2014 transaction at a gift / "
    "novelty MCC or the FLORISTS MCC, or whose description mentions a gift card, gift "
    "certificate, flowers or decorations. The MCC “FLORISTS SUPPLIES, NURSERY STOCK & "
    "FLOWERS” is excluded from the flagged population and quantified separately, because at "
    "an agricultural university it is dominated by legitimate nursery stock bought by Grounds "
    "and Horticulture. Output: Name, Amount, Vendor, Description, TransactionDate, MCC and the "
    "flag basis, sorted by Amount with the largest first.",
12: "Control requirement: payment of personal or individual memberships and dues is a violation "
    "of State statutes, and the card may never be used for personal purchases. Risk: gym and "
    "country-club memberships, spa treatments, golf and other recreation are charged to the "
    "card as business expenses. Test: return every 2014 transaction at a membership-club, "
    "health-and-beauty-spa, golf-course, recreation-services or personal-grooming MCC, or whose "
    "description mentions a membership or dues. The generic “MEMBERSHIP ORGANIZATIONS” "
    "MCC is left out of the test because it is dominated by institutional professional-society "
    "dues, which are allowable. Output: Name, Amount, Vendor, Description, TransactionDate and "
    "MCC, sorted by Amount with the largest first.",
13: "Control requirement: cash, cash advances and ATM transactions are prohibited; insurance "
    "must be processed on a requisition through Risk and Property Management; late fees are "
    "prohibited. Risk: the card is used to obtain cash or quasi-cash, to pay insurance premiums "
    "outside Risk Management, or the University absorbs late fees and finance charges caused by "
    "slow processing. Test: return every 2014 transaction whose MCC is a cash-disbursing, "
    "money-transfer, quasi-cash or insurance category, or whose description indicates insurance, "
    "a late fee, a late charge, a finance charge or an interest charge, labelling each hit with "
    "the prohibition it relates to. Output: Prohibition, Name, Amount, Vendor, Description, "
    "TransactionDate and MCC, sorted by prohibition and then by Amount with the largest first.",
14: "Control requirement: maintenance, lease/rental and service agreements for office or "
    "scientific equipment must be processed on a requisition with a purchase order issued when "
    "the total for the fiscal year exceeds $5,000; they may not simply be paid month after month "
    "on a P-Card. Risk: a standing contract is created and paid by card, so it never reaches "
    "Purchasing and is never competitively bid. Test: find every cardholder / vendor / amount "
    "combination in 2014 where the identical amount is charged in at least six different months "
    "— the signature of a fixed monthly agreement — and where the cardholder's total "
    "spend with that vendor for the year exceeds $5,000. Output: Name, Vendor, the recurring "
    "amount, the number of months at that amount, the number of charges, the recurring spend, "
    "the annual total with that vendor, the annual transaction count and the MCC, sorted by the "
    "annual total with the vendor, largest first.",
}

T2_RESULTS = {
1: [
 "Result: 127 of the 2,021 OSU cardholders spent more than $50,000 during 2014, and together "
 "they account for $15,527,124 of the $33,504,148 charged on P-Cards that year (46%). Thirty-nine "
 "cardholders exceeded $100,000. The largest is Employee 51914657 at $1,595,302.32 across 3,510 "
 "transactions, followed by Employee B1FA2F0D ($1,182,094.86) and Employee 688E3D92 ($627,608.56).",
 "Conclusion: the $50,000 ceiling in the procedure is a per-cycle credit limit, not an annual cap, "
 "so spending more than $50,000 across twelve cycles is not by itself a violation — several of "
 "these cardholders are clearly central facilities and maintenance buyers, and the transaction "
 "counts support that. The exception worth pursuing is the cardholder whose annual volume is far "
 "larger than any approved cycle limit could support: at $1.6m, Employee 51914657 averages "
 "$132,942 per month, which no compliant limit permits.",
 "Follow-up: obtain the approved single-transaction and cycle limits from each of the 127 P-Card "
 "application forms and compare them with actual usage; this population is also the natural input "
 "to the annual Cardholder Limit Recertification required by the procedure.",
],
2: [
 "Result: 457 cardholder-months exceeded $10,000 in 2014, involving 161 different cardholders and "
 "$11,140,681 of spend. Forty of those cardholder-months exceeded $50,000, which does breach the "
 "stated ceiling that a cycle credit limit “shall not exceed $50,000”. The exceptions are "
 "spread evenly across the year (April 45, February / June / October 42 each, November 27), so "
 "there is no year-end or fiscal-year-end spending spike.",
 "Conclusion: exceeding $10,000 in a month is permitted where departmental administration has "
 "documented a justification, so the 457 rows are a population to be reconciled against "
 "authorisations rather than 457 violations. The 40 cardholder-months above $50,000 are different "
 "— no justification can authorise a cycle limit above that ceiling, so each one is either a "
 "genuine control breach or evidence that the point-of-sale cycle limit was not set as the "
 "procedure requires.",
 "Follow-up: request the departmental justifications for every cardholder with a monthly limit "
 "above $10,000 (above $2,500 for student employees) and confirm with Bank of America what cycle "
 "limit was actually loaded on the 40 cards that passed $50,000 in a single month.",
],
3: [
 "Result: only 33 transactions exceeded $5,000 in 2014, totalling $357,870.91, and they belong to "
 "just six cardholders. The largest is $29,731.61 (OEC Otis Elevator Co). By contrast there are 20 "
 "transactions at exactly $5,000.00 and 113 between $4,900 and $5,000.",
 "Conclusion: the single-transaction limit is enforced at the point of sale, which is why so few "
 "transactions clear it — each of the 33 implies that a limit was temporarily raised, so each "
 "one should have approval documentation behind it. Two cardholders dominate: Employee 0E3DD9FC "
 "(conference lodging and group air travel — room blocks and charter-type charges, plausibly "
 "legitimate but requiring an exception) and Employee 302B04AF, whose $19,233.28 and $5,688.46 "
 "charges at COCKRELL EYECARE CENTER, an optician, have no obvious University business purpose.",
 "Follow-up: obtain the approved limit-increase request for each of the 33 transactions, and treat "
 "the two Cockrell Eyecare charges as a priority investigation — the same cardholder also "
 "appears in Control 12 with $8,545 of spa charges.",
],
4: [
 "Result: 254 transactions fall into 66 cardholder / vendor / day clusters where the same "
 "cardholder swiped the same card more than once at the same vendor on the same day and the day's "
 "total exceeded $5,000. Thirty cardholders are involved and $470,368.63 is at stake. The largest "
 "clusters are Employee CEFFB0FE with 11 swipes at DOUBLETREE HOTEL BETHESDA on 22 May 2014 "
 "($21,020.26), Employee 7A1AD2BE with 2 swipes at HILTON BOSTON DOWNTOWN ($15,326.88) and Employee "
 "6A680974 with 7 swipes at VETERANS AFFRS DMC on 17 October ($12,976.96) and 11 swipes on 24 "
 "February ($7,490.94).",
 "Conclusion: multiple same-day charges at one vendor are not automatically a split purchase. "
 "Hotel clusters are usually one folio per traveller in a group booking, and the supply-house "
 "clusters (Rexel, Oklahoma Contractors Supply, Economy Supply) are consistent with separate work "
 "orders drawn on the same day. The clusters that do look like evasion are the ones where the "
 "individual swipes are each just below $5,000, because there the amounts, not the work, appear to "
 "be driving the split.",
 "Follow-up: request the itemised receipts for the 66 clusters and test whether a single known "
 "quantity of goods or services was divided; the Veterans Affairs and Doubletree clusters should be "
 "first because of both their size and their frequency.",
],
5: [
 "Result: 24 vendor-days meet the test — 48 transactions, 38 cardholders and $146,966.52 "
 "— where a vendor took more than $5,000 in one day from exactly two cardholders, each of whom "
 "made exactly one charge. Three are near-certain splits because both cardholders paid an identical "
 "amount: PAYPAL FUTUREBUS on 15 May, 2 × $4,014.90 = $8,029.80; B & H PHOTO-VIDEO.COM on 13 "
 "February, 2 × $2,544.07 = $5,088.14, both described as “EOS 6D DIGITAL CAM”; and "
 "SHAKE RATTLE AND ROLL on 28 May, $4,979.00 + $4,959.00 = $9,938.00.",
 "Conclusion: the B & H case is the clearest control breach in this test — two identical "
 "camera kits bought the same day by two cardholders from one vendor is a single known quantity of "
 "goods divided between two cards, exactly the example the procedure gives. The PayPal and "
 "entertainment pairs share the same signature. The remaining pairs, where one leg is small (for "
 "example $4,999.35 + $503.04 at The Lee Company), are more likely to be two departments coinciding "
 "at a common supplier.",
 "Follow-up: interview both cardholders and both approvers for the three identical-amount pairs, "
 "and confirm whether the two camera bodies were part of one requisition that should have been bid.",
],
6: [
 "Result: 59 cardholder-days meet the test — 118 transactions, 48 cardholders and $368,166.79 "
 "— where one cardholder spent more than $5,000 on a day across exactly two vendors with one "
 "charge each.",
 "Conclusion: this is the weakest of the three split tests, because buying from two different "
 "vendors on the same day is ordinary purchasing behaviour and the test cannot see whether the two "
 "purchases were for the same thing. Several flagged pairs are plainly unrelated goods: Employee "
 "D8983D5C's $5,000.00 to the Academy of Nutrition and Dietetics plus $3,775.00 to a plumbing "
 "contractor on 16 January, or Employee 1BCC5E9A's $5,000.00 to I2E Inc plus a $2.80 PIKEPASS toll "
 "on 14 February — in the latter case the toll only pulls a legitimate $5,000 charge over the "
 "threshold. The rows worth pursuing are those where both legs sit just under $5,000 and the two "
 "vendors sell the same category of goods.",
 "Follow-up: narrow the population to pairs whose two vendors share an MCC and whose legs are each "
 "between $2,500 and $4,999, then request the receipts for that subset.",
],
7: [
 "Result: 99 restaurant and fast-food charges, worth $19,448.41, were made by 31 employees on days "
 "when those same employees also had a lodging charge (an MCC containing hotel, motel, resort or "
 "inn). The average charge is $196 and the largest is $1,033.46. Employees 465E5080 and 77949E3B "
 "each have seven such charges.",
 "Conclusion: food while in travel status is prohibited because it is reimbursed through per diem "
 "on a travel voucher, so a restaurant charge on a lodging day is a genuine control deviation "
 "signal. The test is reasonably precise here — the word “inn” correctly matches "
 "lodging brands (Holiday Inns, Hampton Inns, Fairfield Inn) and no pet-food merchants were caught "
 "by the word “food”. The main legitimate explanation is group hospitality: a $1,033 "
 "restaurant charge is not one traveller's dinner but a hosted meal for recruits, a search "
 "committee or conference attendees, which is treated differently from per diem.",
 "Follow-up: pull the travel vouchers for these 31 employees for the flagged dates. If per diem was "
 "claimed for a day on which a meal was also charged to the card, the University has paid twice and "
 "the amount should be recovered.",
],
8: [
 "Result: 15 transactions worth $20,856.11 across seven cardholders. Employee 3B7AEC76 accounts for "
 "$17,418.48 of that on seven charges at BROWNS BOTTLE SHOP, five of them between $2,676.44 and "
 "$4,151.05, spread through March, May, October, November and December. The remaining cardholders "
 "have one or two charges each, mostly at package stores (BEELINE LIQUOR $713.54, PARKHILL'S "
 "WAREHOUSE LIQUOR $466.65, TULSA HILLS WINE CELLAR $395.26) or at brewpubs, where the charge may "
 "be a meal rather than alcohol.",
 "Conclusion: this is the most clear-cut prohibited-purchase finding in the audit. Alcohol is "
 "banned outright, and a package-store MCC leaves little room for an innocent explanation. The "
 "pattern on Employee 3B7AEC76's card — recurring four-figure purchases at a single liquor "
 "store, every one of them below the $5,000 single-transaction limit — indicates a standing "
 "arrangement rather than a mistake.",
 "Follow-up: escalate Employee 3B7AEC76 immediately: obtain all seven receipts, the Works "
 "descriptions and approver sign-offs, and identify the events the alcohol was bought for and who "
 "approved them. Treat the brewpub charges as ordinary restaurant charges unless the receipts show "
 "otherwise.",
],
9: [
 "Result: 730 transactions worth $296,421.24 were charged at fuel-selling merchants by 189 "
 "cardholders. Sixteen cardholders spent more than $5,000 on fuel; the largest are Employee "
 "B1FA2F0D ($46,602.60 on 43 charges), Employee 7239C3FF ($20,515.27) and Employee 2B4B388B "
 "($16,942.83). The largest single charge is $4,075.00.",
 "Conclusion: charges of $1,000–$4,000 at a service station are not car fill-ups; they are "
 "bulk fuel deliveries to a tank. At an agricultural university with farms, research stations and "
 "off-road equipment, buying bulk fuel is a real business need, and the MCC alone cannot separate "
 "bulk delivery from filling a vehicle. The control deviation is nevertheless real in form: the "
 "procedure routes all gasoline through Transportation Services or the vehicle card, with no "
 "exception for bulk purchases, so either the purchases or the procedure need to change.",
 "Follow-up: reconcile the 16 cardholders above $5,000 against Transportation Services fuel records "
 "and the vehicle-card programme; separately review the low-value, single-fill charges, which are "
 "the ones most likely to be a personal vehicle.",
],
10: [
 "Result: 89 transactions worth $14,726.07 across 49 cardholders. These include 14 direct purchases "
 "of postage stamps from USPS (the largest $1,218.00, $1,035.00 and $905.00), recurring postage-"
 "meter refills billed by Pitney Bowes — Employee 820C69E3 alone has eight charges of $210 to "
 "$527.50 — and retail shipping outlets such as POSTAL PACK & SHIP PLUS and GOIN' POSTAL.",
 "Conclusion: this prohibition is unusually clear-cut, so most of these rows are genuine "
 "deviations: the University runs a central mailing operation precisely so that postage is bought "
 "at contract rates and charged back, and a departmental postage meter run on a P-Card bypasses "
 "that entirely. One false positive is present — MARRIOTT USPS CONFERENCE is a hotel charge "
 "for a USPS conference, not postage.",
 "Follow-up: confirm with University Mailing whether the departments concerned have an approved "
 "exception; if not, the recurring Pitney Bowes meters should be closed and the postage moved to "
 "the central operation.",
],
11: [
 "Result: 356 transactions worth $83,882.20 across 149 cardholders — 216 at gift / novelty "
 "MCCs, 128 at the FLORISTS MCC and 12 caught by description keywords. The largest are $4,045.00 "
 "(KEY PLUS PRODUCT), $3,969.16 (SHOPNASACOM), $3,000.00 (DEKRA-LITE INDUSTRIES, a commercial "
 "holiday-decoration supplier) and $2,340.00 (NASA EXCHANGE – JSC). The nursery-stock MCC that "
 "was deliberately excluded holds a further 217 transactions worth $80,415.62.",
 "Conclusion: the population divides into three groups. Decorations bought from a decoration "
 "supplier, and cut flowers from a florist, are squarely on the prohibited list and are exceptions "
 "on their face. Gift-shop and museum-store purchases at places such as the NASA Exchange are more "
 "likely to be resale stock or programme materials for outreach activities than gifts, and need the "
 "Works description to resolve. Excluding nursery stock was necessary — it is bulk plant "
 "material for Grounds and Horticulture, and including it would have tripled the population with "
 "false positives.",
 "Follow-up: sample 25 of the flagged transactions across all three groups, read the business "
 "purpose entered in Works and inspect the receipts; if any gift cards or gift certificates are "
 "found, escalate immediately because those breach State statutes and not only University policy.",
],
12: [
 "Result: 147 transactions worth $79,238.66 across 79 cardholders: 44 charges at membership clubs, "
 "19 at golf courses, seven at health-and-beauty spas ($8,545.06) and the remainder at recreation "
 "services. The single largest items are $5,000.00 (AAC CENTER), $4,513.77 (OSU COWBOY GOLF), "
 "$4,037.50 (SPACE CENTER HOUSTON), $3,840.00 (KICKINGBIRD GOLF CLUB) and two charges of $2,400.00 "
 "at B&V BODY WORKS GYM LLC. All seven spa charges belong to Employee 302B04AF at THE ROYAL "
 "TREATMENT ($1,980.00, $1,925.00, $1,450.00, $1,365.00, $1,300.00 and two smaller).",
 "Conclusion: some of this population has a plausible business purpose — a golf course or a "
 "science centre can be the venue for a departmental event or a donor function, and coaching-"
 "association dues are institutional. Two findings do not. The recurring gym charges look like a "
 "membership paid by the University, which State statutes prohibit. The seven spa charges "
 "concentrated on one card are the strongest personal-use indicator in the whole data set, and that "
 "is the same cardholder who charged $24,921 at an optician in Control 3.",
 "Follow-up: open a full-scope investigation of Employee 302B04AF covering all 122 of that "
 "cardholder's 2014 transactions; separately confirm whether the two $2,400 gym charges are "
 "individual memberships or a facility-use contract.",
],
13: [
 "Result: 18 exceptions worth $9,822.92, and all 18 relate to insurance. Across all 116,031 OSU "
 "transactions in 2014 there is not a single cash-advance, ATM, quasi-cash or money-transfer MCC, "
 "and no description contains a late fee, late charge, finance charge or interest charge. The "
 "insurance hits are led by VFIS-CETS ($1,860.00, $965.12, $960.00 and $720.00), US LIABILITY "
 "INSURANCE ($1,400.00) and FRANCIS L DEAN & ASSOCIATES ($809.00), plus several small travel-"
 "insurance policies.",
 "Conclusion: two different conclusions apply. For cash, ATM and late fees the control is operating "
 "effectively — the MCC blocking that the Purchasing Department maintains is doing its job, and "
 "the absence of late fees also suggests transactions are being processed inside the five-day "
 "window. For insurance the control is not effective: premiums must go on a requisition through "
 "Risk and Property Management, and 16 of these are real premiums. Two rows are false positives "
 "— SONY SERVICE charges where “INSURANCE” is a shipping-insurance line inside a "
 "repair invoice.",
 "Follow-up: report the insurance premiums to Risk and Property Management so the coverage can be "
 "brought under the University's programme, and confirm that the cash / ATM MCC blocks remain in "
 "place on every card as new cards are issued.",
],
14: [
 "Result: 46 recurring amount patterns across 31 cardholder-vendor pairs and 27 cardholders, "
 "carrying $156,848.42 of recurring charges. The clearest standing agreements are PAY STORAGE "
 "STATION at $726.00 in each of 11 months ($7,986.00 — a storage lease), GOOGLE ADWORDS at "
 "$500.00 twenty-one times ($10,500.00), WATER QUALITY CONTROL at $750.00 in 11 months ($9,000.00), "
 "COMPLETE PEST CONTROL at $950.00 eight times ($7,600.00), BITGRAVITY at $390.00 thirteen times "
 "and fixed monthly amounts at XEROX, DIRECTV, AT&T DATA and Business World Inc.",
 "Conclusion: an identical amount charged in six or more separate months is not repeat purchasing "
 "of goods — it is a subscription, lease or service agreement being paid by card. Where the "
 "annual total for that vendor exceeds $5,000 the procedure requires a requisition and a purchase "
 "order, so these are control deviations even though every individual charge is small and well "
 "inside the single-transaction limit. That is exactly why a per-transaction limit alone cannot "
 "enforce this rule.",
 "Follow-up: hand the 31 cardholder-vendor pairs to Purchasing to be converted into requisitions "
 "and purchase orders for the next fiscal year, and add an annual recurring-payment report to the "
 "P-Card Administrator's monitoring routine.",
],
}

# --------------------------------------------------------------- Part III ----
T3_TITLES = {
    5: "Structuring just below the $5,000 single-transaction limit",
    6: "Weekend and public-holiday purchasing",
    7: "Sole-cardholder vendor concentration (related-party risk)",
    8: "Credits and returns with no matching original charge",
}

T3_TESTS = {
5: "Fraud risk / hypothesis: a cardholder who repeatedly charges an amount just under the $5,000 "
   "single-transaction limit may be pricing or dividing purchases so that they never reach the "
   "requisition and competitive-bidding route. Test: take every positive 2014 OSU transaction "
   "between $4,500 and $4,999.99 and aggregate it by cardholder, then compare that near-limit "
   "activity with the cardholder's total annual spend. To reduce false positives only cardholders "
   "with at least two near-limit charges are returned — a single charge of $4,900 is ordinary "
   "pricing, a pattern of them is not — and the number of distinct vendors is shown so that "
   "repeated use of one supplier stands out. Output: Name, near-limit charges, near-limit value, "
   "largest near-limit charge, distinct vendors, annual spend, annual transactions and the "
   "percentage of annual spend sitting in the near-limit band, sorted by the number of near-limit "
   "charges, largest first.",
6: "Fraud risk / hypothesis: purchases made when the University is closed are less likely to have "
   "gone through a departmental pre-approval procedure, and weekend and holiday activity on a "
   "business card is a recognised indicator of personal use. Test: identify positive 2014 "
   "transactions dated on a Saturday, a Sunday or one of the 2014 federal holidays. To stop the "
   "population filling up with legitimate travel, merchant categories where weekend activity is "
   "expected — lodging, airlines, car rental, restaurants, fuel, tolls, parking and transport "
   "— are excluded, and only cardholders with at least five such charges are reported. "
   "Output: Name, closed-day charges, closed-day value, a split of charges by holiday / Saturday / "
   "Sunday, distinct vendors and the largest charge, sorted by closed-day value, largest first.",
7: "Fraud risk / hypothesis: the procedure forbids purchases from friends and family, from any "
   "company owned by a University employee, and from any company in which the cardholder has a "
   "financial interest. A shell or related-party vendor typically shows up as a vendor that only "
   "one cardholder in the entire University ever uses, that receives a material amount of money, "
   "and that is billed repeatedly through the year. Test: find 2014 vendors used by exactly one "
   "cardholder with three or more charges and more than $10,000 of spend. Because national chains "
   "and government or utility payees are the main false positives, the output also shows the MCC, "
   "the share of that cardholder's annual spend going to the vendor, and how many charges are round "
   "hundreds — invoices without priced detail. Output: Name, Vendor, charges, vendor spend, "
   "average charge, round-hundred charges, percentage of the cardholder's annual spend and MCC, "
   "sorted by vendor spend, largest first.",
8: "Fraud risk / hypothesis: the procedure requires the cardholder to check the Bank Statement so "
   "that returned goods are credited properly and to retain documentation of every credit. A credit "
   "posted to the University card with no corresponding charge on that card at that vendor can mean "
   "the goods were paid for another way while the refund landed on the University card, that a "
   "merchant adjustment was never investigated, or simply that the original charge fell in a prior "
   "year — in every case it is money moving without support. Test: take every 2014 credit "
   "(negative amount) and test whether the same cardholder has any charge at the same vendor in "
   "2014 that is at least as large as the credit; report the credits with no such charge, together "
   "with each cardholder's overall credit activity for context. Output: Name, credit amount, "
   "Vendor, Description, TransactionDate, MCC, and the cardholder's credits, credit value and "
   "transaction count for the year, sorted by credit amount, largest first.",
}

T3_RESULTS = {
1: [
 "Result: the population is 112,140 transactions of $1.00 or more. Observed first-digit "
 "frequencies are 29.528% / 17.771% / 12.867% / 9.814% / 8.221% / 6.124% / 5.513% / 5.372% / "
 "4.790% against Benford expectations of 30.103% / 17.609% / 12.494% / 9.691% / 7.918% / 6.695% / "
 "5.799% / 5.115% / 4.576%. Every digit is within 0.6 percentage points of expectation; the largest "
 "deviations are digit 1 at −0.575 and digit 6 at −0.570.",
 "Conclusion: this indicates a relatively LOW fraud risk at the population level. The mean absolute "
 "deviation is 0.318 percentage points (0.0032 in proportion terms), which falls inside Nigrini's "
 "“close conformity” band for a first-digit test (below 0.006). A chi-square statistic of "
 "137.3 on 8 degrees of freedom does exceed the 1% critical value of 20.09, but chi-square is "
 "oversensitive at samples above 100,000 and would reject almost any real data set of this size, so "
 "MAD is the better guide here.",
 "Follow-up: two caveats matter. First, Benford's Law describes the population, and fraud confined "
 "to a handful of cardholders can be invisible in 112,140 transactions — so the test should be "
 "re-run per cardholder for the highest spenders. Second, the small shortfall on digit 1 with a "
 "mild excess on digits 3, 5, 8 and 9 is the direction one would expect from the near-limit "
 "clustering found in Question 5, and it is worth re-testing on the sub-population above $1,000.",
],
2: [
 "Result: 4,924 charges form 1,732 possible-duplicate occasions involving 577 cardholders, with a "
 "gross value of $1,087,222.41. In 579 of those occasions three or more charges match. If every "
 "charge beyond the first in each occasion were an overpayment, the exposure would be $670,114.68. "
 "The largest matched pairs are $4,305.00 × 2 at INTERMOUNTAIN LOCK AND SECURITY (29 August), "
 "$3,880.00 × 2 at THE UPS STORE #6556 (11 December) and $3,812.62 × 2 at HOTARD COACHES "
 "(11 February).",
 "Conclusion: this is a lead list, not a loss estimate, and the $670,114.68 is an upper bound. The "
 "test cannot see quantity, so legitimately repeated same-price purchases match: AT&T DATA at $25 "
 "or $30 is a per-device data plan billed once per line, three identical $850.00 ACFE charges on 2 "
 "January are three memberships or registrations, and conference fees for several attendees are "
 "charged separately at the same price on the same day. What raises risk is size and lack of a "
 "quantity explanation — two identical four-figure charges at a locksmith or a coach company "
 "are far less likely to be a coincidence than two $25 phone plans.",
 "Follow-up: test the 30 highest-value occasions against the underlying receipts and the credits "
 "posted afterwards; the recovery mechanism already exists in the procedure, which requires the "
 "cardholder to reconcile receipts to the Bank Statement each cycle.",
],
3: [
 "Result: 577 employees appear in the possible-duplicate population. Ranked by occasions rather "
 "than rows, the highest-risk employees are Employee 5BA61357 (78 occasions, 212 charges, "
 "$41,525.65 of potential overpayment), Employee 50D6FB87 (65 occasions, $18,111.48), Employee "
 "DC886243 (44 occasions, $5,998.52), Employee 51914657 (36 occasions, $19,682.52) and Employees "
 "B1FA2F0D and 4398674F (33 occasions each). Employee 8A27F2BB has only 26 occasions but 181 "
 "charges and the second-highest potential overpayment at $24,477.09. Twenty-five employees have "
 "ten or more occasions, and the top ten account for 22.8% of all 1,732 occasions.",
 "Conclusion: counting occasions rather than transaction rows is what makes this ranking useful "
 "— it stops one employee with a triple charge outranking another with two genuine "
 "double-payment events. The concentration is meaningful: with 577 employees in the population, an "
 "employee with 78 occasions is not experiencing random processing noise, and the pattern points "
 "either to a weak reconciliation habit or to deliberate resubmission.",
 "Follow-up: begin with Employees 5BA61357, 50D6FB87 and 8A27F2BB, and read their duplicates "
 "together with the approver and accountant sign-offs — the procedure requires three different "
 "people per transaction, so a repeated duplicate that cleared every cycle points at the review "
 "step as much as at the cardholder.",
],
4: [
 "Result: 160 positive transactions have a four-digit whole-dollar amount ending in 000, worth "
 "$343,003.98, spread over 115 employees and 136 vendors. The distribution is $1,000 (77 charges), "
 "$2,000 (32), $3,000 (24), $5,000 (20), $4,000 (6) and $6,000 (1). Employee A1DDFECC has 13 of "
 "them, eight of those at “Amazon Payments”; the next-highest employees have four. Only "
 "11 of the 160 carry any cents at all.",
 "Conclusion: round amounts are not evidence of fraud by themselves — association dues, "
 "sponsorships, registration fees and negotiated services are genuinely quoted in round thousands, "
 "and much of this list (ABET, AASHTO, AEJMC, professional societies) is exactly that. Two patterns "
 "do stand out. The 20 charges at exactly $5,000.00 sit precisely on the single-transaction limit, "
 "which means the amount was almost certainly set by the limit rather than by the goods. And "
 "Employee A1DDFECC's eight round charges through Amazon Payments are concerning for a different "
 "reason: Amazon Payments is a payment processor, so the record does not reveal who was actually "
 "paid or what was bought.",
 "Follow-up: obtain the invoices behind the 20 charges at exactly $5,000.00 and the full Amazon "
 "Payments trail for Employee A1DDFECC, including the Works descriptions and the underlying "
 "merchant of record.",
],
5: [
 "Result: 46 cardholders have two or more charges in the $4,500–$4,999.99 band, accounting for "
 "166 charges and $795,967.23. The decisive number is the shape of the distribution around the "
 "limit: 269 transactions fall between $4,500 and $4,999.99, but only 22 fall between $5,000 and "
 "$5,499.99 — a ratio of roughly 12 to 1. Ranked by how much of their annual spend sits in the "
 "band, the highest-risk cardholders are Employee 244811D8 (6 near-limit charges, 45.4% of annual "
 "spend, only 3 vendors), Employee 5BA21F75 (45.4%), Employee 66791A0B (38.2%), Employee CA09FAD0 "
 "(36.7%, all at one vendor) and Employee 073E5CEE (33.3%, 2 vendors). By volume, Employees "
 "B1FA2F0D (18 charges) and 51914657 (17) lead.",
 "Conclusion: part of the cliff at $5,000 is the control working as designed — the card simply "
 "declines above the limit, so charges cannot appear on the other side of it. But a declined card "
 "produces no transaction at all, whereas here we see a heavy build-up immediately below the line, "
 "which means purchases are being shaped to fit it. Read together with Control 4's same-day split "
 "clusters, the reasonable inference is that some cardholders know the limit and are pricing or "
 "dividing purchases around it. Legitimate explanations exist — vendors quoting to a stated "
 "budget, or genuine purchases that happen to fall just under — which is why concentration "
 "matters more than a single charge.",
 "Follow-up: for the five cardholders with more than a third of their annual spend in the band, "
 "obtain the quotations as well as the invoices; a quotation written to a $5,000 ceiling is the "
 "evidence that distinguishes structuring from coincidence.",
],
6: [
 "Result: after excluding travel, lodging, restaurant, fuel and transport merchant categories, 452 "
 "cardholders have five or more charges dated on a Saturday, Sunday or 2014 federal holiday: 5,717 "
 "charges worth $1,269,262.18. The largest are Employee 51914657 (168 charges, $77,806.16, "
 "including 132 Saturdays and 12 holidays), Employee E38DA379 (105 charges, $30,335.02) and "
 "Employee 14B7B862 (117 charges, of which 51 fall on Sundays).",
 "Conclusion: this is a risk-ranking rather than an exception list. Facilities, grounds, utilities "
 "and animal-care staff genuinely work weekends and holidays, and the top two cardholders are the "
 "same central maintenance buyers who dominate the high-volume tests — for them weekend "
 "purchasing is expected. The signal to act on is narrower: charges on the major closed holidays, "
 "and cardholders whose weekend activity sits at consumer-facing merchants rather than at supply "
 "houses. A cardholder with 51 Sunday charges at retail merchants is a different proposition from a "
 "plumber buying parts on a Saturday call-out.",
 "Follow-up: cross-reference the flagged holiday charges against departmental timesheets and "
 "on-call rosters, and re-run the test restricted to consumer-retail MCCs to isolate the personal-"
 "use candidates.",
],
7: [
 "Result: 32 vendor relationships meet the test, carrying $632,601.90. The highest-risk are: "
 "Employee 6A680974 / VETERANS AFFRS DMC — 109 charges, $116,022.89, which is 100.0% of that "
 "cardholder's entire annual spend; Employee 302B04AF / COCKRELL EYECARE CENTER — 6 charges, "
 "$39,834.61, an average of $6,639 which is above the single-transaction limit, at an optician, "
 "20.6% of annual spend; Employee F41CAF02 / PHONAK HEARING SYSTEMS — 50 charges, $39,199.20, "
 "45.0% of annual spend; Employee 68FFDF40 / CUSTOM MISERS LIVESTOCK — 58.6% of annual spend; "
 "and Employee C6584F79 / “PAYPAL ADVANCEDMAC” — 5 charges, $14,825.00 routed "
 "through PayPal so the true payee is concealed.",
 "Conclusion: exclusivity is the point of this test — in a university of 2,021 cardholders and "
 "17,513 vendors, a supplier that exactly one person ever uses, for five or six figures, is either "
 "a genuinely specialised supplier or a relationship nobody else can see. Several here are clearly "
 "the former: Phonak Hearing Systems and Truscreen fit a speech and hearing clinic, and a "
 "veterinary diagnostic laboratory fits an animal-science programme. Two do not fit "
 "straightforwardly — an optician taking $39,834 in six charges from one cardholder, and a "
 "PayPal-routed payee — and both share a signature with findings elsewhere in this audit: "
 "Employee 302B04AF also holds the spa charges in Control 12 and the >$5,000 transactions in "
 "Control 3.",
 "Follow-up: run all 32 vendor names against the State employee register and the Secretary of "
 "State's business-ownership records, and pull the conflict-of-interest disclosures for these "
 "cardholders. For the PayPal payees, request the underlying PayPal transaction records to identify "
 "the actual recipient.",
],
8: [
 "Result: 358 credits worth $91,855.19, spread over 244 cardholders, have no charge of equal or "
 "greater value on the same card at the same vendor during 2014 — out of 3,791 credits worth "
 "$629,445.26 in total. The largest are $4,232.00 at INTL COLD STORAGE (Employee B1FA2F0D), "
 "$4,139.96 and $2,570.99 at “CLAIM ADJ/AIR CANADA” (Employee 79229F61), $2,589.45 at "
 "JORGENSEN LABORATORIES, $2,399.60 at STAPLES and $2,084.52 at “Claim ADJ/21ST CENTURY”.",
 "Conclusion: the population splits cleanly, and the split is reassuring. A large share of the "
 "biggest unmatched credits carry vendor names beginning “CLAIM ADJ/” — Air Canada, "
 "Kroger, The Home Depot, Lowe's, Dell — which are Bank of America dispute adjustments. Those "
 "are the control working exactly as the procedure intends: the cardholder checked the Bank "
 "Statement, found a problem and disputed it. The genuine exceptions are the credits at ordinary "
 "merchants with no matching charge and no dispute marker — INTL COLD STORAGE, Jorgensen "
 "Laboratories, Staples, Best Buy — where the University received money back for something it "
 "cannot be shown to have bought on that card. Prior-year purchases are the most likely innocent "
 "explanation and can be eliminated by widening the match window to 2013.",
 "Follow-up: re-run the match against 2013 transactions to clear the prior-year cases, then request "
 "return documentation for what remains. Employee B1FA2F0D (55 credits, $18,072.26) and Employee "
 "5BA61357 (44 credits, $11,127.10) warrant a walk-through of how returns and credits are "
 "documented on those cards.",
],
}
