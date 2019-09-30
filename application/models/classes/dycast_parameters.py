# Dycast functions

# dist_margs means "distribution marginals" and is the result of the
# monte carlo simulations.  See Theophilides et al. for more information

import logging

from services import import_service as import_service_module
from services import export_service as export_service_module
from services import risk_service as risk_service_module


class DycastParameters(object):

    def __init__(self, **kwargs):
        self.srid_of_cases = None
        self.dead_birds_dir = None
        self.files_to_import = None

        self.export_directory = None
        self.export_prefix = None
        self.export_format = None

        self.spatial_domain = None
        self.temporal_domain = None
        self.close_in_space = None
        self.close_in_time = None
        self.case_threshold = None

        self.startdate = None
        self.enddate = None

        self.extent_min_x = None
        self.extent_min_y = None
        self.extent_max_x = None
        self.extent_max_y = None
        self.srid_of_extent = None

        for (key, value) in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


    def import_cases(self):
        import_service = import_service_module.ImportService()
        if self.files_to_import:
            import_service.load_case_files(self)
        else:
            logging.info("Loading files from import path: %s",
                         self.dead_birds_dir)
            raise NotImplementedError

        logging.info("Done loading cases")

    def listen_for_files(self):
        raise NotImplementedError

    def export_risk(self):
        export_service = export_service_module.ExportService()
        export_service.export_risk(self)

    def generate_risk(self):
        risk_service = risk_service_module.RiskService(self)
        risk_service.generate_risk()
