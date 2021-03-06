#!/usr/bin/env python3
import click
import logging
import os
import sys
from logging import handlers
from src import TinyWriter, TorNavigator
from time import sleep


def set_logger(disk_log_path=None, level=logging.INFO):
    logger = logging.getLogger("Crawler")
    fmt = "%(asctime)s %(levelname)s %(message)s"
    logging.basicConfig(handlers=(logging.StreamHandler(),), format=fmt, level=level)
    if disk_log_path is None:
        return
    rotate = handlers.RotatingFileHandler(disk_log_path, maxBytes=1024*1024)
    logger.addHandler(rotate)
    rotate.setFormatter(logging.Formatter(fmt))

    def new_excepthook(exctype, value, traceback):
        if exctype == KeyboardInterrupt:
            sys.__excepthook__(exctype, value, traceback)
            logger.error("Got a keyboard Interrupt, crawler stopping")
        logger.error("Unhandled exception:\n", exc_info=(exctype, value, traceback))
    sys.excepthook = new_excepthook


def crawl(tor_navigator, tiny_writer):
    """
    Do a single crawl to the paste sites.
    :param TorNavigator tor_navigator:
    :param TinyWriter tiny_writer:
    :return:
    """
    # Opens Tor implicitly
    new_pastes = tor_navigator.new_pastes_to_write()
    tor_navigator.close_tor()
    tiny_writer.write_json_entries(new_pastes)


@click.command()
@click.option("--log-path", type=click.STRING, default=None,
              help="Path to disk log, defaults to None and doesn't write to disk")
@click.option("--sample-wait", type=click.INT, default=4,
              help="Time in hours for difference between samples. Default is 4 hours")
@click.option("--debug", "-d", is_flag=True, help="Flag to enable debug logging")
@click.option("--single", "-s", is_flag=True, help="Whether to have a single crawl only")
@click.option("--timestamp", type=click.FLOAT, default=None,
              help="Override current timestamp with this option, given in seconds since epoch")
@click.option("--db-path", type=click.STRING, default="/tmp/db_loc/db.json")
def main(log_path, sample_wait, debug, single, timestamp, db_path):
    """
    Runner of the crawler.
    Pass log-path if you're interesting in keeping the path, or --sample-wait to change sampling rate
    """
    if debug:
        set_logger(log_path, logging.DEBUG)
    else:
        set_logger(log_path)
    if timestamp is not None:
        tor_navigator = TorNavigator(timestamp=timestamp)
    else:
        tor_navigator = TorNavigator()
    if os.path.exists(os.path.dirname(db_path)):
        tiny_writer = TinyWriter(db_location=db_path)
    else:
        tiny_writer = TinyWriter()
    logger = logging.getLogger("Crawler")
    logger.info("Starting crawler")
    if not single:
        while True:
            crawl(tor_navigator, tiny_writer)
            wait = sample_wait * 3600
            logger.info("Logger halting for %d seconds" % wait)
            sleep(wait)
    logger.info("Crawler leaving! Goodbye")


if __name__ == "__main__":
    main()
