import os
import logging
import time
from services import config_service


def enable_debugger():
    if config_service.get_env_variable("REMOTE_DEBUG") == "True":
        logging.info("REMOTE_DEBUG == True  --> Attaching to remote debugger...")
        import ptvsd
        
        try:
            ptvsd.enable_attach(address=('0.0.0.0', 3000))
            logging.info("Debugger is ready for attachment.")
        except:
            pass


        if config_service.get_env_variable("WAIT_FOR_ATTACH") == "True":
            logging.info("Waiting 10 seconds for debugger to attach...")
            time.sleep(10)
            if ptvsd.is_attached:
                logging.info("Attached debugger")
            else:
                logging.info("Not attached")
