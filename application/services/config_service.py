import sys
import os
import configparser
import logging

CONFIG = configparser.SafeConfigParser(os.environ)


def get_env_variable(var_name):
    try:
        return os.environ[var_name]
    except KeyError:
        return None


def init_config(config_file_path=None):
    if CONFIG.sections().__len__() == 0:
        try:
            if not config_file_path or config_file_path == "":
                config_file_path = get_default_config_file_path()
            logging.debug("Reading config file: %s", config_file_path)
            CONFIG.read(config_file_path)
            logging.debug("Done reading config file.")
        except Exception:
            logging.exception("Could not read config file: %s", config_file_path)
            sys.exit()
    else:
        logging.debug("Config already initialized, skipping")


def get_config():
    return CONFIG


def get_current_directory():
    return os.path.dirname(os.path.realpath(__file__))

def get_root_directory():
    return os.path.join(get_current_directory(), '..', '..')

def get_application_directory():
    return os.path.join(get_current_directory(), '..')

def get_import_directory():
    import_directory = CONFIG.get("system", "import_directory")
    root_directory = get_root_directory()
    return os.path.join(root_directory, import_directory)

def get_export_directory():
    export_directory = CONFIG.get("system", "export_directory")
    root_directory = get_root_directory()
    return os.path.join(root_directory, export_directory)

def get_default_config_file_path():
    config_file_name = 'dycast.config'
    application_directory = get_application_directory()
    return os.path.join(application_directory, config_file_name)

def get_alembic_config_path():
    config_file_name = 'alembic.ini'
    application_directory = get_application_directory()
    return os.path.join(application_directory, 'init', 'migrations', config_file_name)
