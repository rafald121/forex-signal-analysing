import logging
from urllib.request import urlopen
import urllib.request

logger = logging.getLogger('scrapper_utils')

def get_html_source(url):
    try:
        html = urlopen(url)
        html_content = html.read()
        html_decoded = html_content.decode("utf-8")
        return html_decoded
    except Exception as e:
        logger.error("error while fetching coinmarketcap. error: {}".format(e))
        return None


def get_response_xhr(url):
    try:
        request = urllib.request.Request(
            url,
            headers={'User-Agent' : "Magic Browser"}
        )
        content = urllib.request.urlopen(request).read()
        decoded = content.decode('utf-8')
        return decoded
    except Exception as e:
        logger.error('Error occured while trying to fetch content of XHR request of URL: {}. '
                     'Error message: {}'.format(url, e))
