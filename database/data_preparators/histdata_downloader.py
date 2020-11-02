import time
import os
import logging
import threading
from selenium.common.exceptions import WebDriverException
from selenium import webdriver

from app import constants
from app.utils import utils_file
from app.utils.utils_beautifulsoup import UtilsBeautifulSoup
from app.pairs import pairs_without_slash

logger_settings = {
    'level': 20,
    'format': '%(module)s %(message)s %(threadName)s',
}
logging.basicConfig(**logger_settings)
logger = logging.getLogger(__file__)

failed = []


class HistDataDownloader:
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

    def __init__(self, pairs):
        self.pairs = pairs

    @classmethod
    def get_available_pairs(cls):
        strong_tags_all = UtilsBeautifulSoup.get_all_tags_from_url(cls.URL_PAIRS_LIST, 'strong')
        return [tag.text.replace('/', '') for tag in strong_tags_all if '/' in tag.text]

    @classmethod
    def download_all_pairs_from_2017(cls, pairs):
        count = 1
        for pair in pairs:
            count += 1
            logger.info('downloading for pair: {}'.format(pair))
            threading.Thread(
                target=cls.download_pair_data_previous_year,
                name='{}/2017'.format(pair),
                args=(2017, pair, )
            ).start()
            cls.download_pair_data_current_year(pair)
            logger.info('sleep 80')
            time.sleep(60)
        logger.info('end of job')

    @classmethod
    def download_pairs_(cls, pairs):
        count = 1
        for pair in pairs:
            count += 1
            logger.info('downloading for pair: {}'.format(pair))
            cls.download_pair_data_current_year(pair)
            time.sleep(15)
        logger.info('end of job')

    @classmethod
    def download_pair_data_previous_year(cls, year, pair):
        logger.info('download for year: {} for pair: {}'.format(year, pair))
        url = cls.URL_DATA_DETAILS_PREVIOUS_YEARS.format(
            pair=pair,
            year=year
        )
        cls.download_data(url)

    @classmethod
    def download_pair_data_current_year(cls, pair):
        for month_nr in range(9, 13):
            time.sleep(5)
            threading.Thread(
                target=cls.download_pair_data_current_year_for_month,
                name="{}/2018/{}".format(pair, month_nr),
                args=(month_nr, pair, )
            ).start()

    @classmethod
    def download_pair_data_current_year_for_month(cls, month, pair):
        logger.info('downloading for 2018.{} for {}'.format(month, pair))
        year = 2018
        url = cls.URL_DATA_DETAILS_CURRENT_YEAR.format(
            pair=pair, year=year, month=month
        )
        cls.download_data(url)

    @classmethod
    def find_and_download_again_crdownloads(cls):
        files_crdownloads = cls.get_crdownloads_files()
        for file_name, length, url in files_crdownloads:
            logger.info('file_name: {}'.format(file_name))
            HistDataDownloader.download_data(url)
            os.remove(constants.PATH_DOWNLOADS + file_name)
            time.sleep(4)

    @classmethod
    def get_crdownloads_files(cls):
        """Move it somewhere"""
        from os import listdir
        from os.path import isfile, join
        mypath = '/Users/rafaldolega/Downloads'
        return [
            (f, len(f), cls.get_url_from_file_name(f))
            for f in listdir(mypath)
            if isfile(join(mypath, f)) and 'HISTDATA' in f and 'crdownload' in f
        ]

    @classmethod
    def get_url_from_file_name(cls, file_name):
        pair = file_name[16:22]
        year = file_name[25:29]
        month = file_name[29:31] if len(file_name) == 35 else ''
        if len(file_name) == 33:
            return cls.URL_DATA_DETAILS_PREVIOUS_YEARS.format(
                pair=pair, year=year
            )
        elif len(file_name) == 35:
            return cls.URL_DATA_DETAILS_CURRENT_YEAR.format(
                pair=pair, year=year, month=month
            )

    @classmethod
    def download_crdownloads(cls, list_of_files):
        for file_name in list_of_files:
            url = cls.get_url_from_file_name(file_name)
            cls.download_data(url)

    @classmethod
    def download_missing_files(cls):
        missing_urls = []
        file_names_all = cls.get_all_downloaded_hist_data_file_names()

        for pair in pairs_without_slash:
            file_names_for_pair = cls.get_file_names_for_pair_from_downloaded_files(
                pair, file_names_all
            )
            missing_urls = missing_urls + cls.get_missing_urls_for_pair(pair, file_names_for_pair)
        for nr, url in enumerate(missing_urls):
            logger.info('downloading nr.{} url: {}'.format(nr, url))
            cls.download_data(url)
            time.sleep(10)

    @classmethod
    def get_file_names_for_pair_from_downloaded_files(cls, pair, file_names):
        return [f_name for f_name in file_names if pair in f_name]

    @classmethod
    def get_all_downloaded_hist_data_file_names(cls):
        from os import listdir
        from os.path import isfile, join
        mypath = '/Users/rafaldolega/Downloads'
        return [
            f for f in listdir(mypath)
            if isfile(join(mypath, f))
               and 'HISTDATA' in f
               and not utils_file.is_file_older_than_days(join(mypath, f), 3)
        ]

    @classmethod
    def get_missing_urls_for_pair(cls, pair, file_names_for_pair):
        condition_filenames = [cls.FILE_NAME_PREVIOUS_YEAR.format(pair=pair)] + \
                              [
                                cls.FILE_NAME_CURRENT_YEAR.format(pair=pair, month=month_nr)
                                for month_nr in range(1, 10)
                              ]
        missing_url = []
        for file_name in condition_filenames:
            if file_name not in file_names_for_pair:
                missing_url.append(cls.get_url_from_file_name(file_name))
        return missing_url

    @classmethod
    def download_data(cls, url):
        driver = webdriver.Chrome()
        driver.get(url)
        try:
            driver.execute_script(cls.CLICK_SCRIPT)
        except WebDriverException:
            logger.error("some error occured while executing click script")

    @classmethod
    def is_pair_has_complete_dataset(cls, pair):
        pass

    @classmethod
    def download_all_data(cls):
        pass

    @classmethod
    def download_pair_data(cls, from_year, to_year):
        pass

    @classmethod
    def download_current_year_for_month(cls):
        pass

