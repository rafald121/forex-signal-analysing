import os
import json
import zipfile
from datetime import datetime, timedelta

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)


def copy_file(first, second):
    os.rename(first, second)


def is_file_exist(path):
    return os.path.exists(path)


def get_content_of_file(path):
    with open(path) as f:
        return f.read()


def save_to_file(path, name, content):
    complete_path = os.path.join(path, name)
    with open(complete_path, 'w') as file:
        file.write(content)


def get_list_of_objects_from_file(path, file_name):
    complete_path = os.path.join(path, file_name)
    content = get_content_of_file(complete_path)
    return get_list_from_json_list_from_file(content)


def get_list_from_json_list_from_file(file_content):
    list_of_obj = []
    json_loaded = json.loads(file_content)
    for item in json_loaded:
        if isinstance(item, str):
            item_loaded = json.loads(item)
            list_of_obj.append(item_loaded)
        else:
            list_of_obj.append(item)
    return list_of_obj


def dump_all_data(data):
    messages_dumped_list = [message for message in data]
    return json.dumps(messages_dumped_list)


def unzipfile(path_file, path_to_unzip):

    try:
        zip_ref = zipfile.ZipFile(path_file, 'r')
    except zipfile.BadZipFile:
        # for example: If .csv file appear in some of directory just return
        return
    except IsADirectoryError:
        return

    zip_ref.extractall(path_to_unzip)
    zip_ref.close()


def get_all_directories_of_directory(dir_path, without_first=False):
    """
    :param dir_path:
    :param without_first: if False we return also parent directory itself ( . )
                          if True we return only subdirs
    :return:
    """
    return [x[0] for x in os.walk(dir_path)][1:] if without_first else [x[0] for x in os.walk(dir_path)]


def get_files_for_directory(directory_path):
    return os.listdir(directory_path)


def get_pair_from_filename(filename):
    return filename[16:22]


def get_year_from_filename(filename):
    return filename[25:29]


def get_month_from_filename(filename):
    return filename[29:31] if len(filename) == 35 else ''


def build_file_name(pair, year, month):
    month = "{:02}".format(month)
    return f"HISTDATA_COM_MT_{pair}_M1{year}{month}.zip"


def is_file_older_than_days(path, days):
    date_from = datetime.now() - timedelta(days=days)
    file_created_at_ts = os.stat(path).st_atime
    file_created_at = datetime.utcfromtimestamp(file_created_at_ts)
    return file_created_at < date_from


def get_json_from_file(file):
    with open(file) as f:
        return json.load(f)