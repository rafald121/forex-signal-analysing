import os
import logging
from app import constants
from database.data_preparators.histdata_downloader import HistDataDownloader
from app.pairs import pairs_without_slash
from app.utils import utils_file, _print, utils_csv

logger = logging.getLogger(__file__)


class GroupFile:

    def __init__(self):
        self.path_downloads = constants.PATH_DOWNLOADS
        self.path_target_csv_file = constants.PATH_HISTORICAL_PRICES_ABSOLUTE

    def create_directories_for_pairs(self, pairs):
        for pair in pairs:
            path = f"{self.path_target_csv_file}/{pair}"
            utils_file.create_directory(path)

    def sort_file_into_directories(self, pairs):
        file_names = HistDataDownloader.get_all_downloaded_hist_data_file_names()
        for file_name in file_names:
            pair_of_file_name = [pair for pair in pairs if pair in file_name][0]

            path_source = f"{self.path_downloads}/{file_name}"
            path_target = f"{self.path_target_csv_file}/{pair_of_file_name}/{file_name}"

            utils_file.copy_file(path_source, path_target)
            if not utils_file.is_file_exist(path_target):
                logger.warning("Target file: {} doesn't exist".format(path_target))
        logging.info('Successfully copied ')

    def unzip_all_files(self):
        directories = utils_file.get_all_directories_of_directory(
            self.path_target_csv_file, without_first=True
        )
        for dir in directories:
            dir_files = utils_file.get_files_for_directory(dir)
            for file in dir_files:
                file_path = "{}/{}".format(dir,file)
                utils_file.unzipfile(file_path, dir)
        _print(directories)

    def validate_unziping(self):
        directories = utils_file.get_all_directories_of_directory(
            self.path_target_csv_file, without_first=True
        )
        for nr, dir in enumerate(directories):
            dir_files = utils_file.get_files_for_directory(dir)
            logger.info("{} | For directory: {} amount of files: {}. Is merged in file?: {}".format(
                nr,
                dir.rsplit('/', 1)[1],
                len(dir_files),
                'merged.csv' in dir_files
            ))

    def merge_all_csv_files(self):
        directories = utils_file.get_all_directories_of_directory(
            self.path_target_csv_file, without_first=True
        )
        for nr, dir in enumerate(directories):
            logging.info("|{}| merging in dir: {}".format(nr+1, dir))
            dir_files_csv = sorted(["{}/{}".format(dir, file)
                                    for file in utils_file.get_files_for_directory(dir)
                                    if file.rsplit('.', 1)[-1]=='csv'])
            target_dir = "{}/{}".format(dir, "merged.csv")
            if not 'merged.csv' in dir_files_csv:
                utils_csv.merge_files_into_one(dir_files_csv, target_dir)
            else:
                logger.warning('You have been trying to merge .csv in directory that'
                               'merged.csv already exists and this leads to endless loop'
                               'and disk overfill')

    def check_if_not_merged_files(self):
        directories = utils_file.get_all_directories_of_directory(
            self.path_target_csv_file+'/', without_first=True
        )
        for nr, dir in enumerate(directories):
            files = utils_file.get_files_for_directory(dir)
            logging.info("{}, merged.csv in {} = {}".format(nr, dir, 'merged.csv' in files))
