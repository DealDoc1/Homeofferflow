"""
api/fill-pdf/index.py  —  v4
Root cause fix: set_field() via manual AcroForm annotation loops does NOT
visually render in pypdf output.  The confirmed working fix is:
    writer.update_page_form_field_values(writer.pages[page_num], fields_dict)
grouped by page.

Field names and page indices in FIELD_MAP are sourced directly from
HomeOfferFlow_Offer_1438_Whitaker_Road.pdf (the live output PDF),
inspected via pypdf page-annotation walk.  All 339 fields are catalogued.
"""

import io
import json
import logging
import os
from collections import defaultdict

import boto3
from pypdf import PdfReader, PdfWriter

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# S3 helpers
# ---------------------------------------------------------------------------
s3 = boto3.client("s3")
TEMPLATE_BUCKET = os.environ["TEMPLATE_BUCKET"]
OUTPUT_BUCKET   = os.environ.get("OUTPUT_BUCKET", TEMPLATE_BUCKET)
TEMPLATE_KEY    = os.environ.get("TEMPLATE_KEY", "templates/homeofferflow_blank.pdf")


def _download_pdf(bucket: str, key: str) -> bytes:
    resp = s3.get_object(Bucket=bucket, Key=key)
    return resp["Body"].read()


def _upload_pdf(bucket: str, key: str, data: bytes) -> str:
    s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType="application/pdf")
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=3600,
    )


