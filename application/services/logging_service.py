import sys
import os
import logging
import ast
from services import config_service


CONFIG = config_service.get_config()


def init_logging():
    root_logger = logging.getLogger()

    log_format = "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
    log_formatter = logging.Formatter(log_format)

    log_level = get_log_level()
    root_logger.setLevel(log_level)
    logging.basicConfig(level=log_level, format=log_format)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create new handler to log to stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(log_formatter)
    root_logger.addHandler(stream_handler)

    # Create new handler to log to a file
    file_handler = logging.FileHandler(get_log_file_path())
    file_handler.setLevel(log_level)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)


def display_current_parameter_set(dycast_parameters):
    logging.info("")
    logging.info("Parameter set:")
    logging.info("Spatial domain: %s meter", dycast_parameters.spatial_domain)
    logging.info("Temporal domain: %s days", dycast_parameters.temporal_domain)
    logging.info("Close in space: %s meter", dycast_parameters.close_in_space)
    logging.info("Close in time: %s days", dycast_parameters.close_in_time)
    logging.info("")
    logging.info("Spatial extent:")
    logging.info("extent_min_x: %s", dycast_parameters.extent_min_x)
    logging.info("extent_min_y: %s", dycast_parameters.extent_min_y)
    logging.info("extent_max_x: %s", dycast_parameters.extent_max_x)
    logging.info("extent_max_y: %s", dycast_parameters.extent_max_y)
    logging.info("SRID of extent coordinates: %s", dycast_parameters.srid_of_extent)
    logging.info("")
    logging.info("Time span:")
    logging.info("Start date: %s", dycast_parameters.startdate)
    logging.info("End date: %s", dycast_parameters.enddate)
    logging.info("")



# 'Private' methods

def get_log_level():
    debug_setting = config_service.get_env_variable("DEBUG")
    if debug_setting:
        if ast.literal_eval(debug_setting):
            return logging.DEBUG

    return logging.INFO

def get_log_file_path():
    log_dir = CONFIG.get("system", "logfile")
    root_dir = config_service.get_application_directory()
    return os.path.join(root_dir, log_dir)
