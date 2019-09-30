import unittest

from services import file_service
from tests import test_helper_functions

from models.classes import dycast_parameters


class TestFileServiceFunctions(unittest.TestCase):

    def test_read_file(self):
        dycast_model = dycast_parameters.DycastParameters()
        dycast_model.files_to_import = test_helper_functions.get_test_cases_import_files_latlong()

        file_service.read_file(dycast_model.files_to_import[0])

    def test_save_file(self):
        file_name = test_helper_functions.get_test_file_path()
        body = "This is a test file.\nThis file will be saved to disk."
        file_service.save_file(body, file_name)
        test_helper_functions.delete_test_file()
