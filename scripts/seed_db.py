import mysql.connector
import pandas as pd
import random
import math
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from backend import database, models
from backend.config import get_mariadb_connection_options, get_required_env
from backend.security import get_password_hash



def get_connection(db_name: str | None = None):
    options = get_mariadb_connection_options()
    if db_name is not None:
        options["database"] = db_name
    return mysql.connector.connect(**options)

def generate_dimensions(carat, shape, depth_pct):
    # Базова імітація розмірів в залежності від форми
    if shape == 'Round':
        avg_diam = 6.4 * math.pow(carat, 1/3)
        ratio = 1.0
    elif shape in ['Princess', 'Cushion']:
        avg_diam = 5.5 * math.pow(carat, 1/3) # Квадратні менші візуально
        ratio = 1.0
    elif shape == 'Oval':
        avg_diam = 6.0 * math.pow(carat, 1/3)
        ratio = 1.4 # Витягнутий
    elif shape == 'Emerald':
        avg_diam = 5.8 * math.pow(carat, 1/3)
        ratio = 1.35
    elif shape == 'Marquise':
        avg_diam = 5.2 * math.pow(carat, 1/3)
        ratio = 1.85
    elif shape == 'Pear':
        avg_diam = 5.8 * math.pow(carat, 1/3)
        ratio = 1.55
    else:
        avg_diam = 6.0 * math.pow(carat, 1/3)
        ratio = 1.0

    offset = random.uniform(-0.05, 0.05)
    width = round(avg_diam + offset, 2)
    length = round(width * ratio, 2)
    depth_mm = round(width * (depth_pct / 100), 2)
    
    return length, width, depth_mm

