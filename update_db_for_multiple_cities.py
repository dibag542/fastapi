"""
Скрипт для обновления базы данных для поддержки нескольких городов на программу.
1. Создает таблицу program_cities (если не существует)
2. Переносит данные из city_id в program_cities
3. Удаляет колонку city_id из таблицы programs
"""
from sqlalchemy import text
from database import engine, SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_database_for_multiple_cities():
    """Обновляет базу данных для поддержки нескольких городов на программу"""
    # Закрываем все соединения с базой данных
    logger.info("Закрытие соединений с базой данных...")
    engine.dispose()
    
    db = SessionLocal()
    try:
        # Проверяем, существует ли таблица program_cities
        result = db.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='program_cities'
        """))
        table_exists = result.fetchone() is not None
        
        if not table_exists:
            logger.info("Создание таблицы program_cities...")
            try:
                db.execute(text("""
                    CREATE TABLE program_cities (
                        program_id INTEGER NOT NULL,
                        city_id INTEGER NOT NULL,
                        PRIMARY KEY (program_id, city_id),
                        FOREIGN KEY (program_id) REFERENCES programs (id),
                        FOREIGN KEY (city_id) REFERENCES cities (id)
                    )
                """))
                db.commit()
                logger.info("Таблица program_cities создана!")
            except Exception as e:
                logger.warning(f"Не удалось создать таблицу program_cities: {e}")
                logger.warning("Пожалуйста, закройте все приложения, использующие базу данных, и попробуйте снова")
                return
        else:
            logger.info("Таблица program_cities уже существует")
        
        # Проверяем, есть ли колонка city_id в таблице programs
        result = db.execute(text("PRAGMA table_info(programs)"))
        columns = {row[1]: row for row in result.fetchall()}
        
        if 'city_id' in columns:
            logger.info("Найдена колонка city_id - переносим данные в program_cities...")
            
            # Получаем все программы с city_id
            programs_with_city = db.execute(text("""
                SELECT id, city_id FROM programs WHERE city_id IS NOT NULL
            """)).fetchall()
            
            # Переносим данные в program_cities
            for program_id, city_id in programs_with_city:
                # Проверяем, нет ли уже такой записи
                existing = db.execute(text("""
                    SELECT 1 FROM program_cities 
                    WHERE program_id = :program_id AND city_id = :city_id
                """), {"program_id": program_id, "city_id": city_id}).fetchone()
                
                if not existing:
                    db.execute(text("""
                        INSERT INTO program_cities (program_id, city_id) 
                        VALUES (:program_id, :city_id)
                    """), {"program_id": program_id, "city_id": city_id})
                    logger.info(f"Перенесена связь: программа {program_id} -> город {city_id}")
            
            db.commit()
            logger.info(f"Перенесено связей: {len(programs_with_city)}")
            
            # Удаляем колонку city_id (в SQLite нужно пересоздать таблицу)
            logger.info("Удаление колонки city_id из таблицы programs...")
            
            # Сохраняем данные
            programs_data = db.execute(text("""
                SELECT id, name, university_id, required_subjects FROM programs
            """)).fetchall()
            
            # Создаем новую таблицу без city_id
            db.execute(text("""
                CREATE TABLE programs_new (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    university_id INTEGER,
                    required_subjects VARCHAR,
                    FOREIGN KEY (university_id) REFERENCES university (id)
                )
            """))
            
            # Копируем данные
            for program_id, name, university_id, required_subjects in programs_data:
                db.execute(text("""
                    INSERT INTO programs_new (id, name, university_id, required_subjects)
                    VALUES (:id, :name, :university_id, :required_subjects)
                """), {
                    "id": program_id,
                    "name": name,
                    "university_id": university_id,
                    "required_subjects": required_subjects
                })
            
            # Удаляем старую таблицу
            db.execute(text("DROP TABLE programs"))
            
            # Переименовываем новую таблицу
            db.execute(text("ALTER TABLE programs_new RENAME TO programs"))
            
            db.commit()
            logger.info("Колонка city_id удалена из таблицы programs!")
        else:
            logger.info("Колонка city_id не найдена в таблице programs")
        
        print("\n" + "="*50)
        print("База данных успешно обновлена!")
        print("="*50)
        print("\nТеперь структура базы данных:")
        print("- Таблица 'cities' - хранит города")
        print("- Таблица 'programs' - хранит программы (без city_id)")
        print("- Таблица 'program_cities' - связь many-to-many между программами и городами")
        print("\nТеперь каждая программа может быть связана с несколькими городами!")
        print()
        
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при обновлении базы данных: {e}", exc_info=True)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    update_database_for_multiple_cities()

