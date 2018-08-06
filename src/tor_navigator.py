import logging
from time import time
from enum import Enum
from urllib.parse import urljoin
from src import TorRequest
from arrow import Arrow


class _Formats(Enum):
    JSON = "json"
    XML = "xml"


class TorNavigator:
    """
    Check all paste sites compliant with "Sticky Notes" API. Look here for further details:
    https://sayakb.github.io/sticky-notes/pages/api/
    """
    relevant_paste_fields = ["timestamp", "title", "author", "data"]

    def __init__(self, api_format="json", timestamp=time(), paste_url="http://nzxj65x32vh2fkhk.onion/"):
        """
        Start a navigation session to a paste website
        :param str api_format: The format in which to get results from the website. Only "json" is currently supported.
        :param float timestamp: The timestamp from which to start recording the pastes
        :param str paste_url: The onion url of the paste site
        """
        self.__set_last_crawl(str(timestamp))
        self.last_crawl = property(fget=self.__get_last_crawl, fset=self.__set_last_crawl)
        enum_val = _Formats(api_format)
        if enum_val != _Formats.JSON:
            self._logger.warning(
                "It is strongly advised to use JSON format,"
                "as the paste site doesn't behave as expected in other formats.")
        self.__format = enum_val
        self.resource_url = "/".join(("api", _Formats(api_format).value))
        self.paste_url = paste_url
        self._tor_proxy_request = TorRequest()
        self._logger = logging.getLogger("Crawler")

    def _list_pastes(self, page_num):
        resp = self.__make_tor_request("list", str(page_num))
        page_list = self._parse_res_as_json(resp)["result"]["pastes"]
        self._logger.debug("Found %d pastes in page" % len(page_list))
        return page_list

    def _parse_res_as_json(self, resp):
        if self.__format == _Formats.JSON:
            return resp.json()
        elif self.__format == _Formats.XML:
            return self.__xml_to_json(resp)

    def __xml_to_json(self, resp):
        raise NotImplementedError

    def __make_tor_request(self, *args):
        resource_location = "/".join((self.resource_url, *args))
        full_url = urljoin(self.paste_url, resource_location)
        self._logger.debug("Asking TOR for URL %s" % full_url)
        return self._tor_proxy_request.get_with_refresh(full_url)

    def _get_paste(self, paste_id):
        paste_info = self.__make_tor_request("show", paste_id)
        res = self._parse_res_as_json(paste_info)["result"]
        self._logger.debug("Found new paste with paste_id %s" % paste_id)
        return res

    def __set_last_crawl(self, timestamp=str(time())):
        if type(timestamp) == Arrow:
            self.__last_crawl = timestamp
        else:
            self.__last_crawl = Arrow.fromtimestamp(str(timestamp)).replace(tzinfo="UTC")

    def __get_last_crawl(self):
        return self.__last_crawl

    def minimize_paste_fields(self, paste_jsons, *fields):
        """
        Keep only a few fields from the paste json
        :param list[dict[str]] paste_jsons:
        :param str fields: The name of the fields to keep
        :rtype: list[dict[str]]
        """
        if not fields:
            fields = TorNavigator.relevant_paste_fields
        self._logger.debug("Saving these fields: %s" % ", ".join(fields))
        minimized_jsons = []
        for paste_json in paste_jsons:
            minimized = {field: paste_json[field] for field in fields}
            minimized_jsons.append(minimized)
        return minimized_jsons

    def get_all_new_pastes(self):
        """
        Get all new pastes and set the last crawl time to now
        """
        page = 1
        oldest_timestamp = None
        new_pastes = []
        while oldest_timestamp is None or oldest_timestamp > self.__last_crawl:
            try:
                current_pastes = self._list_pastes(page)
            # Page does not exist
            except KeyError:
                break
            for paste_id in current_pastes:
                paste_json = self._get_paste(paste_id)
                if oldest_timestamp is None or \
                        Arrow.fromtimestamp(paste_json["timestamp"]).replace(tzinfo="UTC") < oldest_timestamp:
                    oldest_timestamp = Arrow.fromtimestamp(paste_json["timestamp"])
                if oldest_timestamp > self.__last_crawl:
                    new_pastes.append(paste_json)
            page += 1
        self._logger.info("Found %d new pastes since %s" % (len(new_pastes), self.__last_crawl.for_json()))
        self.__set_last_crawl()
        return new_pastes

    def new_pastes_to_write(self):
        new_pastes = self.get_all_new_pastes()
        minimized_pastes = self.minimize_paste_fields(new_pastes)
        return minimized_pastes

    def close_tor(self):
        self._tor_proxy_request.close()
