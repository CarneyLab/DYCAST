import unittest
import os
from application.services import export_service as export_service_module
from application.services import database_service
from application.services import conversion_service
from application.tests import test_helper_functions
from application.models.classes import dycast_parameters
from application.models.enums import enums


class TestImportServiceFunctions(unittest.TestCase):

    def test_load_cases(self):
        dycast = dycast_parameters.DycastParameters()

        dycast.srid_of_cases = '3857'
        dycast.files_to_import = test_helper_functions.get_test_cases_import_files_latlong()

        dycast.startdate = conversion_service.get_date_object_from_string('2016-03-30')
        dycast.enddate = conversion_service.get_date_object_from_string('2016-04-10')
        dycast.export_prefix = 'test_export_'
        dycast.export_format = 'tsv'

        dycast.export_directory = test_helper_functions.get_test_data_export_directory()

        test_helper_functions.insert_test_risk()

        export_service = export_service_module.ExportService()
        exported_file_path = export_service.export_risk(dycast)

        exported_file_size = os.stat(exported_file_path).st_size
        os.remove(exported_file_path)

        self.assertGreater(exported_file_size, 0)

        