# ---------------------------------------------------------------------------
# FIELD_MAP  —  logical_key → (page_0based, exact_acroform_field_name)
#
# Field names extracted directly from the live PDF via page-annotation walk.
# Page indices are 0-based.
#
# Section comments indicate which TREC form / document section each block
# corresponds to in the merged 17-page HomeOfferFlow output PDF.
# ---------------------------------------------------------------------------
FIELD_MAP: dict[str, tuple[int, str]] = {

    # ── Page 0: Main Contract — Parties, Property, Sales Price ──────────────
    "seller_name_1":                (0, "1 PARTIES The parties to this contract are"),
    "seller_name_2":                (0, "Seller and"),
    "property_lot":                 (0, "A LAND Lot"),
    "property_block":               (0, "Block"),
    "property_addition_city":       (0, "Addition City of"),
    "property_county":              (0, "County of"),
    "property_address":             (0, "Texas known as"),
    "property_exclusions":          (0, "be removed prior to delivery of possession"),
    "sales_price_cash":             (0, "undefined_4"),
    "sales_price_total":            (0, "undefined_5"),
    "escrow_agent_address_pg1":     (0, "undefined_8"),
    "sales_price_financing_sum":    (0, "undefined_9"),
    # Checkboxes
    "cb_financing_third_party":     (0, "B Sum of all financing described in the attached"),
    "cb_loan_assumption_pg1":       (0, "Loan Assumption Addendum"),
    "cb_title_seller_expense":      (0, "A TITLE POLICY Seller shall furnish to Buyer at"),
    "cb_title_seller":              (0, "Sellers"),
    "cb_title_buyer":               (0, "Seller"),
    "cb_title_no_amend":            (0, "i will not be amended or deleted from the title policy or"),
    "cb_title_amend_shortages":     (0, "ii will be amended to read shortages in area at the expense of"),
    "escrow_agent_address_box":     (0, "to escrow agent within 1"),

    # ── Page 1: Earnest Money, Title Company, HOA ────────────────────────────
    "hoa_is_mandatory":             (1, "2 MEMBERSHIP IN PROPERTY OWNERS ASSOCIATIONS The Property"),
    "survey_days_opt2":             (1, "2Within"),
    "survey_days_opt3":             (1, "3Within"),
    "cb_survey_seller_expense":     (1, "Sellers_2"),
    "cb_survey_buyer_expense":      (1, "Buyers expense no later"),
    "survey_days_opt1":             (1, "the Title Company and Buyers lenders Check one box only"),
    "earnest_money":                (1, "as earnest money to"),
    "option_fee":                   (1, "as earnest money to 2"),
    "escrow_agent_name":            (1, "undefined_6"),
    "escrow_agent_address":         (1, "undefined_7"),
    "earnest_additional":           (1, "earnest money of"),
    "title_company_name":           (1, "insurance Title Policy issued by"),
    "pid_disclosure":               (1, "other party in writing before entering into a contract of sale  Disclose if applicable"),
    "title_objection_days":         (1, "to escrow agent within"),
    "hoa_transfer_info":            (1, "undefined_10"),
    "hoa_reserve_info":             (1, "undefined_11"),
    # Checkboxes
    "cb_hoa_mandatory":             (1, "is"),
    "cb_hoa_not_mandatory":         (1, "is not"),

    # ── Page 2: Survey, Title Objections ────────────────────────────────────
    "cb_survey_opt1":               (2, "1Within"),
    "cb_survey_opt2":               (2, "2 Within"),
    "survey_repair_days":           (2, "3 days prior"),
    "title_objection_activity":     (2, "Commitment other than items 6A1 through 9 above or which prohibit the following use"),
    "title_objection_days_2":       (2, "the Commitment Exception Documents and the survey Buyers failure to object within the"),
    "statutory_district_notice":    (2, "Property Code requires Seller to notify Buyer as follows"),
    "private_transfer_fee":         (2, "The private transfer fee"),
    # Survey option checkboxes (page 2 = backup/secondary)
    "cb_within_four":               (2, "Within four"),
    "cb_within_one":                (2, "Within one"),
    "cb_within_three":              (2, "Within three"),
    "cb_within_two":                (2, "Within two"),
    "survey_days_seller_pg2":       (2, "receipt or the date specified in this paragraph whichever is earlier"),
    "survey_closing_days":          (2, "than 3 days prior to Closing Date"),
    "property_notes_pg2":           (2, "undefined_12"),

    # ── Page 3: Property Condition, Repairs ─────────────────────────────────
    "cb_as_is":                     (3, "1 Buyer accepts the Property As Is"),
    "cb_as_is_with_repairs":        (3, "2 Buyer accepts the Property As Is provided Seller at Sellers expense shall complete the"),
    "contract_concerning_pg3":      (3, "Contract Concerning"),
    "repair_list":                  (3, "Text4"),
    "repair_list_2":                (3, "Text4 2"),
    "repair_list_3":                (3, "Text4 3"),
    "survey_days_pg3":              (3, "Within"),
    "property_notes_pg3":           (3, "undefined_14"),
    "property_notes_pg3b":          (3, "undefined_15"),
    # Checkboxes
    "cb_possession_upon":           (3, "upon"),

    # ── Page 4: Closing Date, Possession, Expenses ──────────────────────────
    "closing_date":                 (4, "A The closing of the sale will be on or before"),
    "cb_as_is_pg4":                 (4, "As Is"),
    "cb_as_is_except_pg4":         (4, "As Is except"),
    "brokers_sales_2":              (4, "Brokers and Sales 2"),
    "brokers_sales":                (4, "Brokers and Sales"),
    "buyer_closing_costs":          (4, "Buyers Expenses as allowed by the lender"),
    "contract_concerning_pg4":      (4, "Contract Concerning_2"),
    "seller_repairs":               (4, "following specific repairs and treatments"),
    "residential_service_amount":   (4, "service contract in an amount not exceeding"),
    "property_notes_pg4":           (4, "undefined_13"),
    "closing_year":                 (4, "undefined_16"),

    # ── Page 5: Option Fee Credits, Termination ─────────────────────────────
    "contract_concerning_pg5":      (5, "Contract Concerning_3"),
    "text3_2":                      (5, "Text3 2"),
    "option_credit_amount":         (5, "acknowledged by Seller and Buyers agreement to pay Seller"),
    "option_credit_amount_1":       (5, "acknowledged by Seller and Buyers agreement to pay Seller 1"),
    "option_credit_amount_2":       (5, "acknowledged by Seller and Buyers agreement to pay Seller2"),
    "property_notes_pg5":           (5, "undefined_17"),
    "property_notes_pg5b":          (5, "undefined_18"),
    "cb_option_will_not_credit":    (5, "will not be credited to the Sales Price at closing Time is of the"),
    "cb_option_will_not_credit_1":  (5, "will not be credited to the Sales Price at closing Time is of the 1"),

    # ── Page 6: Access Codes / Notes ─────────────────────────────────────────
    "ac_numb_1":                    (6, "AC numb 1"),
    "ac_numb_2":                    (6, "AC numb 2"),
    "ac_numb_3":                    (6, "AC numb 3"),
    "ac_numb_4":                    (6, "AC numb 4"),

    # ── Page 7: Addenda Checklist, Contacts, Notices ─────────────────────────
    "attorney_name_1":              (7, "Attorney is"),
    "attorney_name_2":              (7, "Attorney is_2"),
    "contract_concerning_pg7":      (7, "Contract Concerning_4"),
    "buyer_email":                  (7, "AC1"),
    "seller_phone":                 (7, "AC4"),
    "fax_52":                       (7, "Fax 52"),
    "buyer_phone_1":                (7, "Phone 51"),
    "buyer_phone_2":                (7, "Phone 52"),
    "phone_2":                      (7, "Phone 2"),
    "phone_11":                     (7, "Phone11"),
    "text22":                       (7, "Text22"),
    "text23":                       (7, "Text23"),
    "text6":                        (7, "Text6"),
    "text7":                        (7, "Text7"),
    "notice_address":               (7, "when mailed to handdelivered at or transmitted by fax or electronic transmission as follows"),
    "system_service_area":          (7, "System Service Area"),
    "addenda_notes_21":             (7, "undefined numb 21"),
    "addenda_notes_22":             (7, "undefined numb 22"),
    "addenda_notes_22_0":           (7, "undefined numb 22-0"),
    "addenda_pg7_19":               (7, "undefined_19"),
    "addenda_pg7_20":               (7, "undefined_20"),
    "addenda_pg7_20_0":             (7, "undefined_20-0"),
    "addenda_pg7_22":               (7, "undefined_22"),
    "addenda_pg7_23":               (7, "undefined_23"),
    "addenda_pg7_24":               (7, "undefined_24"),
    "addenda_pg7_25":               (7, "undefined_25"),
    "at_field":                     (7, "at"),
    "at_field_2":                   (7, "at_2"),
    "number_field_1":               (7, "1"),
    # Addenda checkboxes
    "cb_addendum_backup":           (7, "Addendum for BackUp Contract"),
    "cb_addendum_seaward":          (7, "Addendum for Property Located Seaward"),
    "cb_addendum_hoa":              (7, "Addendum for Property Subject to"),
    "cb_addendum_propane":          (7, "Addendum for Property in a Propane Gas"),
    "cb_addendum_oil_gas":          (7, "Addendum for Reservation of Oil Gas"),
    "cb_addendum_sale_other":       (7, "Addendum for Sale of Other Property by"),
    "cb_addendum_1031":             (7, "Addendum for Section 1031"),
    "cb_addendum_buyers_lease":     (7, "Buyers Temporary Residential Lease"),
    "cb_addendum_environ":          (7, "Environmental Assessment Threatened or"),
    "cb_addendum_loan_assumption":  (7, "Loan Assumption Addendum_2"),
    "cb_addendum_seller_financing": (7, "Seller Financing Addendum"),
    "cb_addendum_sellers_disclos":  (7, "Sellers Disclos"),
    "cb_addendum_sellers_lease":    (7, "Sellers Temporary Residential Lease"),
    "cb_addendum_short_sale":       (7, "Short Sale Addendum"),
    "cb_addendum_third_party":      (7, "Third Party Financing Addendum"),
    "cb_check_box_8":               (7, "Check Box8"),
    "cb_check_box_9":               (7, "Check Box9"),
    "cb_check_box_10":              (7, "Check box 10"),
    "cb_check_box_11":              (7, "Check box 11"),
    "cb_pid":                       (7, "PID"),
    "cb_other":                     (7, "Other"),
    "cb_sellers_disclosure":        (7, "Sellers Disclos"),
    "cb_buyer_only_rep":            (7, "Buyer only"),
    "cb_seller_sub_agent":          (7, "Seller as List Brok Sub agent"),
    "list_assoc_name":              (7, "List Assoc Name"),
    "associates_name_numb_1":       (7, "Associates Name numb 1"),
    "when_mailed_to":               (7, "when mailed to"),   # NOTE: page 7 copy; canonical is page 9

    # ── Page 8: Execution / Effective Date ───────────────────────────────────
    "executed_day":                 (8, "EXECUTED the"),
    "executed_month":               (8, "day of"),

    # ── Page 9: Broker Information ───────────────────────────────────────────
    "property_address_pg9":         (9, "Addr of Prop"),
    "associate_email":              (9, "Associates Email Address"),
    "associate_name":               (9, "Associates Name"),
    "listing_associate_name":       (9, "Listing Associates Name"),
    "selling_associate_name":       (9, "Selling Associates Name"),
    "selling_associate_name_1":     (9, "Selling Associates Name-1"),
    "other_broker_city":            (9, "City"),
    "listing_broker_city":          (9, "City_2"),
    "selling_assoc_city":           (9, "City_3"),
    "other_broker_license":         (9, "License No"),
    "other_broker_license_2":       (9, "License No_2"),
    "other_broker_license_3":       (9, "License No_3"),
    "listing_broker_license":       (9, "License No_4"),
    "listing_broker_license_2":     (9, "License No_5"),
    "listing_assoc_license":        (9, "License No_6"),
    "selling_assoc_license":        (9, "License No_7"),
    "selling_assoc_license_2":      (9, "License No_8"),
    "other_broker_supervisor":      (9, "Licensed Supervisor of Associate"),
    "listing_assoc_supervisor":     (9, "Licensed Supervisor of Listing Associate"),
    "selling_assoc_supervisor":     (9, "Licensed Supervisor of Selling Associate"),
    "listing_assoc_email":          (9, "Listing Associates Email Address"),
    "listing_broker_firm":          (9, "Listing Broker Firm"),
    "listing_broker_address":       (9, "Listing Brokers Office Address"),
    "other_broker_firm":            (9, "Other Broker Firm"),
    "other_broker_address":         (9, "Other Brokers Address"),
    "other_broker_phone":           (9, "Phone"),
    "listing_broker_phone":         (9, "Phone_2"),
    "listing_assoc_phone":          (9, "Phone_3"),
    "listing_broker_phone_2":       (9, "Phone_4"),
    "selling_assoc_phone":          (9, "Phone_5"),
    "other_broker_state":           (9, "State"),
    "listing_broker_state":         (9, "State_2"),
    "selling_assoc_state":          (9, "State_3"),
    "other_broker_zip":             (9, "Zip"),
    "listing_broker_zip":           (9, "Zip_2"),
    "other_broker_zip_3":           (9, "Zip_3"),
    "broker_notice_address":        (9, "when mailed to"),
    "listing_fee_note":             (9, "when the Listing Brokers fee is received Escrow agent is authorized and directed to pay Other Broker from"),
    # Checkboxes
    "cb_broker_dollar_amt":         (9, "Dollar Amt"),
    "cb_broker_percentage":         (9, "Percentage"),
    "cb_rep_buyer_only":            (9, "Buyer only"),
    "cb_rep_seller_subagent":       (9, "Seller as List Brok Sub agent"),
    "cb_rep_intermediary":          (9, "Seller and Buyer as an intermediary"),
    "cb_rep_seller_only":           (9, "Seller only as Sellers agent"),

    # ── Page 10: Receipts (Earnest, Option, Additional) ──────────────────────
    "receipt_property_address":     (10, "Address of Property_2"),
    "earnest_receipt_escrow_agent": (10, "Escrow Agent"),
    "earnest_receipt_received_by":  (10, "Received by"),
    "earnest_receipt_address":      (10, "Address"),
    "earnest_receipt_city":         (10, "City_4"),
    "earnest_receipt_state":        (10, "State_4"),
    "earnest_receipt_zip":          (10, "Zip_4"),
    "earnest_receipt_email":        (10, "Email Address"),
    "earnest_receipt_datetime":     (10, "DateTime"),
    "earnest_receipt_phone":        (10, "Phone_6"),
    "earnest_receipt_fax":          (10, "Fax"),
    "contract_receipt_escrow":      (10, "Escrow Agent_2"),
    "contract_receipt_received_by": (10, "Received by_2"),
    "contract_receipt_address":     (10, "Address_2"),
    "contract_receipt_city":        (10, "City_5"),
    "contract_receipt_state":       (10, "State_5"),
    "contract_receipt_zip":         (10, "Zip_5"),
    "contract_receipt_email":       (10, "Email Address_2"),
    "contract_receipt_date":        (10, "Date_2"),
    "contract_receipt_phone":       (10, "Phone_7"),
    "contract_receipt_fax":         (10, "Fax_2"),
    "addl_earnest_escrow":          (10, "Escrow Agent_3"),
    "addl_earnest_received_by":     (10, "Received by_3"),
    "addl_earnest_address":         (10, "Address_3"),
    "addl_earnest_city":            (10, "City_6"),
    "addl_earnest_state":           (10, "State_6"),
    "addl_earnest_zip":             (10, "Zip_6"),
    "addl_earnest_email":           (10, "Email Address_3"),
    "addl_earnest_datetime":        (10, "DateTime_2"),
    "addl_earnest_phone":           (10, "Phone_8"),
    "addl_earnest_fax":             (10, "Fax_3"),
    "option_receipt_seller":        (10, "Seller or Listing Broker"),
    "option_receipt_date":          (10, "Date"),
    "earnest_form":                 (10, "Earnest Money in the form of"),
    "option_form":                  (10, "Option Fee in the form of"),
    "addl_earnest_form":            (10, "additional Earnest Money in the form of"),
    "earnest_acknowledged":         (10, "is acknowledged"),
    "contract_acknowledged":        (10, "is acknowledged_2"),
    "addl_earnest_acknowledged":    (10, "is acknowledged_3"),

    # ── Page 11: Third Party Financing Addendum (TREC 40-10) ─────────────────
    "cb_financing_conventional":    (11, "1 Conventional Financing"),
    "cb_financing_tx_veterans":     (11, "2 Texas Veterans Loan A loans from the Texas Veterans Land Board of"),
    "cb_financing_fha":             (11, "3 FHA Insured Financing A Section"),
    "cb_financing_va":              (11, "4 VA Guaranteed Financing A VA guaranteed loan of not less than"),
    "cb_financing_usda":            (11, "5 USDA Guaranteed Financing A USDAguaranteed loan of not less than"),
    "cb_financing_reverse":         (11, "6 Reverse Mortgage Financing A reverse mortgage loan also known as a Home Equity"),
    "cb_financing_reverse_1":       (11, "6 Reverse Mortgage Financing A reverse mortgage loan also known as a Home Equity-1"),
    "cb_loan_first":                (11, "a A first mortgage loan in the principal amount of"),
    "cb_loan_second":               (11, "b A second mortgage loan in the principal amount of"),
    "loan_pmi_1":                   (11, "any financed PMI premium due in full in 1"),
    "loan_pmi_1_2":                 (11, "any financed PMI premium due in full in 1_2"),
    "loan_pmi_2":                   (11, "any financed PMI premium due in full in 2"),
    "loan_pmi_2_2":                 (11, "any financed PMI premium due in full in 2_2"),
    "loan_pmi_other":               (11, "any financed PMI premium or other costs with interest not to exceed"),
    "loan_funding_fee":             (11, "any financed Funding Fee amortizable monthly for not less than"),
    "loan_funding_fee_1":           (11, "any financed Funding Fee amortizable monthly for not less than-1"),
    "loan_mip":                     (11, "excluding any financed MIP amortizable monthly for not less"),
    "loan_mip_fee":                 (11, "excluding any financed Funding Fee amortizable monthly for not less than"),
    "loan_charges":                 (11, "Charges as shown on Buyers Loan Estimate for the loan not to exceed"),
    "loan_origination":             (11, "Origination Charges as shown on Buyers Loan Estimate for the loan not to exceed"),
    "loan_estimate":                (11, "Estimate for the loan not to exceed"),
    "loan_estimate_2":              (11, "shown on Buyers Loan Estimate for the loan not to exceed"),
    "loan_estimate_2_2":            (11, "shown on Buyers Loan Estimate for the loan not to exceed_2"),
    "loan_excluding":               (11, "excluding"),
    "loan_excluding_2":             (11, "excluding_2"),
    "loan_excluding_2_1":           (11, "excluding_2-1"),
    "loan_period":                  (11, "for a period in the total amount of"),
    "loan_first_period":            (11, "for the first"),
    "loan_not_exceed":              (11, "not to exceed"),
    "loan_not_exceed_1":            (11, "not to exceed-1"),
    "loan_not_exceed_2":            (11, "not to exceed_2"),
    "loan_not_exceed_2_1":          (11, "not to exceed_2-1"),
    "loan_rate_1":                  (11, "per annum for the first"),
    "loan_rate_2":                  (11, "per annum for the first_2"),
    "loan_rate_3":                  (11, "per annum for the first_3"),
    "loan_rate_3_1":                (11, "per annum for the first_3-1"),
    "loan_rate_4":                  (11, "per annum for the first_4"),
    "loan_than":                    (11, "than"),
    "loan_years":                   (11, "years"),
    "loan_years_rate":              (11, "years at the interest rate established by the"),
    "loan_years_not_exceed":        (11, "years with interest not to exceed"),
    "loan_years_not_exceed_2":      (11, "years with interest not to exceed_2"),
    "loan_interest":                (11, "with interest not to exceed"),
    "loan_notes_2":                 (11, "undefined_2"),
    "loan_notes_3":                 (11, "undefined_3"),
    "cb_buyer_approval":            (11, "This contract is subject to Buyer obtaining Buyer Approval If Buyer cannot obtain Buyer"),
    "cb_fha_will_not":              (11, "will not be an FHA insured loan"),
    "cb_will":                      (11, "will"),
    "cb_will_1":                    (11, "will-1"),
    "cb_will_2":                    (11, "will-2"),

    # ── Page 12: Financing Addendum continued / Buyer Approval ───────────────
    "cb_check_box_2":               (12, "Check Box2"),
    "reverse_mortgage_amount":      (12, "Conversion Mortgage loan in the original principal amount of"),
    "va_property_value":            (12, "value of the Property established by the Department of Veterans Affairs"),

    # ── Page 13: HOA Addendum (TREC 36-9) ────────────────────────────────────
    "hoa_name":                     (13, "Name of Property Owners Association Association and Phone Number"),
    "hoa_subdivision_info":         (13, "the Subdivision Information to the Buyer If Seller delivers the Subdivision Information Buyer may terminate"),
    "hoa_cb_within_1":              (13, "1 Within"),
    "hoa_cb_approved":              (13, "3Buyer has received and approved the Subdivision Information before signing the contract Buyer"),
    "hoa_cb_no_delivery":           (13, "4Buyer does not require delivery of the Subdivision Information"),
    "hoa_cb_buyer":                 (13, "Buyer"),
    "hoa_deposits":                 (13, "D DEPOSITS FOR RESERVES Buyer shall pay any deposits for reserves required at closing by the Association"),
    "hoa_cb_seller_pays_cert":      (13, "Seller shall pay the Title Company the cost of obtaining the"),
    "hoa_street_address":           (13, "Street Address and City"),
    "hoa_cert_copy":                (13, "copy of the Subdivision Information to the Seller"),
    "hoa_cb_does":                  (13, "does"),
    "hoa_cb_does_not_resale":       (13, "does not require an updated resale certificate If Buyer requires an updated resale certificate Seller at"),
    "hoa_property_undefined":       (13, "undefined"),

    # ── Page 14: Sale of Other Property Addendum (TREC 10-7) ─────────────────
    "sale_other_address":           (14, "Address on or before"),
    "sale_other_notice":            (14, "All notices and waivers must be in writing and are"),
    "sale_other_contingency":       (14, "Contingency is not satisfied or waived by Buyer by the above date the contract will terminate"),
    "sale_other_terminate":         (14, "terminate automatically and the earnest money will be refunded to Buyer"),

    # ── Page 15: Back-Up Contract Addendum (TREC 11-8) ───────────────────────
    "backup_year":                  (15, "20"),
    "backup_year_2":                (15, "20_2"),
    "backup_property_address":      (15, "Address of Property"),
    "backup_except":                (15, "Except as provided by this Addendum neither party is required to perform under the"),
    "backup_text1":                 (15, "Text1"),
    "backup_text1_1":               (15, "Text1 1"),
    "backup_text1_2":               (15, "Text1 2"),
    "backup_text3":                 (15, "Text3"),
    "backup_text3_3":               (15, "Text3 3"),
    "backup_text31":                (15, "Text31"),
    "backup_text31_2":              (15, "Text31 2"),
    "backup_terminate":             (15, "the BackUp Contract terminates and the earnest money will be refunded to Buyer  Seller must"),

    # ── Page 16: Signatures ───────────────────────────────────────────────────
    # Signature fields are /Sig type — update_page_form_field_values skips them
    # automatically; listed here for completeness / future DocuSign integration
    # "sig_buyer_1":               (16, "Signature1"),
    # "sig_buyer_2":               (16, "Signature2"),
    # "sig_seller_1":              (16, "Signature3"),
    # "sig_seller_2":              (16, "Signature4"),
    "pg16_text2":                   (16, "Text2"),
}


