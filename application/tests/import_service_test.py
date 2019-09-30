import unittest

from sqlalchemy.exc import DataError

from services import import_service as import_service_module
from services import database_service
from tests import test_helper_functions

from models.models import Case
from models.classes import dycast_parameters
from models.enums import enums


class TestImportServiceFunctions(unittest.TestCase):

    def test_load_cases(self):
        import_service = import_service_module.ImportService()

        dycast_model = dycast_parameters.DycastParameters()

        dycast_model.srid_of_cases = '3857'
        dycast_model.files_to_import = test_helper_functions.get_test_cases_import_files_latlong()

        import_service.load_case_files(dycast_model)


    def test_load_case_correct(self):
        session = database_service.get_sqlalchemy_session()
        import_service = import_service_module.ImportService()

        dycast_model = dycast_parameters.DycastParameters()
        dycast_model.srid_of_cases = 3857

        line_correct = "99999\t03/09/16\t1832445.278\t2118527.399"
        location_type = enums.Location_type.LAT_LONG

        import_service.load_case(session, dycast_model, line_correct, location_type)
        session.commit()

        query = session.query(Case).filter(Case.id == '99999')
        count = database_service.get_count_for_query(query)

        self.assertEqual(count, 1)
        session.delete(query.first())
        session.commit()


    def test_load_case_data_error(self):
        session = database_service.get_sqlalchemy_session()
        import_service = import_service_module.ImportService()

        dycast_model = dycast_parameters.DycastParameters()
        dycast_model.srid_of_cases = 3857

        location_type = enums.Location_type.LAT_LONG
        line_incorrect_date = "9998\t30/09/16\t1832445.278\t2118527.399"

        with self.assertRaises(DataError):
            import_service.load_case(session, dycast_model, line_incorrect_date, location_type)
