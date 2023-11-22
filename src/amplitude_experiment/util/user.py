from typing import Dict, Any

from ..user import User


def user_to_evaluation_context(user: User) -> Dict[str, Any]:
    user_groups = user.groups
    user_group_properties = user.group_properties
    user_dict = {key: value for key, value in user.__dict__.copy().items() if value is not None}
    user_dict.pop('groups', None)
    user_dict.pop('group_properties', None)
    context = {'user': user_dict} if len(user_dict) > 0 else {}
    if user_groups is None:
        return context
    groups: Dict[str, Dict[str, Any]] = {}
    for group_type in user_groups:
        group_name = user_groups[group_type]
        if type(group_name) == list and len(group_name) > 0:
            group_name = group_name[0]
        groups[group_type] = {'group_name': group_name}
        if user_group_properties is None:
            continue
        group_properties_type = user_group_properties[group_type]
        if group_properties_type is None or type(group_properties_type) != dict:
            continue
        group_properties_name = group_properties_type[group_name]
        if group_properties_name is None or type(group_properties_name) != dict:
            continue
        groups[group_type]['group_properties'] = group_properties_name
    context['groups'] = groups
    return context
