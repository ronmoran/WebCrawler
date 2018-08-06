import platform
import logging
from arrow import Arrow
from os import environ
from os.path import join as join_path
from tinydb import TinyDB


def _determine_home_dir():
    system = platform.system()
    if "windows" in system.lower():
        return environ.get("USERPROFILE", "")
    else:
        return environ.get("HOME", "")


class TinyWriter:
    """
    Class to handle writing to a TinyDB database. Only supports JSON databases.
    """
    _unknown_authors = ["anonymous", "unknown", str(None).lower()]

    def __init__(self, timezone="UTC", strip=True, db_location=join_path(_determine_home_dir(), "db.json")):
        """
        :param str timezone: An ISO compliant timezone string. Defaults to UTC
        :param bool strip: Should strip strings from whitespaces before writing.
        :param str db_location: DB json path. Defaults to home directory with file name "db.json"
        """
        self.__db_location = db_location
        self.timezone = timezone
        self.should_strip = strip
        self.__db = TinyDB(db_location)
        self.__location = db_location
        self._logger = logging.getLogger("Crawler")
        self._logger.debug("Opened tinydb at %s" % db_location)

    def write_json_entries(self, jsons_to_write):
        """
        Write all given jsons to the initialized location
        :param list[dict[str]]] jsons_to_write: All jsons to insert into the database.
        All objects MUST be json serializalbe.
        """
        self._logger.info("Writing %d new JSONs" % len(jsons_to_write))
        for json_to_write in jsons_to_write:
            self._reformat_json(json_to_write)
        self.__db.insert_multiple(jsons_to_write)

    @property
    def db_location(self):
        return self.__db_location

    @db_location.setter
    def db_location(self, db_location):
        self._logger.debug("Changed path to %s" % db_location)
        self.__db = TinyDB(db_location)
        self.__location = db_location

    @classmethod
    def add_unknown_author(cls, author):
        """
        Add an author to list of unknown Authors. Will write to DB as "Unknown"
        :param str author: The Author's name
        """
        cls._unknown_authors.append(author.lower())

    def _reformat_json(self, dict_to_write):
        """
        In-place reformatting method for a consistent format between objects.
        :param dict dict_to_write: Formats all JSONs to write out
        :return: None, changes the JSON in place
        """
        self._logger.debug("Reformatting JSON: %s" % str(dict_to_write))
        for key in dict_to_write:
            if key == "timestamp":
                arrow_date = Arrow.fromtimestamp(dict_to_write[key]).replace(tzinfo=self.timezone)
                val = arrow_date.for_json()
            elif key == "author":
                author = dict_to_write[key]
                val = author if str(author).lower() not in TinyWriter._unknown_authors else "Unknown"
            else:
                val = str(dict_to_write[key]).strip() if self.should_strip and type(dict_to_write[key]) == str\
                    else dict_to_write[key]
            if type(val) == str:
                val.replace("\r\n", "\n")
            dict_to_write[key] = val
