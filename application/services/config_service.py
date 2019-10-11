import sys
import os
import configparser
import logging
import traceback

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
            elif not os.path.isabs(config_file_path):
                config_file_path = get_absolute_path_from_relative(config_file_path)
            
            message = "Reading config file: {config_file_path}".format(config_file_path=config_file_path)
            log_before_config_is_initialized(message)
            CONFIG.read(config_file_path)
            logging.debug("Done reading config file.")
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            log_before_config_is_initialized("Could not read config file:{config_file_path}".format(config_file_path=config_file_path))
            log_before_config_is_initialized(str(e))
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

def log_before_config_is_initialized(message):
    logging.debug(message)
    print(message)

def get_absolute_path_from_relative(relative_path):
    application_directory = get_application_directory()
    relative_dir = os.path.dirname(relative_path)
    relative_file = os.path.basename(relative_path)

    return os.path.join(application_directory, relative_dir, relative_file)