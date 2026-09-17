class DiamondCalculator:
    """
    Детермінований demo-калькулятор для Proportions і Cut (Round Brilliant).

    Це не повна реалізація IDC 2013: підтримуються лише чотири геометричні
    параметри, а підсумок для MVP є найгіршим із трьох component grades.
    """

    @staticmethod
    def evaluate_proportions(table: float, depth: float, crown: float, pavilion: float) -> int:
        """
        Повертає demo-grade (0=Ex, 1=VG, 2=G, 3=F) за чотирма параметрами.
        """
        score = 0 # Починаємо з 0 (Excellent)

        # Table Size (Ідеал 56-61%)
        if 56.0 <= table <= 61.0: pass
        elif 53.0 <= table < 56.0 or 61.0 < table <= 64.0: score = max(score, 1) # VG
        elif 51.0 <= table < 53.0 or 64.0 < table <= 68.0: score = max(score, 2) # Good
        else: score = max(score, 3) # Fair

        # Crown Angle (Ідеал 33.5 - 36.5)
        if 33.5 <= crown <= 36.5: pass
        elif 32.0 <= crown < 33.5 or 36.5 < crown <= 38.0: score = max(score, 1)
        else: score = max(score, 2)

        # Pavilion Angle (Ідеал 40.6 - 41.0) - Дуже суворо!
        if 40.6 <= pavilion <= 41.0: pass
        elif 40.2 <= pavilion < 40.6 or 41.0 < pavilion <= 41.8: score = max(score, 1)
        else: score = max(score, 2)

        # Total Depth (Ідеал 59.0 - 63.0)
        if 59.0 <= depth <= 63.0: pass
        else: score = max(score, 1)

        return min(score, 4) # Не гірше Poor

    @staticmethod
    def calculate_final_cut(proportions: int, polish: int, symmetry: int) -> int:
        """
        Demo-підсумок Cut — найгірша з трьох компонентних оцінок.
        """
        return max(proportions, polish, symmetry)
