import datetime
import logging
import sys

import configargparse

from models.classes import dycast_parameters
from services import config_service
from services import conversion_service
from services import database_service
from services import debug_service
from services import logging_service

debug_service.enable_debugger()

CONFIG = config_service.get_config()


# Types
def valid_date(date_string):
    if date_string == "today":
        return conversion_service.get_date_object_from_string(datetime.date.today())
    try:
        return conversion_service.get_date_object_from_string(date_string)
    except ValueError as e:
        logging.exception("Invalid date format: %s", date_string)
        sys.exit(1)



# Parsers
def create_parser():
    # Common arguments for all subcommands
    common_parser = configargparse.ArgParser(add_help=False)

    common_parser.add('--config', '-c',
                      default="./dycast.config",
                      help="Override default config file")

    # Main parser that keeps all subcommand separate, while still using common arguments from the common_parser
    main_parser = configargparse.ArgParser(add_help=True)
    subparsers = main_parser.add_subparsers(
        title='Commands', help='Choose from the following commands:')

    # Load cases
    load_cases_parser = subparsers.add_parser('load_cases',
                                              parents=[common_parser],
                                              help='Loads cases into Dycast from a specified file',
                                              argument_default=configargparse.SUPPRESS)
    load_cases_parser.set_defaults(func=import_cases)

    # Generate risk
    generate_risk_parser = subparsers.add_parser('generate_risk',
                                                 parents=[common_parser],
                                                 help='Generates risk from the cases currently in the database',
                                                 argument_default=configargparse.SUPPRESS)
    generate_risk_parser.set_defaults(func=generate_risk)

    # Export cases
    export_risk_parser = subparsers.add_parser('export_risk',
                                               parents=[common_parser],
                                               help='Exports risk currently in the database to --export_directory',
                                               argument_default=configargparse.SUPPRESS)
    export_risk_parser.set_defaults(func=export_risk)

    # Run Dycast (run all steps)
    run_dycast_parser = subparsers.add_parser('run_dycast',
                                              parents=[common_parser],
                                              help='Loads any .tsv files in (--files | -f), generates risk and exports it to --export_directory',
                                              argument_default=configargparse.SUPPRESS)
    run_dycast_parser.set_defaults(func=run_dycast)

    # Init database
    setup_dycast_parser = subparsers.add_parser('setup_dycast',
                                              parents=[common_parser],
                                              help='Initialize database',
                                              argument_default=configargparse.SUPPRESS)
    setup_dycast_parser.set_defaults(func=setup_dycast)

    # Run database migrations
    run_migrations_parser = subparsers.add_parser('run_migrations',
                                              parents=[common_parser],
                                              help='Run database migrations',
                                              argument_default=configargparse.SUPPRESS)
    run_migrations_parser.set_defaults(func=run_migrations)

    ## Common arguments:
        # load_cases
        # run_dycast
    for subparser in [load_cases_parser, run_dycast_parser]:
        subparser.add('--files', '-f',
                      nargs='+',
                      env_var='FILES',
                      help='File path or paths (space separated) to load cases from. Supported format: .TSV')
        subparser.add('--import-directory',
                      env_var='IMPORT_DIRECTORY',
                      help='Override default set in dycast.config. Path to load cases from. If no (--files | -f) is specified, Dycast will look in this directory for .tsv files to load into the database')
        subparser.add('--srid-cases',
                      env_var='SRID_CASES',
                      help='The SRID (projection) of the cases you are loading. Only required if your cases are in lat/long, not when they are in PostGIS geometry format')


    ## Common arguments:
        # generate_risk
        # run_dycast
    for subparser in [generate_risk_parser, run_dycast_parser]:
        subparser.add('--extent-min-x',
                      env_var='EXTENT_MIN_X',
                      required=True,
                      type=float,
                      help='The minimum point on the X axis (north-west)')
        subparser.add('--extent-min-y',
                      env_var='EXTENT_MIN_Y',
                      required=True,
                      type=float,
                      help='The minimum point on the Y axis (north-west)')
        subparser.add('--extent-max-x',
                      env_var='EXTENT_MAX_X',
                      required=True,
                      type=float,
                      help='The maximum point on the X axis (south-east)')
        subparser.add('--extent-max-y',
                      env_var='EXTENT_MAX_Y',
                      required=True,
                      type=float,
                      help='The maximum point on the Y axis (south-east)')
        subparser.add('--srid-extent',
                      env_var='SRID_EXTENT',
                      required=True,
                      help='The SRID (projection) of the specified extent.')
        subparser.add('--spatial-domain',
                      env_var='SPATIAL_DOMAIN',
                      default='800',
                      type=int,
                      help='Spatial domain used in Dycast risk generation and statistical analysis')
        subparser.add('--temporal-domain',
                      env_var='TEMPORAL_DOMAIN',
                      default='28',
                      type=int,
                      help='Temporal domain used in Dycast risk generation and statistical analysis')
        subparser.add('--close-in-space',
                      env_var='CLOSE_SPACE',
                      default='200',
                      type=int,
                      help='The amount of meters between two cases that is considered "close in space" in Dycast risk generation and statistical analysis')
        subparser.add('--close-in-time',
                      env_var='CLOSE_TIME',
                      default='4',
                      type=int,
                      help='The amount of days between two cases that is considered "close in time" in Dycast risk generation and statistical analysis')
        subparser.add('--case-threshold',
                      env_var='CASE_THRESHOLD',
                      default='10',
                      type=int,
                      help='Spatial domain used in Dycast risk generation and statistical analysis')


    ## Common arguments:
        # export_risk
        # run_dycast
    for subparser in [export_risk_parser, run_dycast_parser]:
        subparser.add('--export-directory',
                      env_var='EXPORT_DIRECTORY',
                      help='Optional. Default is defined in dycast.config')
        subparser.add('--export-format',
                      env_var='EXPORT_FORMAT',
                      default='tsv',
                      help='Options: tsv | csv')
        subparser.add('--export-prefix',
                      env_var='EXPORT_PREFIX',
                      help='Set a prefix for the output file so that it is easy to recognize')


    ## Common arguments:
        # generate_risk
        # export_risk
        # run_dycast
    for subparser in [generate_risk_parser, export_risk_parser, run_dycast_parser]:
        subparser.add('--startdate', '-s',
                      env_var='START_DATE',
                      type=valid_date,
                      default='today',
                      help='Default: today. The start date from which to generate and/or export risk. Format: YYYY-MM-DD. Also accepts "today" as input')
        subparser.add('--enddate', '-e',
                      env_var='END_DATE',
                      type=valid_date,
                      help='Default: same as start date. The end date to which to generate and/or export risk. Format: YYYY-MM-DD')


    ## Init db arguments:
    setup_dycast_parser.add('--force-db-init',
                       action='store_true',
                       help='If this flag is provided: drops existing database')
    setup_dycast_parser.add('--monte-carlo-file',
                       env_var='MONTE_CARLO_FILE',
                       required=True,
                       help='File name without folder. File must be in `application/init` folder')


    ## Run migrations arguments:
    run_migrations_parser.add('--revision',
                              default='head',
                              help='Default: head (run all migrations that are not already applied)')


    return main_parser


