import logging

def custom_excepthook(exctype, value, traceback):
    logging.error("An uncaught exception occurred:")
    logging.error("Type: %s", exctype)
    logging.error("Value: %s", value)
    logging.error("Traceback: %s", traceback)