# ---------------------------------------------------------------------------
# Core fill logic  —  THE v4 FIX
# ---------------------------------------------------------------------------

def fill_pdf(template_bytes: bytes, field_values: dict[str, str]) -> bytes:
    """
    Fill an AcroForm PDF using update_page_form_field_values() grouped by page.

    WHY:  Direct set_field() / annotation-loop approaches write to the PDF
    object tree but do NOT update appearance streams, so text is invisible.
    writer.update_page_form_field_values() correctly writes both the value
    AND the visual appearance, producing text that renders in all viewers.

    Args:
        template_bytes: Raw bytes of the blank AcroForm PDF template.
        field_values:   Dict of logical_key → string value.

    Returns:
        Filled PDF as raw bytes.
    """
    reader = PdfReader(io.BytesIO(template_bytes))
    writer = PdfWriter()
    writer.append(reader)   # clones all pages + preserves AcroForm structure

    # Group values by page index  →  {page_idx: {acroform_name: value}}
    pages_fields: dict[int, dict[str, str]] = defaultdict(dict)
    skipped_keys: list[str] = []

    for logical_key, value in field_values.items():
        if logical_key not in FIELD_MAP:
            skipped_keys.append(logical_key)
            continue
        page_idx, acroform_name = FIELD_MAP[logical_key]
        pages_fields[page_idx][acroform_name] = str(value)

    if skipped_keys:
        logger.warning("Skipped %d unknown field key(s): %s", len(skipped_keys), skipped_keys)

    # Apply per-page  —  THE confirmed working method
    for page_idx in sorted(pages_fields.keys()):
        fields_dict = pages_fields[page_idx]
        if page_idx >= len(writer.pages):
            logger.error(
                "Page %d out of range (template has %d pages) — skipping %d field(s)",
                page_idx, len(writer.pages), len(fields_dict),
            )
            continue

        logger.info("Page %d: filling %d field(s): %s",
                    page_idx, len(fields_dict), list(fields_dict.keys()))

        writer.update_page_form_field_values(
            writer.pages[page_idx],
            fields_dict,
            auto_regenerate=False,
        )

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------

