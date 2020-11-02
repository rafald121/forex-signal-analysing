import json
import operator

from app import constants
from app.pairs import pairs_without_slash_lower
from app.utils import utils_file

empty_dict = {pair:0 for pair in pairs_without_slash_lower}

def check_coverage_for_channel(channel):
    json_files = utils_file.get_content_of_file(
        constants.PATH_PROJECT + constants.PATH_TELEGRAM_STATISTIC + '/' + channel)
    json_loaded = json.loads(json_files)
    for item in json_loaded:
        empty_dict[item['pair']] += 1
    sorted_dict = sorted(empty_dict.items(), key=operator.itemgetter(1), reverse=True)
    return sorted_dict
