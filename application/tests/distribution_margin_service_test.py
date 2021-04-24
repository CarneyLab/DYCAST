import unittest
from services.distribution_margin_service import DistributionMarginService

class TestDistributionMarginService(unittest.TestCase):

    def test_generate_distribution_margins(self):
        # Arrange
        distribution_margin_service = DistributionMarginService()

        # Act
        distribution_margins = distribution_margin_service.generate_distribution_margins()

        # Assert
        self.assertEqual(len(distribution_margins), 2)

        first_margin = distribution_margins[0]
        self.assertGreater(first_margin.cumulative_probability, 0)

        second_margin = distribution_margins[1]
        self.assertGreater(second_margin.cumulative_probability, 0)
