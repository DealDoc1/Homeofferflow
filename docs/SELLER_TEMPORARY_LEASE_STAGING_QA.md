# Seller's Temporary Residential Lease — Staging QA

## Release scope

This document tests the staging-only implementation of **TREC 15-7 Seller's
Temporary Residential Lease**. It must not be promoted to the production offer
route until the completed, signed staging packet is visually approved.

Production remains on the verified TREC 20-19 Release 18B offer route. This
staging QA must not change the production offer-generation/signing flow.

The test is valid only against:

- `/api/fill_pdf_20_19_staging`
- `api/fill_pdf_20_19_staging.py`

## Exact browser-console payload

Paste the entire block in the deployed staging site's browser console. The
closure lets it be run repeatedly without redeclaration errors.

```js
(async () => {
  const offer = {
    userType: "agent",
    hasBuyerAgent: "yes",
    buyer1: "Seller Lease Buyer One",
    buyer2: "Seller Lease Buyer Two",
    buyerEmail: "andrewchri@gmail.com",
    buyer2Email: "andrewchri+sellerleasebuyer2@gmail.com",
    buyerPhone: "2143649890",
    buyerFax: "2145550101",
    buyerMailAddr: "721 Broderick Lane, Prosper, TX 75078",

    seller: "Seller Lease Seller One and Seller Lease Seller Two",
    sellerEmail: "seller@example.com",
    sellerPhone: "9725550134",
    sellerFax: "9725550199",
    sellerMailAddr: "100 Seller Lane, Van Alstyne, TX 75495",

    address: "1438 Whitaker Road",
    city: "Van Alstyne",
    county: "Grayson",
    zip: "75495",
    lotNumber: "1",
    blockNumber: "A",

    price: "500000",
    financing: "cash",
    loanAmount: "0",
    cashAmount: "500000",
    earnest: "5000",
    optionFee: "250",
    optionDays: "7",

    escrowAgent: "Chicago Title DFW",
    escrowAddress: "2770 Main Street, Frisco, TX 75033",
    titleCompany: "Chicago Title DFW",
    titlePayer: "buyer",
    titleAmendment: "buyer",
    survey: "buyerNew",
    surveyDays: "7",
    objectionDays: "5",
    hoa: "no",
    sellerDisclosure: "received",
    sellerWaterDisclosure: "received",
    asIs: "yes",

    closingDate: "2026-08-15",
    possession: "sellerTemporaryLease",
    sellerTemporaryLease: "yes",
    sellerTemporaryLeaseTerminationDate: "2026-08-31",
    sellerTemporaryLeaseRentPerDay: "125",
    sellerTemporaryLeaseDeposit: "1000",
    sellerTemporaryLeaseUtilitiesPaidByBuyer: "Water and trash",
    sellerTemporaryLeasePetsAllowed: "One dog under 40 pounds",
    sellerTemporaryLeaseSpecialProvisions:
      "Tenant will maintain the yard and return all keys and garage remotes when possession is surrendered.",
    sellerTemporaryLeaseHoldoverPerDay: "300",

    saleContingency: "no",
    backupOffer: "no",
    appraisalAddendum: "none",
    nonRealtyItems: "no",
    leadBasedPaint: "no",
    yearBuilt: "2005",

    agentName: "Andrew Christian",
    agentEmail: "andrew@ondemanddfw.com",
    agentPhone: "2143649890",
    agentLicense: "0738821",
    agentBrokerage: "OnDemand Realty",
    agentBrokerLicense: "9010832",
    teamName: "The Christian Group"
  };

  const payload = {
    type: "checkout.session.completed",
    data: {
      object: {
        customer_email: offer.buyerEmail,
        customer_details: { email: offer.buyerEmail },
        metadata: {
          plan: "agent-subscription",
          offer_data: JSON.stringify(offer)
        }
      }
    }
  };

  const response = await fetch("/api/fill_pdf_20_19_staging", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const result = await response.json();
  console.log("status:", response.status);
  console.log("result:", result);
  console.log("signwell:", JSON.stringify(result.signwell, null, 2));
})();
```

Use the two different buyer emails exactly as shown; SignWell rejects duplicate
recipient email addresses. Sign both buyers, download the completed packet,
then retain it with the staging QA record.

## Required visual audit

| Packet page | Field or control | Expected result |
|---:|---|---|
| 6 | Paragraph 10A | Seller temporary lease possession checkbox is selected; buyer temporary lease remains blank. |
| 9 | Paragraph 22 | Seller's Temporary Residential Lease checkbox is selected; Buyer's Temporary Residential Lease remains blank. |
| 13 | Parties | Buyers appear as landlords; sellers appear as tenants. |
| 13 | Property and term | Address and August 31, 2026 termination date are in their blanks. |
| 13 | Money terms | $125 daily rent and $1,000 deposit are in their respective blanks. |
| 13 | Terms | Utilities, pets, and special provisions are readable and stay inside their printed areas. |
| 13 | Initials | Each buyer/landlord initial field is on the printed landlord initial line. |
| 14 | Holdover / notices | $300 holdover amount and buyer/seller notice contacts are in their blanks. |
| 14 | Signatures and dates | Both buyer/landlord signature and date fields sit on their respective landlord lines; no field overlaps body text or footer. |
| Entire packet | Addenda ordering | No unrequested lease or finance addendum is present; page count is 14 for this exact payload. |

## Release gate

Keep this feature staging-only until all rows above pass in the **completed
signed PDF**. A source-render check is not a substitute for completed SignWell
signature/date placement QA.
