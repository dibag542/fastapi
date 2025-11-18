from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from models import University, Program, City
from typing import List, Optional

# #получение всех универов
# def get_universities(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(University).offset(skip).limit(limit).all()

#получение универа по конкретному id
def get_university(db: Session, subjects: Optional[List[str]] = None, cities: Optional[List[str]] = None):
    try:
        # Если нет фильтров, просто возвращаем все университеты с eager loading
        if not subjects and not cities:
            return db.query(University).options(joinedload(University.programs)).all()
        
        # Находим программы, которые соответствуют критериям
        # Начинаем с запроса всех программ с загрузкой городов
        query = db.query(Program).options(joinedload(Program.cities))
        
        # Фильтруем по городам, если указаны
        if cities:
            # Используем OR для поиска программ, связанных с любым из выбранных городов
            city_filters = [City.name.ilike(f"%{city}%") for city in cities]
            query = query.join(Program.cities).filter(or_(*city_filters)).distinct()
        
        all_programs = query.all()
        
        # Фильтруем программы по предметам и городам
        matching_programs = []
        for program in all_programs:
            program_matches = True
            
            # Проверяем предметы
            if subjects:
                if not program.required_subjects:
                    program_matches = False
                else:
                    required_subjects_lower = program.required_subjects.lower()
                    all_subjects_match = all(
                        subject.lower() in required_subjects_lower 
                        for subject in subjects
                    )
                    if not all_subjects_match:
                        program_matches = False
            
            # Проверяем города (если не были отфильтрованы в запросе)
            if cities and program_matches:
                if program.cities:
                    program_cities_names = [c.name.lower() for c in program.cities]
                    cities_lower = [city.lower() for city in cities]
                    # Программа должна содержать хотя бы один из выбранных городов
                    city_match = any(
                        any(selected_city in pc or pc in selected_city for pc in program_cities_names)
                        for selected_city in cities_lower
                    )
                    if not city_match:
                        program_matches = False
                else:
                    program_matches = False
            
            if program_matches:
                matching_programs.append(program)
        
        # Если нет подходящих программ, возвращаем пустой список
        if not matching_programs:
            return []
        
        # Получаем ID университетов, у которых есть подходящие программы
        university_ids = {p.university_id for p in matching_programs if p.university_id}
        matching_program_ids = {p.id for p in matching_programs}
        
        # Загружаем университеты с их программами
        universities = db.query(University).options(
            joinedload(University.programs)
        ).filter(University.id.in_(list(university_ids))).all()
        
        # Фильтруем программы внутри каждого университета, оставляя только подходящие
        for university in universities:
            university.programs = [p for p in university.programs if p.id in matching_program_ids]
        
        # Убираем университеты без подходящих программ
        universities = [u for u in universities if u.programs]
        
        return universities
    except Exception as e:
        # Логируем ошибку и пробрасываем исключение
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка в get_university: {e}", exc_info=True)
        raise
