import datetime
import time
import logging

from sqlalchemy import bindparam, distinct, func, select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext import baked
from sqlalchemy.sql.expression import literal
from sqlalchemy.dialects.postgresql import array

from services import config_service
from services import logging_service
from services import database_service
from services import geography_service

from models.models import Case, DistributionMargin, Risk


CONFIG = config_service.get_config()
bakery = baked.bakery()

class RiskService(object):

    def __init__(self, dycast_parameters):
        self.system_srid = CONFIG.get(
            "dycast", "system_srid")
        self.dycast_parameters = dycast_parameters


    def generate_risk(self):

        session = database_service.get_sqlalchemy_session()
        logging_service.display_current_parameter_set(self.dycast_parameters)

        case_threshold = self.dycast_parameters.case_threshold

        gridpoints = geography_service.generate_grid(self.dycast_parameters)

        day = self.dycast_parameters.startdate
        delta = datetime.timedelta(days=1)

        while day <= self.dycast_parameters.enddate:

            daily_cases_query = self.get_daily_cases_query(session, day)
            daily_case_count = database_service.get_count_for_query(daily_cases_query)

            if daily_case_count >= case_threshold:
                start_time = time.time()
                logging.info("Starting daily_risk for %s", day)
                points_above_threshold = 0

                clusters_per_point = self.get_clusters_per_point_query(session, gridpoints, day)

                for cluster in clusters_per_point:
                    vector_count = len(cluster.case_array)
                    if vector_count >= case_threshold:
                        points_above_threshold += 1
                        point = geography_service.get_shape_from_sqlalch_element(cluster.point)
                        risk = Risk(risk_date=day,
                                    number_of_cases=vector_count,
                                    lat=point.x,
                                    long=point.y)


                for point in gridpoints:
                    cases_in_cluster_query = self.get_cases_in_cluster_query(daily_cases_query, point)
                    vector_count = database_service.get_count_for_query(cases_in_cluster_query)
                    if vector_count >= case_threshold:
                        points_above_threshold += 1
                        risk = Risk(risk_date=day,
                                    number_of_cases=vector_count,
                                    lat=point.x,
                                    long=point.y)

                        risk.close_pairs = self.get_close_space_and_time(cases_in_cluster_query)
                        risk.close_space = self.get_close_space_only_old(cases_in_cluster_query) - risk.close_pairs
                        risk.close_time = self.get_close_time_only(cases_in_cluster_query) - risk.close_pairs

                        risk.cumulative_probability = self.get_cumulative_probability(session,
                                                                                      risk.number_of_cases,
                                                                                      risk.close_pairs,
                                                                                      risk.close_space,
                                                                                      risk.close_time)
                        self.insert_risk(session, risk)

                logging.info(
                    "Finished daily_risk for %s: done %s points", day, len(gridpoints))
                logging.info("Total points above threshold of %s: %s",
                             case_threshold, points_above_threshold)
                logging.info("Time elapsed: %.0f seconds",
                             time.time() - start_time)
            else:
                logging.info("Amount of cases for %s lower than threshold %s: %s, skipping.",
                             day, case_threshold, daily_case_count)

            day += delta

        try:
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logging.exception("There was a problem committing the risk data session")
            logging.exception(e)
            raise
        finally:
            session.close()


    def insert_risk(self, session, risk):
        try:
            session.add(risk)
            session.commit()
        except IntegrityError as e:
            logging.warning("Risk already exists in database for this date '%s' and location '%s - %s', skipping...",
                            risk.risk_date, risk.lat, risk.long)
            session.rollback()
        except SQLAlchemyError as e:
            logging.exception("There was a problem inserting risk")
            logging.exception(e)
            session.rollback()
            raise


    def get_clusters_per_point_query(self, session, gridpoints, riskdate):
        days_prev = self.dycast_parameters.temporal_domain
        enddate = riskdate
        startdate = riskdate - datetime.timedelta(days=(days_prev))

        points_query = self.get_points_query_from_grid(gridpoints)
        # close_space_and_time_query = self.get_close_space_and_time_query(session)

        # case_subquery = session.query(Case).subquery()

        # daily_case_query = session.query(Case) \
        #                     .join(points_query, literal(True)) \
        #                     .filter(Case.report_date >= startdate,
        #                             Case.report_date <= enddate)
        
        return session.query(func.array_agg(
                                func.json_build_object(
                                    Case.id,
                                    Case.location
                                )).label('case_array'),
                             points_query.c.point.geom.label('point')) \
                        .join(points_query, literal(True)) \
                        .filter(Case.report_date >= startdate,
                                Case.report_date <= enddate,
                                func.ST_DWithin(Case.location, points_query.c.point.geom,
                                    self.dycast_parameters.spatial_domain)) \
                        .group_by(points_query.c.point.geom)

        # cluster_per_point_subquery = session.query(Case.id.label('cst_case_id'),
        #                                 points_query.c.point.geom.label('cst_point')) \
        #             .join(points_query, literal(True)) \
        #             .filter(Case.report_date >= startdate,
        #                     Case.report_date <= enddate,
        #                     func.ST_DWithin(Case.location, points_query.c.point.geom,
        #                         dycast_parameters.spatial_domain)) \
        #             .group_by(points_query.c.point.geom,
        #                       Case.id).subquery()
                            
        # cluster_per_point_subquery = cluster_per_point_query.subquery()

        # cst_query = cluster_per_point_query \
        #                 .join(cluster_per_point_subquery, cluster_per_point_subquery.c.cst_point == cluster_per_point_query.c.point )


        # cst_query = cluster_per_point_query.select(cluster_per_point_query.point,
        #                                           func.array_agg(cluster_per_point_query.c.id).label('case_id_array'),
        #                                           func.count(distinct(cluster_per_point_subquery.c.id)).label('cst_count')) \
        #                 .join(cluster_per_point_subquery, cluster_per_point_query.c.point == cluster_per_point_subquery.c.point)

        # cst_query = session.query(func.count(distinct(Case.id)).label('cst_count'),
        #                           func.array_agg(cluster_per_point_query.c.id).label('case_id_array'),
        #                           cluster_per_point_query.c.point.label('point')) \
        #                    .join(cluster_per_point_query, literal(True)) \
        #                    .filter(Case.report_date >= startdate,
        #                            Case.report_date <= enddate,
        #                            func.abs(Case.report_date - cluster_per_point_query.c.report_date) <= dycast_parameters.close_in_time,
        #                            Case.id < cluster_per_point_query.c.id
        #                            ) \
        #                    .group_by(cluster_per_point_query.c.point,
        #                              Case.id)


        # return session.query(func.array_agg(Case.id).label('case_id_array'),
        #                      points_query.c.point.geom.label('point'),
        #                      func.count(distinct(case_subquery.c.id)).label('cst_count')
        #                     ) \
        #     .join(points_query, literal(True)) \
        #     .join(case_subquery, literal(True)) \
        #     .filter(Case.report_date >= startdate,
        #             Case.report_date <= enddate,
        #             func.ST_DWithin(Case.location, points_query.c.point.geom,
        #                             self.dycast_parameters.spatial_domain),
        #             func.ST_DWithin(Case.location, case_subquery.c.location,
        #                             self.dycast_parameters.close_in_space),
        #             func.abs(Case.report_date - case_subquery.c.report_date) <= self.dycast_parameters.close_in_time,
        #             Case.id < case_subquery.c.id
        #             ) \
        #     .group_by(points_query.c.point.geom) \
        #     .all()
            # .outerjoin(close_space_and_time_query, Case.id == close_space_and_time_query.c.id) \


    def get_points_query_from_grid(self, gridpoints):
        return select([
                func.ST_DumpPoints(
                func.ST_Collect(array(gridpoints))) \
            .label('point')]) \
            .alias('point_query')

    def get_close_space_and_time_query(self, session):
        case_query = session.query(Case.id)
        subquery = session.query(Case).subquery()

        return case_query.join(subquery, literal(True)) \
            .filter(func.ST_DWithin(Case.location, subquery.c.location, self.dycast_parameters.close_in_space),
                    func.abs(Case.report_date - subquery.c.report_date) <= self.dycast_parameters.close_in_time,
                    Case.id < subquery.c.id) \
            .subquery()

    def get_daily_cases_query(self, session, riskdate):
        days_prev = self.dycast_parameters.temporal_domain
        enddate = riskdate
        startdate = riskdate - datetime.timedelta(days=(days_prev))

        return session.query(Case).filter(
            Case.report_date >= startdate,
            Case.report_date <= enddate
        )


    def get_cases_in_cluster_query(self, daily_cases_query, point):
        # wkt_point = geography_service.get_point_from_lat_long(point.y, point.x, self.system_srid)
        return daily_cases_query.filter(func.ST_DWithin(Case.location, point, self.dycast_parameters.spatial_domain))


    def get_close_space_and_time_baked(self, session, cluster):
        baked_query = bakery(lambda session: session.query(func.count(Case.id).label('count_cst)')))
        baked_query += lambda q: q.filter(Case.id.op('IN')(bindparam('case_id_array')))
        baked_query += self.get_cst_subquery_baked
        baked_query += lambda q: q.group_by(Case.id)

        return baked_query(session).params(case_id_array=tuple(cluster.case_id_array)).count()

    def get_cst_subquery_baked(self, main_query):
        subquery = main_query.session.query(Case) \
                .filter(Case.id.op('IN')(bindparam('case_id_array'))) \
                .subquery()
        return main_query.join(subquery, literal(True)) \
            .filter(func.ST_DWithin(Case.location, subquery.c.location, self.dycast_parameters.close_in_space),
                    func.abs(Case.report_date - subquery.c.report_date) <= self.dycast_parameters.close_in_time,
                    Case.id < subquery.c.id)


    def get_close_space_and_time_new(self, session, cluster):
        cases_in_cluster = session.query(Case).filter(Case.id.in_(cluster.case_id_array))
        subquery = cases_in_cluster.subquery()
        
        close_in_space_and_time = cases_in_cluster.join(subquery, literal(True)) \
            .filter(func.ST_DWithin(Case.location, subquery.c.location, self.dycast_parameters.close_in_space),
                    func.abs(Case.report_date - subquery.c.report_date) <= self.dycast_parameters.close_in_time,
                    Case.id < subquery.c.id)

        return database_service.get_count_for_query(close_in_space_and_time)


    def get_close_space_and_time(self, cases_in_cluster_query):
        subquery = cases_in_cluster_query.subquery()
        query = cases_in_cluster_query.join(subquery, literal(True)) \
            .filter(func.ST_DWithin(Case.location, subquery.c.location, self.dycast_parameters.close_in_space),
                    func.abs(Case.report_date - subquery.c.report_date) <= self.dycast_parameters.close_in_time,
                    Case.id < subquery.c.id)

        return database_service.get_count_for_query(query)


    def get_close_space_only(self, cluster_per_point_query):
        close_space_count = 0
        cluster_per_point = cluster_per_point_query.all()
        for cluster in cluster_per_point:
            for case in cluster.case_array:
                for case_id, case_location in case.items():
                    for nearby_case in cluster.case_array:
                        for nearby_case_id, nearby_case_location in nearby_case.items():
                            if (case_id > nearby_case_id):
                                if geography_service.is_within_distance(case_location,
                                                                        nearby_case_location,
                                                                        self.dycast_parameters.close_in_space):
                                    close_space_count += 1
            cluster.close_in_space = close_space_count
            close_space_count = 0



        # for cluster in cluster_per_point:
        #     for subquery in cluster_per_point:
        #         if (subquery.point == cluster.point):
        #             if (subquery.case_id > cluster.case_id):
        #                 if geography_service.is_within_distance(subquery.case_location, cluster.case_location, self.dycast_parameters.close_in_space):
        #                     close_space_count += 1

        return cluster_per_point


    def get_close_space_only_old(self, cases_in_cluster_query):
        subquery = cases_in_cluster_query.subquery()
        query = cases_in_cluster_query.join(subquery, literal(True)) \
            .filter(func.ST_DWithin(Case.location, subquery.c.location, self.dycast_parameters.close_in_space),
                    Case.id < subquery.c.id)

        return database_service.get_count_for_query(query)


    def get_close_time_only(self, cases_in_cluster_query):
        subquery = cases_in_cluster_query.subquery()
        query = cases_in_cluster_query.join(subquery, literal(True)) \
            .filter(func.abs(Case.report_date - subquery.c.report_date) <= self.dycast_parameters.close_in_time,
                    Case.id < subquery.c.id)
        return database_service.get_count_for_query(query)


    def get_cumulative_probability(self, session, number_of_cases, close_in_space_and_time, close_in_space, close_in_time):
        exact_match = self.get_exact_match_cumulative_probability(session,
                                                                  number_of_cases,
                                                                  close_in_space_and_time,
                                                                  close_in_space,
                                                                  close_in_time)

        if exact_match:
            return exact_match
        else:
            nearest_close_in_time = self.get_nearest_close_in_time_distribution_margin(session,
                                                                                       number_of_cases,
                                                                                       close_in_space_and_time,
                                                                                       close_in_time)
            if nearest_close_in_time:
                cumulative_probability = self.get_cumulative_probability_by_nearest_close_in_time(session,
                                                                                                  number_of_cases,
                                                                                                  close_in_space_and_time,
                                                                                                  nearest_close_in_time,
                                                                                                  close_in_space)
                return cumulative_probability or 0.001
            else:
                return 0.0001


    def get_exact_match_cumulative_probability(self, session,
                                               number_of_cases,
                                               close_in_space_and_time,
                                               close_in_space,
                                               close_in_time):

        return session.query(DistributionMargin.cumulative_probability) \
            .filter(
                DistributionMargin.number_of_cases == number_of_cases,
                DistributionMargin.close_in_space_and_time == close_in_space_and_time,
                DistributionMargin.close_space == close_in_space,
                DistributionMargin.close_time == close_in_time) \
            .scalar()


    def get_nearest_close_in_time_distribution_margin(self, session,
                                                      number_of_cases,
                                                      close_in_space_and_time,
                                                      close_in_time):

        return session.query(DistributionMargin.close_time) \
            .filter(
                DistributionMargin.number_of_cases == number_of_cases,
                DistributionMargin.close_in_space_and_time >= close_in_space_and_time,
                DistributionMargin.close_time >= close_in_time) \
            .order_by(DistributionMargin.close_time) \
            .first()


    def get_cumulative_probability_by_nearest_close_in_time(self, session,
                                                            number_of_cases,
                                                            close_in_space_and_time,
                                                            nearest_close_in_time,
                                                            close_in_space):

        return session.query(DistributionMargin.cumulative_probability) \
            .filter(
                DistributionMargin.number_of_cases == number_of_cases,
                DistributionMargin.close_in_space_and_time >= close_in_space_and_time,
                DistributionMargin.close_time == nearest_close_in_time,
                DistributionMargin.close_space >= close_in_space) \
            .order_by(DistributionMargin.close_space) \
            .first()
