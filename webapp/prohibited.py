"""The prohibited-purchase categories from the OSU P-card procedure.

Each category gives the auditor a starting set of search terms: `description`
terms are searched in the merchant-supplied line detail, `vendor` terms in the
merchant name.  They are starting points, not a definitive test -- the notes
record the false positives found when the 2014 data was tested.
"""

CATEGORIES = [
    {
        "key": "alcohol",
        "label": "Alcohol",
        "description": ["beer", "wine", "vodka", "whiskey", "keg"],
        "vendor": ["liquor", "bottle shop", "brewery", "brewing", "wine cella", "package store"],
        "note": "Search the vendor rather than the description: 'alcohol' in a description is "
                "almost always a laboratory reagent (ethyl or isopropyl alcohol).",
    },
    {
        "key": "cash",
        "label": "Cash, cash advances and ATM",
        "description": ["cash advance", "money order", "wire transfer"],
        "vendor": ["atm", "western union", "moneygram"],
        "note": "No cash or ATM merchant category appears in 2014 -- the MCC block appears to be "
                "working. Search anyway when reviewing a later year.",
    },
    {
        "key": "decorations",
        "label": "Decorations",
        "description": ["decorat", "christmas", "holiday light", "garland", "wreath", "balloon"],
        "vendor": ["decor", "party", "hobby lobby", "michaels"],
        "note": "Party and craft-store purchases are often legitimate teaching or lab supplies; "
                "read the description before concluding.",
    },
    {
        "key": "donations",
        "label": "Donations and sponsorships",
        "description": ["donation", "sponsor", "contribution", "gala", "fundraiser", "pledge"],
        "vendor": ["foundation", "charit", "united way", "society of"],
        "note": "Professional-society payments are usually dues or registrations, which are "
                "allowable; a sponsorship is not.",
    },
    {
        "key": "gasoline",
        "label": "Gasoline",
        "description": ["gasoline", "unleaded", "diesel"],
        "vendor": ["oil co", "fuel", "petroleum", "shell", "phillips 66", "conoco", "quiktrip"],
        "note": "Bulk fuel deliveries for farm and research equipment look identical to vehicle "
                "fill-ups here; charges over $1,000 are almost always bulk deliveries.",
    },
    {
        "key": "gifts",
        "label": "Gifts, gift cards and gift certificates",
        "description": ["gift card", "gift certif", "candy", "greeting card"],
        "vendor": ["gift", "florist", "flowers", "hallmark", "edible arrangement"],
        "note": "Gift cards are a State-statute violation, so escalate any hit immediately. "
                "'FLORISTS SUPPLIES, NURSERY STOCK' vendors are usually legitimate nursery stock.",
    },
    {
        "key": "insurance",
        "label": "Insurance",
        "description": ["premium", "coverage", "policy"],
        "vendor": ["insurance", "assurance", "underwrit", "state farm", "vfis"],
        "note": "Insurance must go on a requisition through Risk and Property Management. "
                "Shipping insurance inside a repair invoice is a false positive.",
    },
    {
        "key": "latefees",
        "label": "Late fees",
        "description": ["late fee", "late charge", "finance charge", "interest charge", "penalty"],
        "vendor": [],
        "note": "None found in 2014, which also suggests transactions are being processed inside "
                "the five-day window.",
    },
    {
        "key": "postage",
        "label": "Mail and postage",
        "description": ["postage", "stamps", "certified mail", "registered mail", "parcel post"],
        "vendor": ["usps", "postal", "post office", "pitney", "stamps.com"],
        "note": "All mail must go through University Mailing. Inbound freight on a purchase "
                "(FedEx, UPS) is normally allowable -- outbound mail is not.",
    },
    {
        "key": "moving",
        "label": "Moving expenses",
        "description": ["moving", "relocation", "van line", "packing service"],
        "vendor": ["van lines", "u-haul", "uhaul", "penske", "two men and a truck", "movers"],
        "note": "A requisition is required for employee moving expenses. Equipment rental from "
                "the same vendors is a common false positive.",
    },
    {
        "key": "personal",
        "label": "Personal purchases of any type",
        "description": ["personal", "grocer", "clothing", "shoes", "haircut"],
        "vendor": ["spa", "salon", "gym", "fitness", "nail", "barber", "netflix", "spotify"],
        "note": "The broadest category and the noisiest. Rank hits by amount and by how many "
                "times the same cardholder appears.",
    },
    {
        "key": "memberships",
        "label": "Personal and individual memberships, including dues",
        "description": ["membership", "dues", "annual membership", "renewal"],
        "vendor": ["country club", "golf club", "gym", "fitness", "athletic club", "sam's club", "costco"],
        "note": "Institutional professional-society dues are allowable; an individual membership "
                "is not. Look for the same amount recurring annually on one card.",
    },
    {
        "key": "salaries",
        "label": "Salaries, wages and benefits",
        "description": ["salary", "wages", "stipend", "honorarium", "benefit"],
        "vendor": ["payroll", "paychex", "adp"],
        "note": "Honoraria to visiting speakers are the usual hit and must go through payroll or "
                "accounts payable, not the card.",
    },
    {
        "key": "awards",
        "label": "Service and incentive awards, and items bought for an employee",
        "description": ["award", "plaque", "engrav", "recognition", "retirement"],
        "vendor": ["awards", "trophy", "engraving", "crown trophy"],
        "note": "Student and external awards may be allowable; anything purchased for an employee "
                "must go on a requisition.",
    },
]