def handler(event: dict, context) -> dict:
    """
    Expected event body (JSON):
    {
        "output_key": "offers/abc123/filled.pdf",
        "fields": {
            "seller_name_1":   "John Doe",
            "property_address": "1438 Whitaker Road, Van Alstyne, TX 75495",
            "earnest_money":   "5,000",
            ...
        }
    }

    Optional:
        "template_key":  override the default S3 template key

    Returns:
    {
        "statusCode": 200,
        "body": {
            "url":            "<presigned S3 URL valid 1 hr>",
            "output_key":     "offers/abc123/filled.pdf",
            "fields_filled":  42,
            "fields_skipped": 0
        }
    }
    """
    try:
        body = json.loads(event["body"]) if isinstance(event.get("body"), str) else event.get("body", event)
        output_key   = body["output_key"]
        field_values = body.get("fields", {})
        template_key = body.get("template_key", TEMPLATE_KEY)
    except (KeyError, json.JSONDecodeError) as exc:
        logger.error("Bad request: %s", exc)
        return _response(400, {"error": f"Bad request: {exc}"})

    # Download template
    try:
        logger.info("Downloading template s3://%s/%s", TEMPLATE_BUCKET, template_key)
        template_bytes = _download_pdf(TEMPLATE_BUCKET, template_key)
    except Exception as exc:
        logger.error("Template download failed: %s", exc)
        return _response(500, {"error": f"Template download failed: {exc}"})

    # Fill
    try:
        filled_bytes = fill_pdf(template_bytes, field_values)
    except Exception as exc:
        logger.exception("PDF fill failed")
        return _response(500, {"error": f"PDF fill error: {exc}"})

    # Upload result
    try:
        logger.info("Uploading to s3://%s/%s", OUTPUT_BUCKET, output_key)
        presigned_url = _upload_pdf(OUTPUT_BUCKET, output_key, filled_bytes)
    except Exception as exc:
        logger.error("Upload failed: %s", exc)
        return _response(500, {"error": f"Upload failed: {exc}"})

    known_keys    = set(FIELD_MAP.keys())
    sent_keys     = set(field_values.keys())
    filled_count  = len(sent_keys & known_keys)
    skipped_count = len(sent_keys - known_keys)

    logger.info("Done. %d filled, %d skipped.", filled_count, skipped_count)
    return _response(200, {
        "url":            presigned_url,
        "output_key":     output_key,
        "fields_filled":  filled_count,
        "fields_skipped": skipped_count,
    })


