import json
from app.utils.utils_file import get_list_of_objects_from_file
from app.utils.utils_file import save_to_file
from telegram import constants


def nest_obj(obj, obj_contained):
    obj['reply_to_msg_obj'] = obj_contained
    return obj


def generate_nested_obj(path, channel):
    list_objs = get_list_of_objects_from_file(path, channel)
    dict_objs = {obj.get('id'): obj for obj in list_objs}
    dict_objs[-1] = 'error'
    list_new = []
    for obj in list_objs:
        if obj['reply_to_msg_id']:
            list_new.append(
                nest_obj(obj, dict_objs.get(obj['reply_to_msg_id'], -1))
            )
        else:
            list_new.append(obj)
    list_new_dumped = json.dumps(list_new)
    save_to_file(
        constants.PATH_TELEGRAM_MESSAGES, channel+'_nested', list_new_dumped
    )

generate_nested_obj(constants.PATH_TELEGRAM_MESSAGES, constants.BLUE_CAPITAL_FX)
