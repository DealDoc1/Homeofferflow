"""Verify provider-persisted completion rules before an invitation is sent."""


def controls_match(document, expected_fields, checkbox_groups, conditional_rules):
    """Compare documented group/rule semantics, ignoring generated UUIDs.

    Checkbox responses may identify members by field UUID instead of api_id;
    resolve only through the already geometry/recipient-verified field list.
    Unexpected groups/rules fail closed when these new controls are requested.
    """
    if not isinstance(document,dict):return False
    try:
        actual_fields={f['api_id']:f for group in document['fields'] for f in group}
        expected={f['api_id']:f for group in expected_fields for f in group}
        aliases={str(f['id']):key for key,f in actual_fields.items() if f.get('id')}
        def api_id(value):return aliases.get(str(value),str(value))
        def groups(rows):
            if not isinstance(rows,list):raise ValueError()
            result={}
            for group in rows:
                name=group['group_name']
                if name in result or group.get('validation')!='exact' or type(group.get('required')) is not bool:raise ValueError()
                ids=group['checkbox_ids']
                if not isinstance(ids,list) or len(ids)!=len(set(ids)):raise ValueError()
                result[name]=(str(group['recipient_id']),tuple(sorted(api_id(v) for v in ids)),
                              group['validation'],group['required'],int(group['exact_value']))
            return result
        if groups(checkbox_groups)!=groups(document.get('checkbox_groups') or []):return False
        def rules(rows):
            if not isinstance(rows,list):raise ValueError()
            result=[]
            for rule in rows:
                conditions=[]
                for index,item in enumerate(sorted(rule['conditions'],key=lambda value:value.get('position',1))):
                    conditions.append((item['condition_type'],item['status'],
                        'and_operator' if index==0 else item.get('join_operator','and_operator'),
                        tuple(sorted(api_id(value) for value in item['field_api_ids']))))
                result.append((api_id(rule['target_id']),rule['action_type'],
                    tuple(sorted(api_id(value) for value in rule['action_field_ids'])),tuple(conditions)))
            return sorted(result)
        if rules(conditional_rules)!=rules(document.get('conditional_rules') or []):return False
        # A required=true checkbox pair defeats "choose exactly one". A lost
        # text length constraint can put answer text outside the reviewed box.
        for key,field in expected.items():
            if field.get('type') not in {'checkbox','text'}:continue
            returned=actual_fields[key]
            for option in ('required','fixed_width','validation','validation_regex','validation_regex_error_message'):
                if option in field and returned.get(option)!=field[option]:return False
        return True
    except (KeyError,TypeError,ValueError,AttributeError):return False
