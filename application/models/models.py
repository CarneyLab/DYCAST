import logging

from sqlalchemy import Column, Integer, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry


DeclarativeBase = declarative_base()



# Helper functions

def create_tables(engine):
    logging.info("Creating tables...")
    DeclarativeBase.metadata.create_all(engine)



# Entities

class Case(DeclarativeBase):
    """SQLAlchemy Case model"""
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True)
    report_date = Column(Date)
    location = Column(Geometry(geometry_type='POINT', srid='3857'))

class DistributionMargin(DeclarativeBase):
    """SQLAlchemy Distribution Margins model (Monte Carlo)"""
    __tablename__ = "distribution_margins"

    number_of_cases = Column(Integer, primary_key=True, index=True)
    close_in_space_and_time = Column(Integer, primary_key=True, index=True)
    probability = Column(Float)
    cumulative_probability = Column(Float)
    close_space = Column(Integer, primary_key=True, index=True)
    close_time = Column(Integer, primary_key=True, index=True)

class Risk(DeclarativeBase):
    """SQLAlchemy Risk model"""
    __tablename__ = "risk"

    risk_date = Column(Date, primary_key=True)
    lat = Column(Float, primary_key=True)
    long = Column(Float, primary_key=True)
    location = Column(Geometry(geometry_type='POINT', srid='3857'))
    number_of_cases = Column(Integer)
    close_pairs = Column(Integer)
    close_space = Column(Integer)
    close_time = Column(Integer)
    cumulative_probability = Column(Float)
