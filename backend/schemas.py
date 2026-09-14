from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Схема для створення юзера (з паролем)
class UserCreate(BaseModel):
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    role: Optional[str] = "gemologist"

# Схема для оновлення юзера (пароль необов'язковий)
class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None

# Схема для експерта (дані, що ми віддаємо на фронт)
class ExpertBase(BaseModel):
    expert_id: int
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    middle_name: Optional[str]
    role: str

    class Config:
        from_attributes = True

# Схема для створення нового звіту (те, що вводить експерт)
class DiamondCreate(BaseModel):
    # --- Ідентифікація ---
    shape: str  # Обов'язкове
    stone_origin: int # 0=Natural, 1=Lab

    # --- 4C (Основні) ---
    carat_weight: float
    color_grade: int
    clarity_grade: int
    
    # --- Геометрія (Measurements) ---
    measurements_length: float
    measurements_width: float
    measurements_depth: float

    # --- Фізичні параметри (IDC Input) ---
    table_percent: float
    depth_percent: float
    crown_angle: float
    pavilion_angle: float
    
    # --- Деталі ---
    girdle_thickness: Optional[str] = "Medium"
    culet_size: Optional[str] = "None"

    # --- Finish ---
    polish_grade: int
    symmetry_grade: int
    fluorescence_grade: int

    # --- Extra ---
    expert_comment: Optional[str] = None # Коментар експерта
    
    # Поля, які ми або порахуємо, або візьмемо введені (необов'язкові)
    cut_grade: Optional[int] = None
    proportions_grade: Optional[int] = None
    
    # Ціна (якщо 0 - викличемо ML)
    price: Optional[float] = 0.0

# Схема для оновлення звіту (всі поля необов'язкові)
class DiamondUpdate(BaseModel):
    is_sold: Optional[bool] = None
    price: Optional[float] = None

# Схема для статистики (для аналізу експертів)
class ExpertStats(BaseModel):
    expert_username: str
    total_reports: int
    avg_carat: float

# Схема для діаманта (базові поля)
class DiamondReportSchema(BaseModel):
    report_id: str
    report_date: datetime
    shape: str
    carat_weight: float
    color_grade: int
    clarity_grade: int
    cut_grade: int
    price: float
    is_sold: bool

    class Config:
        from_attributes = True

# Схема для токена (JWT)
class Token(BaseModel):
    access_token: str
    token_type: str

class GradeMappingSchema(BaseModel):
    """
    Схема для передачі довідкових даних (метаданих) на клієнт.
    Використовується для заповнення Select-елементів у формах.
    """
    category: str      # Назва категорії (напр. 'color', 'cut')
    grade_value: int   # Числове значення в БД (напр. 2)
    grade_label: str   # Текстова назва для людини (напр. 'F')

    class Config:
        from_attributes = True

class MarketPriceCreate(BaseModel):
    """Схема для встановлення нової ринкової ціни (Admin input)"""
    price_index_value: float
    notes: Optional[str] = None

class MarketPriceResponse(BaseModel):
    """Схема для відображення поточної ціни"""
    id: int
    price_index_value: float
    updated_at: datetime
    notes: Optional[str]

    class Config:
        from_attributes = True
