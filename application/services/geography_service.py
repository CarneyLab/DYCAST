import logging
import shapely.geometry
import pyproj

from geoalchemy2.functions import ST_Transform
from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import to_shape

from services import config_service


CONFIG = config_service.get_config()

 

def get_point_from_lat_long(lat, lon, projection):
    return WKTElement("POINT({0} {1})".format(lon, lat), srid=projection)


def get_shape_from_literal_wkt(wkt):
    return shapely.wkt.loads(wkt)


def get_wktelement_from_wkt(wkt):
    return WKTElement(wkt, srid=CONFIG.get("dycast", "system_coordinate_system"))


def get_shape_from_sqlalch_element(element):
    return to_shape(element)


def transform_point(point, target_projection):
    return ST_Transform(point, int(target_projection))


def generate_grid(dycast_parameters):
    '''
    Returns a raster grid with points in the coordinate system as
    specified in global setting 'system_coordinate_system'
    '''

    srid_of_extent = dycast_parameters.srid_of_extent
    extent_min_x = dycast_parameters.extent_min_x
    extent_min_y = dycast_parameters.extent_min_y
    extent_max_x = dycast_parameters.extent_max_x
    extent_max_y = dycast_parameters.extent_max_y

    system_coordinate_system = CONFIG.get("dycast", "system_coordinate_system")

    # Set up projections
    projection_user_defined = pyproj.Proj(init="epsg:%s" % srid_of_extent)
    projection_metric = pyproj.Proj(init='epsg:3857')  # metric; same as EPSG:900913
    projection_system_default = pyproj.Proj(init="epsg:%s" % system_coordinate_system)

    # Create corners of rectangle to be transformed to a grid
    north_west = shapely.geometry.Point((extent_min_x, extent_min_y))
    south_east = shapely.geometry.Point((extent_max_x, extent_max_y))

    stepsize = 100  # 100 meter grid step size

    # Project corners to target projection
    # Transform NW and SE points to 3857
    start = pyproj.transform(projection_user_defined, projection_metric, north_west.x, north_west.y)
    end = pyproj.transform(projection_user_defined, projection_metric, south_east.x, south_east.y)

    # Iterate over 2D area
    gridpoints = []
    x = start[0]
    logging.info("Started generating grid...")
    while x < end[0]:
        y = start[1]
        while y > end[1]:
            new_x, new_y = pyproj.transform(projection_metric, projection_system_default, x, y)
            point = get_point_from_lat_long(new_y, new_x, system_coordinate_system)
            gridpoints.append(point)
            y -= stepsize
        x += stepsize

    logging.info("Done generating grid. Result: %s points", len(gridpoints))

    return gridpoints


def is_within_distance(point_1, point_2, distance):
    if point_1.distance(point_2) < distance:
        return True
    else:
        return False
