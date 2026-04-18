"""
Классификатор уровня защищенности (УЗ) на основе найденных ПДн
Согласно требованиям 152-ФЗ
"""

from typing import Dict, List
from enum import Enum


class ProtectionLevel(Enum):
    """Уровни защищенности информационных систем"""
    UZ_1 = "УЗ-1"  # Высокий риск
    UZ_2 = "УЗ-2"  # Значительный риск
    UZ_3 = "УЗ-3"  # Средний риск
    UZ_4 = "УЗ-4"  # Базовый уровень
    NONE = "Нет ПДн"


class ProtectionLevelClassifier:
    """Классификатор уровня защищенности"""
    
    # Категории специальных ПДн (высокий риск)
    SPECIAL_CATEGORIES = {'biometric', 'health', 'special'}
    
    # Государственные идентификаторы и платежная информация
    SENSITIVE_IDENTIFIERS = {'passport', 'snils', 'inn', 'driver_license', 
                             'bank_card', 'bank_account', 'bik'}
    
    # Обычные персональные данные
    REGULAR_PII = {'fio', 'phone', 'email', 'address', 'birth_date'}
    
    # Пороги для определения "больших объемов"
    THRESHOLD_LARGE_VOLUME = 100
    THRESHOLD_MEDIUM_VOLUME = 10
    
    def classify(self, pii_counts: Dict[str, int]) -> ProtectionLevel:
        """
        Определение уровня защищенности на основе найденных ПДн
        
        Args:
            pii_counts: Словарь с количеством найденных ПДн по категориям
            
        Returns:
            Уровень защищенности
        """
        if not pii_counts:
            return ProtectionLevel.NONE
        
        # УЗ-1: Наличие специальных категорий ПДн или биометрических данных
        if any(cat in pii_counts for cat in self.SPECIAL_CATEGORIES):
            return ProtectionLevel.UZ_1
        
        # Подсчет чувствительных идентификаторов
        sensitive_count = sum(
            count for cat, count in pii_counts.items() 
            if cat in self.SENSITIVE_IDENTIFIERS
        )
        
        # Подсчет обычных ПДн
        regular_count = sum(
            count for cat, count in pii_counts.items() 
            if cat in self.REGULAR_PII
        )
        
        # УЗ-2: Платежная информация или государственные идентификаторы в больших объемах
        payment_categories = {'bank_card', 'bank_account', 'bik'}
        has_payment = any(cat in pii_counts for cat in payment_categories)
        
        if has_payment or sensitive_count >= self.THRESHOLD_LARGE_VOLUME:
            return ProtectionLevel.UZ_2
        
        # УЗ-3: Государственные идентификаторы в небольших объемах 
        # или обычные ПДн в больших объемах
        if (sensitive_count >= self.THRESHOLD_MEDIUM_VOLUME or 
            regular_count >= self.THRESHOLD_LARGE_VOLUME):
            return ProtectionLevel.UZ_3
        
        # УЗ-4: Только обычные ПДн в небольших объемах
        if regular_count > 0:
            return ProtectionLevel.UZ_4
        
        return ProtectionLevel.NONE
    
    def get_recommendations(self, level: ProtectionLevel) -> str:
        """
        Получение рекомендаций по обработке данных
        
        Args:
            level: Уровень защищенности
            
        Returns:
            Текст с рекомендациями
        """
        recommendations = {
            ProtectionLevel.UZ_1: (
                "Требуется максимальный уровень защиты. "
                "Необходимо шифрование, строгий контроль доступа, "
                "аудит всех операций с данными."
            ),
            ProtectionLevel.UZ_2: (
                "Требуется усиленная защита. "
                "Рекомендуется шифрование, контроль доступа, "
                "регулярный аудит."
            ),
            ProtectionLevel.UZ_3: (
                "Требуется стандартная защита. "
                "Необходим контроль доступа и базовые меры безопасности."
            ),
            ProtectionLevel.UZ_4: (
                "Требуется базовая защита. "
                "Рекомендуется ограничение доступа и базовые меры безопасности."
            ),
            ProtectionLevel.NONE: "Персональные данные не обнаружены."
        }
        
        return recommendations.get(level, "")
