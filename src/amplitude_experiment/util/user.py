from typing import Dict, Any

from ..user import User


def user_to_evaluation_context(user: User) -> Dict[str, Any]:
    user_groups = user.groups
    user_group_properties = user.group_properties
    user_group_cohort_ids = user.group_cohort_ids
    user_dict = {key: value for key, value in user.__dict__.copy().items() if value is not None}
    user_dict.pop('groups', None)
    user_dict.pop('group_properties', None)
    user_dict.pop('group_cohort_ids', None)
    context = {'user': user_dict} if len(user_dict) > 0 else {}

    if user_groups is None:
        return context

    groups: Dict[str, Dict[str, Any]] = {}
    for group_type, group_names in user_groups.items():
        if isinstance(group_names, list) and len(group_names) > 0:
            group_name = group_names[0]
        else:
            continue

        group_name_map = {'group_name': group_name}

        if user_group_properties:
            group_properties_type = user_group_properties.get(group_type)
            if group_properties_type:
                group_properties_name = group_properties_type.get(group_name)
                if group_properties_name:
                    group_name_map['group_properties'] = group_properties_name

        if user_group_cohort_ids:
            group_cohort_ids_type = user_group_cohort_ids.get(group_type)
            if group_cohort_ids_type:
                group_cohort_ids_name = group_cohort_ids_type.get(group_name)
                if group_cohort_ids_name:
                    group_name_map['cohort_ids'] = group_cohort_ids_name

        groups[group_type] = group_name_map

    context['groups'] = groups
    return context