##########################################################################
# Main functions:
##########################################################################

def run_dycast(**kwargs):
    import_cases(**kwargs)
    generate_risk(**kwargs)
    export_risk(**kwargs)


def import_cases(**kwargs):

    dycast = dycast_parameters.DycastParameters()

    dycast.srid_of_cases = kwargs.get('srid_cases')
    dycast.dead_birds_dir = kwargs.get('import_directory', config_service.get_import_directory())
    dycast.files_to_import = kwargs.get('files')

    dycast.import_cases()


def generate_risk(**kwargs):

    dycast = dycast_parameters.DycastParameters()

    dycast.spatial_domain = float(kwargs.get('spatial_domain'))
    dycast.temporal_domain = int(kwargs.get('temporal_domain'))
    dycast.close_in_space = float(kwargs.get('close_in_space'))
    dycast.close_in_time = int(kwargs.get('close_in_time'))
    dycast.case_threshold = int(kwargs.get('case_threshold'))

    dycast.startdate = kwargs.get('startdate', datetime.date.today())
    dycast.enddate = kwargs.get('enddate', dycast.startdate)
    dycast.extent_min_x = kwargs.get('extent_min_x')
    dycast.extent_min_y = kwargs.get('extent_min_y')
    dycast.extent_max_x = kwargs.get('extent_max_x')
    dycast.extent_max_y = kwargs.get('extent_max_y')
    dycast.srid_of_extent = kwargs.get('srid_extent')

    dycast.generate_risk()


def export_risk(**kwargs):

    dycast = dycast_parameters.DycastParameters()

    dycast.export_prefix = kwargs.get('export_prefix')
    dycast.export_format = kwargs.get('export_format')
    dycast.export_directory = kwargs.get('export_directory', config_service.get_export_directory())
    dycast.startdate = kwargs.get('startdate', datetime.date.today())
    dycast.enddate = kwargs.get('enddate', dycast.startdate)

    dycast.export_risk()


def listen_for_input(**kwargs):
    raise NotImplementedError


def setup_dycast(**kwargs):
    force = kwargs.get('force_db_init')
    monte_carlo_file = kwargs.get('monte_carlo_file')
    database_service.init_db(monte_carlo_file, force)


def run_migrations(**kwargs):
    revision = kwargs.get('revision')
    database_service.run_migrations(revision)


def main(raw_args=None):
    parser = create_parser()
    args = parser.parse_args(raw_args)

    dictionary_args = vars(args)

    config_service.init_config(dictionary_args.get('config'))
    logging_service.init_logging()

    if args.func:
        args.func(**dictionary_args)


if __name__ == '__main__':
    main()
