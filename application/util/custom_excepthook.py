import logging

def custom_excepthook(exctype, value, tb):
    logging.error("An uncaught exception occurred:")
    logging.error("Type: {exctype}".format(exctype=exctype))
    logging.error("Value: {value}".format(value=value))
    logging.error("Traceback: {tb}".format(tb=tb))