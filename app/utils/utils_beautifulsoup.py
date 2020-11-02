from bs4 import BeautifulSoup
from app.utils import utils_scrapping

class UtilsBeautifulSoup:

    HTML_PARSER = 'html.parser'

    @classmethod
    def get_soup_from_source(cls, source):
        return BeautifulSoup(source, cls.HTML_PARSER)

    @classmethod
    def get_all_tags_from_source(cls, source, tag):
        soup = cls.get_soup_from_source(source)
        return soup(tag)

    @classmethod
    def get_all_tags_from_url(cls, url, tag):
        source = utils_scrapping.get_html_source(url)
        soup = cls.get_soup_from_source(source)
        return soup(tag)