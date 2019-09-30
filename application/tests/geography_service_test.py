import unittest

from services import geography_service
from models.classes import dycast_parameters
from tests import test_helper_functions


class TestGeographyServiceFunctions(unittest.TestCase):

    def test_generate_grid(self):
        dycast_paramaters = dycast_parameters.DycastParameters()

        dycast_paramaters.srid_of_extent = "29193"
        dycast_paramaters.extent_min_x = 197457.283284349
        dycast_paramaters.extent_min_y = 7639474.3256114
        dycast_paramaters.extent_max_x = 198056.722079
        dycast_paramaters.extent_max_y = 7639344.265401

        gridpoints = geography_service.generate_grid(dycast_paramaters)
        self.assertIsNotNone(gridpoints)
        self.assertGreaterEqual(len(gridpoints), 1)
