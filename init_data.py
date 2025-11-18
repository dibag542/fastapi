from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import University, Program, City

# Создаем сессию
db = SessionLocal()

try:
    # Создаем университет
    msu = University(name="МГУ")
    db.add(msu)

    # Создаем программу
    biology_program = Program(name="Биология", required_subjects="Химия, Биология", university=msu)
    db.add(biology_program)

    # Создаем города академической мобильности
    paris = City(name="Париж")
    shanghai = City(name="Шанхай")
    beijing = City(name="Пекин")
    db.add(paris)
    db.add(shanghai)
    db.add(beijing)

    # Связываем программу с несколькими городами
    biology_program.cities.append(paris)
    biology_program.cities.append(shanghai)
    biology_program.cities.append(beijing)
    
    # Или можно добавить все сразу:
    # biology_program.cities = [paris, shanghai, beijing]

    # Сохраняем изменения
    db.commit()
except Exception as e:
    db.rollback()
    print(f"Произошла ошибка: {e}")
finally:
    db.close()