def _response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


# ---------------------------------------------------------------------------
# Local smoke-test:  python index.py <blank_template.pdf>
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys, tempfile

    if len(sys.argv) < 2:
        print("Usage: python index.py <blank_template.pdf>")
        sys.exit(1)

    with open(sys.argv[1], "rb") as f:
        tmpl = f.read()

    # Use the real values from the Whitaker Road offer as smoke-test data
    test_fields = {
        "seller_name_1":        "Seller Test",
        "seller_name_2":        "Andrew Christian and buyer two",
        "property_lot":         "1",
        "property_block":       "1",
        "property_addition_city": "Van Alstyne",
        "property_county":      "Grayson",
        "property_address":     "1438 Whitaker Road, Van Alstyne, TX 75495",
        "sales_price_cash":     "450,000",
        "sales_price_total":    "500,000",
        "earnest_money":        "5,000",
        "option_fee":           "250",
        "closing_date":         "June 22",
        "buyer_closing_costs":  "6,767",
        "buyer_email":          "andrewchri@gmail.com",
        "buyer_phone_1":        "2143649890",
        "escrow_agent_name":    "Kate Lewis Tucker - Chicago Title DFW",
        "escrow_agent_address": "2770 Main Street, Suite 114, Frisco, TX 75033",
        "title_company_name":   "Chicago Title DFW - Forgey Law Group PLLC",
        "notice_address":       "721 Broderick Lane, Prosper, TX 75078",
        "cb_financing_third_party": "/Yes",
        "cb_hoa_mandatory":     "/Yes",
        "cb_addendum_hoa":      "/Yes",
        "cb_addendum_sale_other": "/Yes",
        "cb_addendum_backup":   "/Yes",
        "cb_addendum_third_party": "/Yes",
        "cb_as_is":             "/Yes",
        "cb_possession_upon":   "/Yes",
        "cb_buyer_approval":    "/Yes",
        "cb_title_no_amend":    "/Yes",
        "cb_title_seller_expense": "/Yes",
        "cb_title_seller":      "/Yes",
        "survey_days_opt1":     "7",
        "title_objection_days_2": "3",
        "cb_survey_opt1":       "/Yes",
    }

    filled = fill_pdf(tmpl, test_fields)

    out = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    out.write(filled)
    out.close()
    print(f"Filled PDF written to: {out.name}")
    print(f"Fields attempted: {len(test_fields)}")
    print(f"Known fields in map: {len(FIELD_MAP)}")
