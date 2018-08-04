from time import time
from enum import Enum
from urllib.parse import urljoin
from warnings import warn
from src import TorRequest
from arrow import Arrow


class _Formats(Enum):
    JSON = "json"
    XML = "xml"


class TorNavigator:
    __relevant_paste_fields = ["timestamp", "title", "author", "data"]

    def __init__(self, api_format="json"):
        self.__set_last_crawl("12336534")
        self.last_crawl = property(self.__get_last_crawl, self.__set_last_crawl)
        enum_val = _Formats(api_format)
        if enum_val != _Formats.JSON:
            warn("It is strongly advised to use JSON format, "
                 "as the paste site doesn't behave as expected in other formats.")
        self.__format = enum_val
        self.resource_url = "/".join(("api", _Formats(api_format).value))
        self.paste_url = "http://nzxj65x32vh2fkhk.onion/"
        self.tor_proxy_request = TorRequest()

    def _list_pastes(self, page_num):
        resp = self.__make_tor_request("list", str(page_num))
        return self.parse_res_as_json(resp)["result"]["pastes"]

    def parse_res_as_json(self, resp):
        if self.__format == _Formats.JSON:
            return resp.json()
        elif self.__format == _Formats.XML:
            return self.__xml_to_json(resp)

    def __xml_to_json(self, resp):
        raise NotImplementedError

    def __make_tor_request(self, *args):
        resource_location = "/".join((self.resource_url, *args))
        full_url = urljoin(self.paste_url, resource_location)
        return self.tor_proxy_request.get_with_refresh(full_url)

    def _get_paste(self, paste_id):
        paste_info = self.__make_tor_request("show", paste_id)
        return self.parse_res_as_json(paste_info)["result"]

    def __set_last_crawl(self, timestamp=str(time())):
        if type(timestamp) == Arrow:
            self.__last_crawl = timestamp
        else:
            self.__last_crawl = Arrow.fromtimestamp(str(timestamp))

    def __get_last_crawl(self):
        return self.__last_crawl

    @classmethod
    def minimize_paste_fields(cls, paste_jsons, *fields):
        if not fields:
            fields = cls.__relevant_paste_fields
        minimized_jsons = []
        for paste_json in paste_jsons:
            minimized = {field: paste_json["field"] for field in fields}
            minimized_jsons.append(minimized)
        return minimized_jsons

    def get_all_new_pastes(self):
        """
        Get all new pastes and set the last crawl time to now
        """
        counter = 1
        oldest_timestamp = None
        new_pastes = []
        while oldest_timestamp is None or oldest_timestamp > self.__last_crawl:
            current_pastes = self._list_pastes(counter)
            for paste_id in current_pastes:
                paste_json = self._get_paste(paste_id)
                if oldest_timestamp is None or Arrow.fromtimestamp(paste_json["timestamp"]) < oldest_timestamp:
                    oldest_timestamp = Arrow.fromtimestamp(paste_json["timestamp"])
                if oldest_timestamp > self.__last_crawl:
                    new_pastes.append(paste_json)
            counter += 1
        self.__set_last_crawl()
        return new_pastes

    def new_pastes_to_write(self):
        new_pastes = self.get_all_new_pastes()
        minimized_pastes = self.minimize_paste_fields(new_pastes)
        return minimized_pastes
