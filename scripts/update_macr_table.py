import argparse
import glob
import logging
import os
import sys
import time
#import urllib.parse

from urlparse import urlparse
from data_oasis import tables
from data_oasis import utils


URL = urlparse.urlparse(os.environ['DATABASE_URL'])
logger = logging.getLogger()


def main():
    utils.setup_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument('inpath', help='GoogleDrive/Team Shared folder - California OpenJustice/Data/arrests/macr/transformed_table_format')
    args = parser.parse_args()
    with utils.get_connection(URL) as conn:
        table = tables.Macr()
        utils.load_data_from_file(conn, table.TABLENAME, args.inpath)


if __name__ == '__main__':
    sys.exit(main())
