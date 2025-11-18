from sqlalchemy import Column, Integer, String, ForeignKey, Text, Table
from sqlalchemy.orm import relationship

from database import Base

# Промежуточная таблица для связи many-to-many между Program и City
program_cities_association = Table(
    'program_cities',
    Base.metadata,
    Column('program_id', Integer, ForeignKey('programs.id'), primary_key=True),
    Column('city_id', Integer, ForeignKey('cities.id'), primary_key=True)
)

class University(Base):
    __tablename__ = 'university'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    programs = relationship("Program", back_populates="university")

class Program(Base):
    __tablename__ = 'programs'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    university_id = Column(Integer, ForeignKey('university.id'))
    required_subjects = Column(String)

    university = relationship("University", back_populates="programs")
    cities = relationship("City", secondary=program_cities_association, back_populates="programs")

class City(Base):
    __tablename__ = 'cities'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    programs = relationship("Program", secondary=program_cities_association, back_populates="cities")
