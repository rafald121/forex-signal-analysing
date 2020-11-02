from tqdm import tqdm
import logging
import threading
import time
from selenium.common.exceptions import WebDriverException
from selenium import webdriver

from app import constants
from app.utils.utils_file import get_month_from_filename, get_pair_from_filename, is_file_exist, \
    build_file_name
from database.data_preparators.histdata_grouping import GroupFile

logger = logging.getLogger(__file__)


class DataDownloaderManager:
    """
    WE NOT SUPPORT DOWNLOADING DATA BETWEEN YEARS SO YOU HAVE TO DOWNLOAD DATA SEPARATELY
    FOR EACH YEAR
    """
    WAIT_BETWEEN_DOWNLOAD = 6
    URL_LIST = 'http://www.histdata.com/download-free-forex-data/?/ascii/1-minute-bar-quotes'
    URL_PAIRS_LIST = 'http://www.histdata.com/download-free-forex-data/?/metatrader/1-minute-bar-quotes'
    A_TAG_CONTAIN_STRING_CONDITION = '/download-free-forex-historical-data/?/metatrader/1-minute-bar-quotes/'
    URL_DATA_DETAILS_PREVIOUS_YEARS = 'http://www.histdata.com/download-free-forex-historical-data/?/metatrader/' \
                                      '1-minute-bar-quotes/{pair}/{year}'
    URL_DATA_DETAILS_CURRENT_YEAR = 'http://www.histdata.com/download-free-forex-historical-data/?/metatrader/' \
                                    '1-minute-bar-quotes/{pair}/{year}/{month}'

    FILE_NAME_PREVIOUS_YEAR = 'HISTDATA_COM_MT_{pair}_M12017.zip'
    FILE_NAME_CURRENT_YEAR = 'HISTDATA_COM_MT_{pair}_M120180{month}.zip'

    CLICK_SCRIPT = 'document.getElementById(\'a_file\').click()'
    TYPE_TICK = ''
    TYPE_CANDLE = ''

    def __init__(self, pairs, year, month_from, month_to,
                 download=False, group=False, fillup=False):
        if self.is_params_valid(month_from, month_to):
            self.pairs = pairs
            self.year = year
            self.month_from = month_from
            self.month_to = month_to
            if download:
                logger.info(f'Start downloading for pairs: {self.pairs}. for year={year}'
                            f'from month={month_from} - to month={month_to}')
                counter_of_attempted_downloading_parts = 0
                while self.get_pairs_that_are_missing():
                    self.download_all_for_instance()
                    logger.info(f'#{counter_of_attempted_downloading_parts}| '
                                f'missing pair amount: {self.get_pairs_that_are_missing()}. '
                                f'Download it again...')
                # self.download_missing(missing_pair_amount)
                # missing_pair_amount = self.get_pairs_that_are_missing()
            if group:
                """
                It extract files and created merged file from given pair and period. 
                Default source file is: ~/Downloads
                Default target file is current repository (constants)
                """
                from database.data_preparators.histdata_grouping import GroupFile

                logger.info("GroupFile().create_directories_for_pairs(self.pairs)")
                GroupFile().create_directories_for_pairs(self.pairs)

                logger.info("GroupFile().sort_file_into_directories(self.pairs)")
                GroupFile().sort_file_into_directories(self.pairs)

                logger.info("GroupFile().unzip_all_files()")
                GroupFile().unzip_all_files()

                logger.info("GroupFile().validate_unziping()")
                GroupFile().validate_unziping()

                logger.info("GroupFile().merge_all_csv_files()")
                GroupFile().merge_all_csv_files()

                logger.info("Ready to save to db")
            if fillup:
                from database.data_preparators.fillup_db import HistDataDbFill

                HistDataDbFill().add_all_data_to_db_from_path(
                    constants.DOCKER_CONTAINER_HIST_DATA_DIRECTORY_PATH
                )
        else:
            logger.error(f'invalid params')

    def download_all_for_instance(self):
        for pair in tqdm(self.pairs):
            for month in range(self.month_from, self.month_to):
                filename = build_file_name(pair, self.year, month)
                path = f"{constants.PATH_DOWNLOADS}/{filename}"
                if not is_file_exist(path):
                    self.download_pair_data(pair, self.year, month)
                    time.sleep(self.WAIT_BETWEEN_DOWNLOAD)

    def download_missing(self, missing_pair_amount):
        missing = []
        for pair, value in missing_pair_amount.items():
            pair_files_months = [
                int(get_month_from_filename(p))
                for p in self.get_already_downloaded_data()
                if get_pair_from_filename(p) == pair
            ]
            for month in range(self.month_from, self.month_to):
                if month not in pair_files_months:
                    missing.append((pair, month))

        for item in missing:
            self.download_pair_data(item[0], self.year, item[1])
            time.sleep(self.WAIT_BETWEEN_DOWNLOAD)

    def get_pairs_that_are_missing(self):
        month_range = self.month_to - self.month_from
        downloaded_files = self.get_already_downloaded_data()
        d = {}
        for pair in self.pairs:
            d[pair] = month_range

        for file in downloaded_files:
            pair = get_pair_from_filename(file)
            d[pair] -= 1

        return {key: val for key, val in d.items() if val > 0}

    @classmethod
    def download_pair_data(cls, pair, year, month):
        url = cls.URL_DATA_DETAILS_CURRENT_YEAR.format(
            pair=pair, year=year, month=month
        )
        cls.download_data(url)

    def is_params_valid(self, mfrom, mto):
        return 0 < mfrom <= 13 and 0 < mto <= 13 and mfrom < mto

    @classmethod
    def download_data(cls, url):
        driver = webdriver.Chrome()
        driver.get(url)
        try:
            driver.execute_script(cls.CLICK_SCRIPT)
        except WebDriverException:
            logger.error("some error occured while executing click script")


    @staticmethod
    def get_already_downloaded_data():
        from os import listdir
        from os.path import isfile, join
        mypath = '/Users/rafaldolega/Downloads'
        return [
            f for f in listdir(mypath)
            if isfile(join(mypath, f)) and 'HISTDATA_COM_MT' in f
        ]


qs = ['GBPUSD', 'USDCAD', 'USDJPY', 'EURCAD', 'EURUSD', 'XAUUSD', 'CADJPY', 'GBPJPY', 'EURJPY',
      'EURAUD', 'EURCHF', 'EURNZD', 'GBPNZD', 'AUDNZD', 'CHFJPY', 'AUDUSD', 'AUDCAD', 'NZDJPY',
      'XAGUSD', 'NZDCAD', 'EURGBP', 'GBPCHF', 'AUDCHF', 'AUDJPY', 'NZDUSD', 'GBPAUD', 'USDCHF',
      'CADCHF', 'GBPCAD', 'NZDCHF', 'USDTRY', 'USDZAR', 'EURTRY', 'USDMXN', 'USDPLN', 'EURSEK',
      'EURHUF', 'USDHUF', 'SGDJPY', 'EURNOK', 'EURPLN', 'USDSGD', 'USDSEK', 'USDNOK']

DataDownloaderManager(qs, 2018, 1, 13, download=False, group=False, fillup=True)
