"""Validate seller-entered facts without accepting identity or delivery data."""
import json
import uuid

from lib.seller_disclosure_explanations import DETAILS, validate_explanations
from lib.trec_seller_disclosure_schema import validate_response_keys


def required_answers(has_water=False):
    from lib import trec_seller_disclosure as source
    groups = [source.TREC_55_1_ITEM_ROWS, source.TREC_55_1_CONDITION_ROWS,
              source.TREC_55_1_CONDITION4_ROWS, source.TREC_55_1_FLOOD_ROWS, source.TREC_55_1_ADDITIONAL_ROWS]
    main = {r[0] for group in groups for r in group} | set(source.TREC_55_1_FEATURE_RESPONSES) | {
        'seller_occupancy', 'property_items_condition_issue', 'working_smoke_detectors',
        'property_needs_repair', 'filed_flood_claim', 'received_fema_or_sba_assistance'}
    water = {'in_groundwater_district','water_wells_known','water_well_on_another_property',
             'water_well_relies_on_outside_rights','groundwater_rights_severed_sold_leased',
             'surface_water_right','pond_lake_or_water_tank'} if has_water else set()
    return main, water


def parse_answers(data, *, has_water=False, require_complete=False):
    if not isinstance(data, dict):
        raise ValueError("Enter valid disclosure answers.")
    try:
        revision = str(uuid.UUID(str(data.get('reviewContentRevision') or '')))
    except (ValueError, TypeError, AttributeError):
        raise ValueError("Reload the latest disclosure before saving.")
    result = []
    for form, key in [('TREC-55-1', 'responseData'), ('TREC-61-0', 'waterRightsData')]:
        answers = data.get(key, {})
        if not isinstance(answers, dict) or any(not isinstance(k, str) or k.startswith('_') for k in answers):
            raise ValueError("Enter valid disclosure answers.")
        if 'property_address' in answers:
            raise ValueError("The property address is set by the saved disclosure.")
        validate_response_keys(form, answers)
        validate_explanations(form, answers)
        details = {d[0] for d in DETAILS[form]}
        for name, value in answers.items():
            if not isinstance(value, (str, bool, int)) or isinstance(value, int) and not isinstance(value, bool) and name not in details:
                raise ValueError("Choose a valid response for each disclosure question.")
            if name not in details and not name.startswith(('notes', 'question_', 'item_')) and name not in {
                'property_address', 'well_ownership'} and not name.endswith('_extent'):
                if value not in ('', 'Y', 'N', 'U', True, False):
                    raise ValueError("Choose Yes, No, or Unknown for each disclosure question.")
            if isinstance(value, str) and len(value) > 3000:
                raise ValueError("Each written answer must be at most 3,000 characters.")
        result.append(dict(answers))
    if not has_water and result[1]:
        raise ValueError("This disclosure does not include a water-rights form.")
    if len(json.dumps(result, ensure_ascii=False).encode('utf-8')) > 250000:
        raise ValueError("Disclosure responses are too large.")
    if require_complete:
        for answers, required in zip(result, required_answers(has_water)):
            if any(answers.get(key) not in ('Y','N','U',True,False) for key in required):
                raise ValueError("Answer every property question before confirming. Choose Unknown when you are not sure.")
        if result[0].get('seller_occupancy') not in ('Y','N',True,False):
            raise ValueError("Confirm whether you currently occupy the property.")
    return revision, result[0], result[1]
