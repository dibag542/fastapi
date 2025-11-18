from typing import List, Optional
from pydantic import BaseModel

class UniversityBase(BaseModel):
    name: str

class University(UniversityBase):
    id: int
    programs: List['Program'] = []

    class Config:
        from_attributes = True

class ProgramBase(BaseModel):
    name: str
    required_subjects: str

class Program(ProgramBase):
    id: int
    university: University
    cities: List['City'] = []

    class Config:
        from_attributes = True

class CityBase(BaseModel):
    name: str

class City(CityBase):
    id: int
    programs: List['Program'] = []

    class Config:
        from_attributes = True


