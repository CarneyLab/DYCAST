import logging
import sys

from sqlalchemy import exists
from sqlalchemy.exc import SQLAlchemyError

from services import config_service
from services import file_service
from services import database_service
from services import geography_service

from models.models import Case
from models.enums import enums


CONFIG = config_service.get_config()


class ImportService(object):

    def __init__(self, **kwargs):
        self.system_coordinate_system = CONFIG.get("dycast", "system_coordinate_system")


    def load_case_files(self, dycast_parameters):
        logging.info("Loading files: %s", dycast_parameters.files_to_import)

        for filepath in dycast_parameters.files_to_import:
            try:
                logging.info("Loading file: %s", filepath)
                self.load_case_file(dycast_parameters, filepath)
            except Exception:
                logging.exception("Could not load file: %s", filepath)
                raise

    def load_case_file(self, dycast_parameters, filename):
        session = database_service.get_sqlalchemy_session()

        lines_read = 0
        lines_processed = 0
        lines_loaded = 0
        lines_skipped = 0
        location_type = ""

        try:
            input_file = file_service.read_file(filename)
        except Exception:
            logging.exception("Could not read file: %s", filename)
            raise

        for line_number, line in enumerate(input_file):
            line = remove_trailing_newline(line)
            if line_number == 0:
                header_count = line.count("\t") + 1
                if header_count == 4:
                    location_type = enums.Location_type.LAT_LONG
                elif header_count == 3:
                    location_type = enums.Location_type.GEOMETRY
                else:
                    raise ValueError("Incorrect column count: {header_count}, exiting...".format(header_count=header_count))
                logging.info("Loading cases as location type: %s", enums.Location_type(location_type).name)
            else:
                lines_read += 1
                result = 0
                try:
                    result = self.load_case(session, dycast_parameters, line, location_type)
                except Exception:
                    raise

                # If result is a case ID or -1 (meaning duplicate) then:
                lines_processed += 1
                if result == -1:
                    lines_skipped += 1
                else:
                    lines_loaded += 1

        try:
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logging.exception("Couldn't insert cases")
            logging.exception(e)
            raise
        finally:
            session.close()

        logging.info("Case load complete: %s", filename)
        logging.info("Processed %s of %s lines, %s loaded, %s duplicate IDs skipped",
                     lines_processed, lines_read, lines_loaded, lines_skipped)
        return lines_read, lines_processed, lines_loaded, lines_skipped


    def load_case(self, session, dycast_parameters, line, location_type):

        if location_type not in (enums.Location_type.LAT_LONG, enums.Location_type.GEOMETRY):
            raise ValueError("Wrong value for 'location_type', exiting...")

        case = Case()

        if location_type == enums.Location_type.LAT_LONG:
            user_coordinate_system = dycast_parameters.srid_of_cases
            if user_coordinate_system is None:
                raise ValueError(
                    "Parameter 'user_coordinate_system' cannot be undefined when loading cases with lat/long locations")
            try:
                (case_id, report_date, lon, lat) = line.split("\t")
            except ValueError as e:
                fail_on_incorrect_count(location_type, line, e)

            point = geography_service.get_point_from_lat_long(lat, lon, user_coordinate_system)
            projected_point = geography_service.transform_point(point, self.system_coordinate_system)

            case = Case(id=case_id, report_date=report_date, location=projected_point)

        else:
            try:
                (case_id, report_date, geometry) = line.split("\t")
            except ValueError as e:
                fail_on_incorrect_count(location_type, line, e)

            case = Case(id=case_id, report_date=report_date, location=geometry)

        if not case_exists(session, case_id):
            session.add(case)
            session.flush()
            return 1
        else:
            logging.warning("Couldn't insert duplicate case key %s, skipping...", case_id)
            return -1




def fail_on_incorrect_count(location_type, line, exception):
    logging.error("Incorrect number of fields for 'location_type': %s",
                  enums.Location_type(location_type).name)
    logging.error(line.rstrip())
    raise exception

def remove_trailing_newline(line):
    return line.strip()

def case_exists(session, case_id):
    return session.query(exists().where(Case.id == case_id)).scalar()
