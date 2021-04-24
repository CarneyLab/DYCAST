from models.models import DistributionMargin

class DistributionMarginService(object):

    def generate_distribution_margins(self):

        distribution_margins = [DistributionMargin(1,2,3,0.4,5,6), DistributionMargin(7,8,9,1.0,11,12)]

        return distribution_margins