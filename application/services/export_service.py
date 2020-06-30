import sys
import os
import logging
from time import strftime
from services import conversion_service
from services import config_service
from services import database_service
from services import file_service
from models.models import Risk


CONFIG = config_service.get_config()

class ExportService(object):
    
    def export_risk(self, dycast_parameters):

        session = database_service.get_sqlalchemy_session()

        startdate = dycast_parameters.startdate
        enddate = dycast_parameters.enddate
        export_directory = dycast_parameters.export_directory
        export_prefix = dycast_parameters.export_prefix
        export_format = dycast_parameters.export_format

        # Quick and dirty solution
        if export_format != "tsv" and export_format != "csv":
            logging.error("Incorrect export format: %s", export_format)
            return 1
        else:
            separator = self.get_separator(export_format)

        if export_directory is None:
            export_directory = CONFIG.get("export_directory")

        # dates are objects, not strings
        startdate_string = conversion_service.get_string_from_date_object(startdate)
        enddate_string = conversion_service.get_string_from_date_object(enddate)

        export_time = strftime("%Y-%m-%d__%H-%M-%S")
        filename = "exported_{0}__risk_{1}--{2}.{3}".format(export_time, startdate_string, enddate_string, export_format)
        if export_prefix:
            filename = export_prefix + filename
        filepath = os.path.join(export_directory, filename)


        logging.info("Exporting risk for: %s - %s", startdate_string, enddate_string)
        risk_query = self.get_risk_query(session, startdate, enddate)
        risk_count = database_service.get_count_for_query(risk_query)

        if risk_count == 0:
            logging.info("No risk found for the provided dates: %s - %s", startdate_string, enddate_string)
            return

        risk_collection = risk_query.all()

        table_content = file_service.TableContent()

        header = self.get_header_as_string(separator)
        table_content.set_header(header)

        body = self.get_rows_as_string(risk_collection, separator)
        table_content.set_body(body)


        file_service.save_file(table_content.get_content(), filepath)

        return filepath


    def get_risk_query(self, session, startdate, enddate):
        return session.query(Risk).filter(Risk.risk_date >= startdate,
                                          Risk.risk_date <= enddate)
      

    def get_header_as_string(self, separator):
        return "risk_date{0}lat{0}long{0}number_of_cases{0}close_pairs{0}close_time{0}close_space{0}p_value".format(separator)  


    def get_rows_as_string(self, risk_collection, separator):
        string = ""
        for risk in risk_collection:
            string = string + "{0}{8}{1}{8}{2}{8}{3}{8}{4}{8}{5}{8}{6}{8}{7}\n".format(risk.risk_date,
                                                                                       risk.lat,
                                                                                       risk.long,
                                                                                       risk.number_of_cases,
                                                                                       risk.close_pairs,
                                                                                       risk.close_time,
                                                                                       risk.close_space,
                                                                                       risk.cumulative_probability,
                                                                                       separator)
        return string

    def get_separator(self, file_format):
        if file_format == "tsv":
            return "\t"
        elif file_format == "csv":
            return ","
        else:
            raise ValueError("Invalid file format requested")
