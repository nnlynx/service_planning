#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# **************************
# src/normatives.py
# **************************

__all__ = [
    "mileage_frequency_standards",
    "service_duration_standards",
]

import datetime


def mileage_frequency_standards(standing_min_percentage=0.6,
                                standing_max_percentage=1.0):
    """ 
    Получает (опционально) процент от диапазона ТОиР, для вычисления пробега из этого диапазона,
    при котором вагону будет планироваться постановка в этот вид ТОиР.
    Возвращает словарь с нормативами межремонтных пробегов по видам ТОиР для вагонов разных моделей. 
    """
    def calculate_standing(standing_min_percentage,
                           standing_max_percentage):
        """ 
        Получает процент от диапазона ТОиР, для вычисления пробега из этого диапазона,
        при котором вагону будет планироваться постановка в этот вид ТОиР.
        Добавляет на месте ключ "standing" с его значением в словарь 
        с нормативами межремонтных пробегов по видам ТОиР.
        """
        for services in standards.values():
            for service_type, mileages in services.items():
                if service_type in ("sr", "kr"):
                    mileages["standing_min"] = mileages["min"]
                    mileages["standing_max"] = mileages["max"]
                else:
                    mileages["standing_min"] = int((mileages["max"] - mileages["min"]) *
                                                   standing_min_percentage + mileages["min"])
                    mileages["standing_max"] = int((mileages["max"] - mileages["min"]) *
                                                   standing_max_percentage + mileages["min"])
    standards = {
        ("81-556", "81-556.1", "81-556.2",
         "81-557", "81-557.1", "81-557.2",
         "81-558", "81-558.1", "81-558.2",
         ): {"to1": {"min": 6_500, "max": 8_500},           # 7_500
             "to2": {"min": 70_000, "max": 80_000},         # 75_000
             "tr1": {"min": 100_000, "max": 140_000},       # 120_000
             "tr2": {"min": 215_000, "max": 265_000},       # 240_000
             "tr3": {"min": 440_000, "max": 520_000},       # 480_000
             "sr": {"min": 1_360_000, "max": 1_520_000},    # 1_440_000
             "kr": {"min": 3_500_000, "max": 5_100_000}     # 4_300_000
             },
        ("81-722", "81-722.1", "81-722.3",
         "81-723", "81-723.1", "81-723.3",
         "81-724", "81-724.1", "81-724.3"
         ): {"to1": {"min": 8_000, "max": 12_000},          # 10_000
             "to2": {"min": 60_000, "max": 80_000},         # 70_000
             "tr1": {"min": 120_000, "max": 160_000},       # 140_000
             "tr2": {"min": 240_000, "max": 320_000},       # 280_000
             "tr3": {"min": 480_000, "max": 640_000},       # 560_000
             "sr": {"min": 1_440_000, "max": 1_920_000},    # 1_680_000
             "kr": {"min": 3_500_000, "max": 5_100_000}     # 4_300_000
             }
    }
    calculate_standing(standing_min_percentage,
                       standing_max_percentage)
    return standards


def service_duration_standards():
    """ 
    Возвращает словарь с нормами простоя по видам ТОиР для вагонов разных моделей. 
    """
    standards = {
        ("81-556", "81-556.1", "81-556.2",
         "81-557", "81-557.1", "81-557.2",
         "81-558", "81-558.1", "81-558.2",
         "81-722", "81-722.3",
         "81-723", "81-723.3",
         "81-724", "81-724.3"
         ): {"to1": datetime.timedelta(days=1),
             "to2": datetime.timedelta(days=2),
             "tr1": datetime.timedelta(days=3),
             "tr2": datetime.timedelta(days=5),
             "tr3": datetime.timedelta(days=45),
             "sr": datetime.timedelta(days=110),
             "kr": datetime.timedelta(days=200)
             }
    }
    return standards
