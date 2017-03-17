import logging
import sys
import time

import psycopg2


DEFAULT_LEVEL = logging.INFO
DEFAULT_LEVEL_NAME = logging.getLevelName(DEFAULT_LEVEL)
DEFAULT_FORMAT = "%(asctime)s %(levelname)-8s %(name)s:%(lineno)d: %(message)s"
DEFAULT_FORMATTER = logging.Formatter(DEFAULT_FORMAT)

logger = logging.getLogger(__name__)


def console_handler():
    """Returns a console handler."""
    result = logging.StreamHandler(sys.stdout)
    result.setFormatter(DEFAULT_FORMATTER)
    return result


def setup_logging(level=DEFAULT_LEVEL, handler=None):
    """Configures a logger with given level and handler."""
    if handler is None:
        handler = console_handler()
        logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(level)


def get_connection(url, local_infile=True):
    """Returns an object used for interacting with a Postgres database
    Params:
        url: an instance of urllib.parse.ParseResult

    Returns:
        connection to a Postgres database
    """
    return psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )


def create_table(conn, tablename, column_definitions):
    """Creates a table in our database
    Params:
        conn: a connection to Postgres
        tablename: string for the table's name
        columns_definition: list of tables.ColumnDefinition objects
    """
    with conn.cursor() as cur:
        create = """CREATE TABLE IF NOT EXISTS {} ({})""".format(
            tablename, ','.join(map(str, column_definitions)))
        cur.execute(create)
    conn.commit()


def execute_query(conn, query, args=()):
    """Executes a SQL query
    Args:
        conn: a connection to Postgres
        query: query to execute
        args: optional dictionary of arguments to pass to the query
    """
    with conn.cursor() as cursor:
        logger.debug('Starting query %s, %s', query, args)
        start = time.time()
        cursor.execute(query, args)
        end = time.time()
        logger.debug('Query took %s seconds', end - start)
    conn.commit()


def load_data_from_file(conn, tablename, infile, null='NULL'):
    """Loads data from a CSV delimited file into a table
    Params:
        conn: a pymsql.Connection instance
        table: a tables.Table object
        infile: full-file path string containing data
        null: sentinel value for missing/NaN data.
    """
    with conn.cursor() as cur:
        with open(infile, 'r') as f:
            logger.info('Loading data from {}'.format(infile))
            start = time.time()
            query = """
                COPY {tablename} FROM STDIN
                WITH
                CSV
                NULL '{null}'
                HEADER;""".format(tablename=tablename, null=null)
            cur.copy_expert(sql=query, file=f)
            end = time.time()
            logger.info('Finished loading data. It took {} seconds'.format(end - start))


def recreate_table_from_file(conn, table, infile):
    """Drops a table and then repopulates using a data_oasis.table object.
    Params:
        conn: a pymsql.Connection instance
        table: a tables.Table object
        infile: full-file path string containing data
    """
    drop_table(conn, table.TABLENAME)
    create_table(conn, table.TABLENAME, table.COLUMNS)
    load_data_from_file(conn, table.TABLENAME, infile)


def truncate_table(conn, tablename):
    query = "TRUNCATE TABLE {tablename};".format(tablename=tablename)
    execute_query(conn, query)


def drop_table(conn, tablename):
    query = "DROP TABLE IF EXISTS {tablename};".format(tablename=tablename)
    execute_query(conn, query)


def create_index(conn, tablename, idxname, columnname):
    query = "CREATE INDEX {idxname} ON {tablename} ({columnname});".format(
        idxname=idxname,
        tablename=tablename,
        columnname=columnname,
    )
    execute_query(conn, query)
