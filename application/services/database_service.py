import os
import logging

import psycopg2
from alembic import command
from alembic.config import Config
from alembic.util.exc import CommandError
from sqlalchemy import create_engine, func
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database, drop_database

from services import config_service

CONFIG = config_service.get_config()
DeclarativeBase = declarative_base()


# Helper functions common

def get_db_instance_name():
    return CONFIG.get("database", "db_instance_name")

def get_db_user():
    return CONFIG.get("database", "user")


def get_db_password():
    return CONFIG.get("database", "password")


def get_db_host():
    return CONFIG.get("database", "host")


def get_db_port():
    return CONFIG.get("database", "port")



# Helper functions SQLAlchemy

def db_connect():
    """
    Connect to database.
    Returns sqlalchemy engine instance
    """
    return create_engine(get_sqlalchemy_conn_string())


def execute_sql_command(sql_command, engine):
    engine.execute(sql_command)


def get_sqlalchemy_conn_string():   
    return URL(drivername="postgres",
               host=get_db_host(),
               port=get_db_port(),
               username=get_db_user(),
               password=get_db_password(),
               database=get_db_instance_name())


def get_sqlalchemy_session():
    engine = db_connect()
    Session = sessionmaker(bind=engine)
    return Session()



# Helper functions Psycopg2

def init_psycopg_db():
    dsn = get_dsn()
    try:
        conn = psycopg2.connect(dsn)
    except Exception:
        logging.exception("Unable to connect to database")
        raise
    cur = conn.cursor()
    return cur, conn


def get_dsn():
    db_instance_name = get_db_instance_name()
    user = get_db_user()
    password = get_db_password()
    host = get_db_host()
    port = get_db_port()

    return "dbname='" + db_instance_name + "' user='" + user + \
        "' password='" + password + "' host='" + host + \
        "' port='" + port + "'"



# Init helper functions

def create_postgis_extension(engine):
    logging.info("Creating PostGIS extension...")
    sql_command = "CREATE EXTENSION postgis;"
    execute_sql_command(sql_command, engine)

def import_monte_carlo(monte_carlo_file):
    logging.info("Importing Monte Carlo file: %s", monte_carlo_file)
    cur, conn = init_psycopg_db()

    monte_carlo_file = parse_monte_carlo_path(monte_carlo_file)
    input_file = open(monte_carlo_file, 'r')
    
    try:
        cur.copy_from(input_file, 'distribution_margins', sep=',')
        conn.commit()
    finally:
        input_file.close()
        conn.close()

def parse_monte_carlo_path(monte_carlo_file):
    if not os.path.isabs(monte_carlo_file):
        init_directory = config_service.get_init_directory()
        monte_carlo_file = os.path.join(init_directory, monte_carlo_file)
    return monte_carlo_file


# Migrations

def run_migrations(revision='head'):
    logging.info("Running database migrations...")
    alembic_config_path = config_service.get_alembic_config_path()
    alembic_config = Config(alembic_config_path)
    try:
        command.upgrade(config=alembic_config, revision=revision)
    except CommandError as ex:
        logging.error("Could not run migrations: [{0}]".format(ex))



# Init command

def init_db(monte_carlo_file, force=False):
    engine = db_connect()
    db_url = engine.url

    try:
        if force:
            if database_exists(db_url):
                logging.info("Dropping existing database in 5 seconds...")
                time.sleep(5)
                drop_database(db_url)
                logging.info("Dropped.")

        if not database_exists(db_url):
            logging.info("Creating database...")
            create_database(db_url)
            create_postgis_extension(engine)
            run_migrations()
            import_monte_carlo(monte_carlo_file)
        else:
            logging.info("Database already exists, skipping database initialization...")
    finally:
        engine.dispose()


# Query helper functions

def get_count_for_query(query):
    count_query = query.statement.with_only_columns([func.count()]).order_by(None)
    return query.session.execute(count_query).scalar()
