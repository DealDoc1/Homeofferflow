/* Shared seller and agent disclosure interview. No network or storage access. */
(function (root) {
  'use strict';
  const escape = value => String(value ?? '').replace(/[&<>"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[char]));
  const responseGroups = [
    ['Occupancy and roof', [['seller_occupancy','Is the seller currently occupying the property?']]],
    ['Systems and features', [
      ['range','Range'],['oven','Oven'],['microwave','Microwave'],['dishwasher','Dishwasher'],['trash_compactor','Trash Compactor'],['disposal','Disposal'],
      ['washer_dryer_hookups','Washer/Dryer Hookups'],['window_screens','Window Screens'],['rain_gutters','Rain Gutters'],['security_system','Security System'],
      ['fire_detection_equipment','Fire Detection Equipment'],['intercom_system','Intercom System'],['smoke_detector','Smoke Detector'],
      ['smoke_detector_hearing_impaired','Smoke Detector-Hearing Impaired'],['carbon_monoxide_alarm','Carbon Monoxide Alarm'],['emergency_escape_ladders','Emergency Escape Ladder(s)'],
      ['tv_antenna','TV Antenna'],['cable_tv_wiring','Cable TV Wiring'],['satellite_dish','Satellite Dish'],['ceiling_fans','Ceiling Fan(s)'],['attic_fans','Attic Fan(s)'],
      ['exhaust_fans','Exhaust Fan(s)'],['central_ac','Central A/C'],['central_heating','Central Heating'],['wall_window_ac','Wall/Window A/C'],
      ['plumbing_system','Plumbing System'],['septic_system','Septic System'],['public_sewer_system','Public Sewer System'],['patio_decking','Patio/Decking'],
      ['outdoor_grill','Outdoor Grill'],['fences','Fences'],['pool','Pool'],['sauna','Sauna'],['spa','Spa'],['hot_tub','Hot Tub'],['pool_equipment','Pool Equipment'],
      ['pool_heater','Pool Heater'],['automatic_lawn_sprinkler_system','Automatic Lawn Sprinkler System'],['fireplace_wood_burning','Fireplace(s) & Chimney (Wood burning)'],
      ['fireplace_mock','Fireplace(s) & Chimney (Mock)'],['natural_gas_lines','Natural Gas Lines'],['gas_fixtures','Gas Fixtures'],['lp_community','LP Community (Captive)'],
      ['lp_on_property','LP on Property'],['fuel_gas_black_iron','Fuel Gas: Black Iron Pipe'],['fuel_gas_corrugated_steel','Fuel Gas: Corrugated Stainless Steel Tubing'],
      ['fuel_gas_copper','Fuel Gas: Copper'],['garage_attached','Garage Attached'],['garage_not_attached','Garage Not Attached'],['carport','Carport'],
      ['garage_opener_electronic','Garage Door Opener Electronic'],['garage_opener_controls','Garage Door Opener Control(s)'],['water_heater_gas','Water Heater Gas'],
      ['water_heater_electric','Water Heater Electric'],['water_supply_city','Water Supply City'],['water_supply_well','Water Supply Well'],['water_supply_mud','Water Supply MUD'],
      ['water_supply_coop','Water Supply Co-op'],['liquid_propane_gas','Liquid propane gas'],['fuel_gas_piping','Fuel gas piping'],
      ['property_items_condition_issue','Are any listed items not working, defective, or in need of repair?']
    ]],
    ['Known defects', [
      ['defect_interior_walls','Interior walls'],['defect_ceilings','Ceilings'],['defect_floors','Floors'],['defect_exterior_walls','Exterior walls'],
      ['defect_doors','Doors'],['defect_windows','Windows'],['defect_roof','Roof'],['defect_foundation_slabs','Foundation/slabs'],['defect_sidewalks','Sidewalks'],
      ['defect_walls_fences','Walls/fences'],['defect_driveways','Driveways'],['defect_intercom','Intercom'],['defect_plumbing_sewers_septics','Plumbing/sewers/septics'],
      ['defect_electrical_systems','Electrical systems'],['defect_lighting_fixtures','Lighting fixtures'],['defect_other_structural_components','Other structural components']
    ]],
    ['Conditions', [
      ['active_termites','Active termites'],['previous_structural_or_roof_repair','Previous structural/roof repair'],['termite_or_wood_rot_needing_repair','Termite/wood rot needing repair'],
      ['hazardous_toxic_waste','Hazardous/toxic waste'],['previous_termite_damage','Previous termite damage'],['asbestos_components','Asbestos components'],
      ['previous_termite_treatment','Previous termite treatment'],['urea_formaldehyde_insulation','Urea-formaldehyde insulation'],['improper_drainage','Improper drainage'],
      ['radon_gas','Radon gas'],['water_damage_not_flood','Water damage (not flood)'],['lead_based_paint','Lead-based paint'],
      ['landfill_settling_soil_movement_fault_lines','Landfill/settling/soil movement/fault lines'],['aluminum_wiring','Aluminum wiring'],
      ['single_blockable_main_drain','Single blockable main drain'],['previous_fires','Previous fires'],['unplatted_easements','Unplatted easements'],
      ['subsurface_structure_or_pits','Subsurface structure or pits'],['previous_methamphetamine_use','Previous methamphetamine use']
    ]],
    ['Flood and repairs', [
      ['property_needs_repair','Property needs repair'],['working_smoke_detectors','Working smoke detectors'],['present_flood_insurance','Present flood insurance coverage'],
      ['previous_reservoir_release_flooding','Previous reservoir release flooding'],['previous_natural_flood_water_penetration','Previous natural-flood water penetration'],
      ['in_100_year_floodplain','In 100-year floodplain'],['in_500_year_floodplain','In 500-year floodplain'],['in_floodway','In a floodway'],
      ['in_flood_pool','In a flood pool'],['in_reservoir','In a reservoir'],['filed_flood_claim','Filed flood claim'],
      ['received_fema_or_sba_assistance','Received FEMA/SBA assistance']
    ]],
    ['Additional disclosures', [
      ['unpermitted_modifications','Unpermitted modifications'],['hoa_assessments','HOA assessments'],['common_area','Common area'],
      ['deed_or_ordinance_violations','Deed/ordinance violations'],['property_lawsuits','Property lawsuits'],['health_or_safety_condition','Health/safety condition'],
      ['large_rainwater_system','Large rainwater system'],['groundwater_or_subsidence_district','Groundwater/subsidence district'],
      ['conservation_easements','Conservation easements'],['covered_by_insurance','Covered by insurance'],['covered_by_windstorm_insurance','Covered by windstorm insurance'],
      ['unable_to_insure','Unable to insure'],['private_road_maintenance','Private-road maintenance'],['storage_tanks','Storage tanks'],
      ['large_aboveground_storage_tanks','Large aboveground storage tanks']
    ]]
  ];
  const waterGroups = [['TREC-61-0 water rights', [
    ['in_groundwater_district','In groundwater conservation district'],['water_wells_known','Water wells known'],
    ['water_well_on_another_property','Water well on another property'],['water_well_relies_on_outside_rights','Relies on outside groundwater rights'],
    ['groundwater_rights_severed_sold_leased','Groundwater rights severed/sold/leased'],['surface_water_right','Surface-water right'],
    ['pond_lake_or_water_tank','Pond/lake/water tank']
  ]]];
  const explanationGroups = {
    'Occupancy and roof': [['seller_occupancy_duration','If unoccupied, how long since the seller occupied the property?'],
      ['roof_type','Roof type'],['roof_age','Approximate roof age']],
    'Systems and features': [['property_item_condition_description','Describe any listed items that are not working or need repair.']],
    'Known defects': [['other_structural_description','Identify any other structural components.'],
      ['known_defects_explanation','Explain any known defects or malfunctions.']],
    'Conditions': [['conditions_explanation','Explain any conditions the seller identified.']],
    'Flood and repairs': [
      ['smoke_detector_explanation','Explain a No or Unknown answer about working smoke detectors.'],
      ['repair_explanation','Describe any items, equipment, or systems that need repair.'],
      ['flood_history_explanation','Explain the flood history or flood-area answers.'],
      ['flood_claim_explanation','Explain any flood insurance claims.'],
      ['fema_assistance_explanation','Explain any FEMA or SBA flood assistance.'],
      ['repairs_flood_explanation','Other repairs or flood information (if needed).']
    ],
    'Additional disclosures': [
      ['additional_disclosures_explanation','Explain any additional disclosures the seller identified.'],
      ['notes','Other seller information (if needed).']
    ]
  };
  const waterExplanationGroups = [
    ['District and well details', [
      ['water_well_count_total','Total known wells'],['water_well_count_in_use','Wells currently in use'],
      ['water_well_count_capped','Wells capped, covered, plugged, or abandoned'],
      ['groundwater_district_name','Groundwater district name'],['groundwater_district_website','District website'],
      ['water_well_permits','Well registrations or permit numbers'],['well_description','Identify the well'],
      ['well_owners_operators','Well owners or operators'],['well_beneficiary','Well beneficiary'],
      ['well_agreement','Well agreement or understanding']
    ]],
    ['Other groundwater rights', [
      ['other_property_well_explanation','Describe the well on another property and any water-access agreement.'],
      ['outside_groundwater_explanation','Describe any groundwater rights outside the property.'],
      ['severed_groundwater_explanation','Describe any groundwater rights severed, sold, or leased.'],
      ['other_water_well_rights_explanation','Other water-well rights information (if needed).']
    ]],
    ['Surface-water details', [
      ['surface_water_right_number','Surface-water permit, filing, or adjudication number'],
      ['surface_water_ownership','Other owners and their respective interests'],
      ['notes','Other water-rights information (if needed).']
    ]]
  ];
  const renderExplanationFields = (kind, fields) => fields.map(([key,label]) => {
    const id = 'hofDisclosure_' + kind + '_' + escape(key);
    const attributes = ' id="' + id + '" data-' + kind + '-response="' + escape(key) + '" maxlength="3000"';
    const shortAnswer = ['groundwater_district_name','groundwater_district_website','surface_water_right_number',
      'seller_occupancy_duration','roof_type','roof_age','water_well_count_total','water_well_count_in_use','water_well_count_capped'].includes(key);
    return '<label class="hof-seller-explanation" for="' + id + '">' + escape(label) +
      (shortAnswer ? '<input type="text"' + attributes + '>' : '<textarea' + attributes + ' rows="3"></textarea>') + '</label>';
  }).join('');
  function collectDisclosureResponses(card, kind, previous = {}) {
    // Preserve older saved answers not represented by a control, but never
    // send the server-owned delivery journal back as a client response.
    const responses = Object.fromEntries(Object.entries(previous).filter(([key]) => !key.startsWith('_')));
    card.querySelectorAll('[data-' + kind + '-response]').forEach(field => {
      const key = kind === 'seller' ? field.dataset.sellerResponse : field.dataset.waterResponse;
      if (field.value !== '') responses[key] = field.value;
      else delete responses[key];
    });
    return responses;
  }
  function disclosureDetailRelevant(kind, key, seller, water) {
    const yes = value => value === 'Y';
    const groupYes = title => (responseGroups.find(group => group[0] === title)?.[1] || [])
      .some(([field]) => yes(seller[field]));
    if (kind === 'seller') {
      if (key.endsWith('_extent')) return yes(seller[key.slice(0, -7)]);
      if (key === 'seller_occupancy_duration') return seller.seller_occupancy === 'N';
      if (key === 'property_item_condition_description') return yes(seller.property_items_condition_issue);
      if (key === 'other_structural_description') return yes(seller.defect_other_structural_components);
      if (key === 'known_defects_explanation') return groupYes('Known defects');
      if (key === 'conditions_explanation') return groupYes('Conditions');
      if (key === 'smoke_detector_explanation') return ['N', 'U'].includes(seller.working_smoke_detectors);
      if (key === 'repair_explanation') return yes(seller.property_needs_repair);
      if (key === 'flood_history_explanation') return ['present_flood_insurance', 'previous_reservoir_release_flooding',
        'previous_natural_flood_water_penetration', 'in_100_year_floodplain', 'in_500_year_floodplain',
        'in_floodway', 'in_flood_pool', 'in_reservoir'].some(field => yes(seller[field]));
      if (key === 'flood_claim_explanation') return yes(seller.filed_flood_claim);
      if (key === 'fema_assistance_explanation') return yes(seller.received_fema_or_sba_assistance);
      if (key === 'additional_disclosures_explanation') return groupYes('Additional disclosures');
      if (key === 'repairs_flood_explanation') return false; // Retain older combined notes only when populated.
    } else {
      if (['groundwater_district_name', 'groundwater_district_website'].includes(key)) return yes(water.in_groundwater_district);
      if (['water_well_count_total', 'water_well_count_in_use', 'water_well_count_capped',
        'water_well_permits', 'well_ownership'].includes(key)) return yes(water.water_wells_known);
      if (['well_description', 'well_owners_operators', 'well_beneficiary', 'well_agreement'].includes(key))
        return yes(water.water_wells_known) && water.well_ownership === 'other';
      if (key === 'other_property_well_explanation') return yes(water.water_well_on_another_property);
      if (key === 'outside_groundwater_explanation') return yes(water.water_well_relies_on_outside_rights);
      if (key === 'severed_groundwater_explanation') return yes(water.groundwater_rights_severed_sold_leased);
      if (['surface_water_right_number', 'surface_water_ownership'].includes(key)) return yes(water.surface_water_right);
      if (key === 'other_water_well_rights_explanation') return false;
    }
    return null; // Ordinary questions and optional additional notes stay available.
  }
  function syncDisclosureDetails(card) {
    if (!card) return;
    const controls = kind => Array.from(card.querySelectorAll('[data-' + kind + '-response]'));
    const sellerFields = controls('seller'), waterFields = controls('water');
    const values = (fields, kind) => Object.fromEntries(fields.map(field => [
      kind === 'seller' ? field.dataset.sellerResponse : field.dataset.waterResponse, field.value]));
    const seller = values(sellerFields, 'seller'), water = values(waterFields, 'water');
    for (const [kind, fields] of [['seller', sellerFields], ['water', waterFields]]) {
      fields.forEach(field => {
        const key = kind === 'seller' ? field.dataset.sellerResponse : field.dataset.waterResponse;
        const relevant = disclosureDetailRelevant(kind, key, seller, water);
        if (relevant === null) return;
        const label = field.closest('label');
        if (!label) return;
        const hasValue = String(field.value ?? '').trim() !== '';
        const retained = !relevant && hasValue;
        label.classList.add('hof-seller-conditional');
        label.hidden = !relevant && !hasValue;
        let hint = label.querySelector('.hof-seller-saved-detail');
        if (retained && !hint) {
          hint = document.createElement('small');
          hint.className = 'hof-seller-saved-detail';
          hint.textContent = 'Saved details are kept. Review or clear them if they no longer apply.';
          label.appendChild(hint);
        }
        if (hint) hint.hidden = !retained;
      });
    }
  }
  const responsePrompt = '<p class="hof-seller-step-hint">Answer from the seller’s own knowledge. Choose Unknown if the seller is not sure. Where the form only offers Yes or No, an Unknown answer appears in the attached details without selecting either answer.</p>';
  const renderExtentFields = () => '<div class="hof-seller-response-grid">' + [
    ['in_100_year_floodplain','100-year floodplain'],['in_500_year_floodplain','500-year floodplain'],
    ['in_floodway','Floodway'],['in_flood_pool','Flood pool'],['in_reservoir','Reservoir']
  ].map(([key,label]) => '<label class="hof-seller-response-row"><span>' + label + ' extent, if Yes</span>' +
    '<select data-seller-response="' + key + '_extent"><option value="">—</option><option value="wholly">Wholly</option><option value="partly">Partly</option></select></label>').join('') + '</div>';
  const renderWaterResponses = () => waterGroups.map(([title, fields]) =>
    '<details><summary>' + escape(title) + '</summary><div class="hof-seller-response-grid">' +
    fields.map(([key,label]) => '<label class="hof-seller-response-row"><span>' + escape(label) + '</span><select data-water-response="' + escape(key) + '"><option value="">—</option><option value="Y">Yes (Y)</option><option value="N">No (N)</option><option value="U">Unknown (U)</option></select></label>').join('') +
    '</div></details>'
  ).join('') + waterExplanationGroups.map(([title, fields]) =>
    '<details><summary>' + escape(title) + '</summary>' +
    (title === 'District and well details' ? '<label class="hof-seller-explanation">Water-well ownership<select data-water-response="well_ownership"><option value="">—</option><option value="seller_only">All wells are owned or operated solely by the seller for this property</option><option value="other">Other owners, beneficiaries, or agreements</option></select></label>' : '') +
    renderExplanationFields('water', fields) + '</details>'
  ).join('');
  const groupPrompts = {'Systems and features':'Is each item present at the property? Answer the repair question at the end of this section separately.',
    'Known defects':'Are you aware of defects or malfunctions in any of these items?',
    'Conditions':'Are you aware of any of these conditions at the property?'};
  const renderResponses = () => responsePrompt + responseGroups.map(([title, fields]) =>
    '<details><summary>' + escape(title) + '</summary>' + (groupPrompts[title] ? '<p>' + escape(groupPrompts[title]) + '</p>' : '') + '<div class="hof-seller-response-grid">' +
    fields.map(([key,label]) => '<label class="hof-seller-response-row"><span>' + escape(label) + '</span><select data-seller-response="' + escape(key) + '"><option value="">—</option><option value="Y">Yes (Y)</option><option value="N">No (N)</option>' + (key === 'seller_occupancy' ? '' : '<option value="U">Unknown (U)</option>') + '</select></label>').join('') +
    '</div>' + (title === 'Flood and repairs' ? renderExtentFields() : '') + renderExplanationFields('seller', explanationGroups[title] || []) + '</details>'
  ).join('');
  root.hofDisclosureInterview = Object.freeze({renderResponses, renderWaterResponses, collectDisclosureResponses,
    syncDisclosureDetails, disclosureDetailRelevant});
})(window);