def seed_data():
    # Перевіряємо конфігурацію до будь-якого руйнівного SQL-запиту.
    admin_password = get_required_env("SEED_ADMIN_PASSWORD")
    gemologist_password = get_required_env("SEED_GEMOLOGIST_PASSWORD")

    raw_conn = get_connection()
    raw_cursor = raw_conn.cursor()
    
    print(" -> [1/5] Перестворення локальних баз даних...")
    raw_cursor.execute("DROP DATABASE IF EXISTS diamond_oltp")
    raw_cursor.execute("DROP DATABASE IF EXISTS diamond_market")
    raw_cursor.execute("DROP DATABASE IF EXISTS diamond_analytics")
    raw_cursor.execute("CREATE DATABASE diamond_oltp")
    raw_cursor.execute("CREATE DATABASE diamond_market")
    raw_cursor.execute("CREATE DATABASE diamond_analytics")
    
    raw_conn.commit()
    raw_cursor.close()
    raw_conn.close()

    print(" -> [2/5] Створення таблиць...")
    models.Base.metadata.create_all(bind=database.engine)

    # --- MARKET ---
    print(" -> [3/5] Наповнення Market (Mappings)...")
    conn_market = get_connection("diamond_market")
    cursor_market = conn_market.cursor()
    
    mappings = []
    
    # 1. Shape
    shapes_list = ['Round', 'Princess', 'Oval', 'Emerald', 'Marquise', 'Cushion', 'Pear', 'Radiant', 'Heart']
    for i, l in enumerate(shapes_list): 
        # category='shape', value=i (для порядку), label=Назва
        mappings.append(('shape', i, l))

    # 2. Color
    colors = ['D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N-Z']
    for i, l in enumerate(colors): mappings.append(('color', i, l))
        
    # 3. Clarity
    clarities = ['FL', 'IF', 'VVS1', 'VVS2', 'VS1', 'VS2', 'SI1', 'SI2', 'I1', 'I2', 'I3']
    for i, l in enumerate(clarities): mappings.append(('clarity', i, l))
        
    # 4. Grades (Cut, Polish, Sym, Prop)
    cuts = ['Excellent', 'Very Good', 'Good', 'Fair', 'Poor']
    for i, l in enumerate(cuts): 
        mappings.append(('cut', i, l))
        mappings.append(('polish', i, l))
        mappings.append(('symmetry', i, l))
        mappings.append(('proportions', i, l))

    # 5. Fluorescence
    fluro = ['None', 'Faint', 'Medium', 'Strong', 'Very Strong']
    for i, l in enumerate(fluro): mappings.append(('fluorescence', i, l))

    # 6. Origin
    origins = ['Natural', 'Lab-Grown']
    for i, l in enumerate(origins): mappings.append(('origin', i, l))

    cursor_market.executemany("INSERT INTO grade_mappings (category, grade_value, grade_label) VALUES (%s, %s, %s)", mappings)
    cursor_market.execute("INSERT INTO market_price_reference (price_index_value, updated_by, notes) VALUES (6000.00, 1, 'Base Index 2026')")
    
    conn_market.commit()
    cursor_market.close()
    conn_market.close()

    # --- OLTP ---
    conn = get_connection("diamond_oltp")
    cursor = conn.cursor()

    print(" -> [4/5] Додавання експертів...")
    admin_password_hash = get_password_hash(admin_password)
    gemologist_password_hash = get_password_hash(gemologist_password)
    experts_data = [
        (1, "admin", admin_password_hash, "admin", "System", "Admin", "Zero"),
        (2, "expert_1", gemologist_password_hash, "gemologist", "Expert", "One", "First"),
        (3, "expert_2", gemologist_password_hash, "gemologist", "Expert", "Two", "Second"),
        (4, "expert_3", gemologist_password_hash, "gemologist", "Expert", "Three", "Third"),
        (5, "expert_4", gemologist_password_hash, "gemologist", "Expert", "Four", "Fourth"),
        (6, "expert_5", gemologist_password_hash, "gemologist", "Expert", "Five", "Fifth"),
    ]
    cursor.executemany(
        "INSERT INTO experts (expert_id, username, password_hash, role, first_name, last_name, middle_name) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        experts_data
    )

    print(" -> [5/5] Генерація звітів...")
    data_path = Path(__file__).resolve().parent.parent / "data" / "diamonds_dataset.csv"
    
    try:
        df = pd.read_csv(data_path)
        df['sale_date'] = df['sale_date'].where(pd.notnull(df['sale_date']), None)
        
        count = 0
        girdles = ['Thin', 'Medium', 'Slightly Thick', 'Thick', 'Very Thick']
        culets = ['None', 'Very Small', 'Small', 'Medium']
        comments = ["Excellent stone.", "Minor inclusions.", "Cloudy.", "Strong fluorescence.", "Perfect cut."]

        for _, row in df.iterrows():
            # Випадкова форма (оскільки в CSV її немає)
            shape = random.choice(shapes_list)
            
            # Генерація розмірів під форму
            length, width, depth_mm = generate_dimensions(row['carat_weight'], shape, row.get('depth_percent', 61.5))
            
            girdle = random.choice(girdles)
            culet = random.choice(culets)
            comment = random.choice(comments)
            sentiment = 1 if "Excellent" in comment or "Perfect" in comment else 0
            
            expert_id = row['expert_id'] + 1
            if expert_id > 6: expert_id = 6

            sql = """INSERT INTO diamond_reports 
                     (report_id, report_date, shape,
                      measurements_length, measurements_width, measurements_depth,
                      table_percent, depth_percent, crown_angle, pavilion_angle,
                      girdle_thickness, culet_size,
                      carat_weight, color_grade, clarity_grade, cut_grade, 
                      polish_grade, symmetry_grade, proportions_grade, fluorescence_grade, stone_origin, 
                      expert_id, evaluation_time_sec, 
                      expert_comment, report_notes_length, report_sentiment,
                      plotting_image, real_image,
                      price, is_sold, sale_date, days_on_market) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            
            values = (
                row['report_id'], row['report_date'], shape,
                length, width, depth_mm,
                row.get('table_percent', 57), row.get('depth_percent', 61.5), 
                row.get('crown_angle', 34.5), row.get('pavilion_angle', 40.8),
                girdle, culet,
                row['carat_weight'], row['color_grade'], row['clarity_grade'], row['cut_grade'],
                row['polish_grade'], row['symmetry_grade'], row['proportions_grade'], row['fluorescence_grade'], row['stone_origin'],
                expert_id, int(row.get('evaluation_time_min', 15) * 60),
                comment, row.get('report_notes_length', 0), sentiment,
                "/uploads/plots/default.jpg", "/uploads/real/default.jpg",
                row['price'], row['is_sold'], row['sale_date'], row['days_on_market']
            )
            cursor.execute(sql, values)
            count += 1

        conn.commit()
        print(f" -> ✅ Успішно! Завантажено {count} звітів з формами та словниками.")

    except Exception as e:
        print(f"ПОМИЛКА: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    seed_data()
