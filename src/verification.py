#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# **************************
# src/verification.py
# **************************

__all__ = [
    "verify_allowed_service_start_date",
    "verify_planning_results"
]

import datetime
from utility import daterange
from classes import Registry


def verify_allowed_service_start_date(service_type: str, date: datetime.date, service_duration: datetime.timedelta):
    """
    Проверяет по delta_month и выходным дням,
    возможно ли начало ТОиР в указанную дату.
    Возвращает bool
    """
    delta_month = {"kr": 7, "sr": 4,
                   "tr3": 2, "tr2": 0, "tr1": 0,
                   "to3": 0, "to2": 0, "to1": 0}
    if (service_type in ("kr", "sr", "tr3") or
            not Registry.transportation_values[date]["holiday"]):
        service_start_month = date.month
        service_end_month = (
            date + service_duration).month
        service_delta_month = service_end_month - service_start_month
        if (service_delta_month <= delta_month[service_type] or
                (service_delta_month + 12) <= delta_month[service_type]):
            return True
        else:
            return False


def verify_planning_results(service_types):
    """
    Получает список видов ТОиР
    Проверяет, что для каждого вагона из Registry.wagons во всем 
    диапазоне планирования соблюдаются нормативы межремонтных пробегов.
    """
    # service_types = ("kr", "sr", "tr3",
    #                  "tr2", "tr1",
    #                  "to3", "to2", "to1")
    from selection import select_debug_data_path

    debug_file_path = select_debug_data_path()
    delta = datetime.timedelta(days=1)
    no_problem_flag = True
    with open(debug_file_path, mode="at", encoding="utf-8") as debug_file:
        for train_number, train_object in sorted(Registry.trains.items()):
            for wagon_number, wagon_object in sorted(train_object.wagons.items()):
                mileage_standards = wagon_object.define_wagon_mileage_stardards()
                wagon_usage_start_date = wagon_object.usage_start_date
                wagon_usage_end_date = wagon_object.usage_end_date
                for date in daterange(wagon_usage_start_date,
                                      wagon_usage_end_date):
                    date_mileages = wagon_object.mileage[date]
                    for service_type in service_types:
                        service_mileage_type = "kr_sr" if service_type in (
                            "kr", "sr") else service_type
                        if date_mileages[service_mileage_type] is None:
                            if date_mileages["ne"] > mileage_standards[service_type]["max"]:
                                print(f"Вагон № {wagon_number:5d}, сцеп № {train_number:3d}:",
                                      f"на дату {str(date)} перепробег от н.э. для {service_type}!", file=debug_file)
                                no_problem_flag = False
                        else:
                            if date_mileages[service_mileage_type] > mileage_standards[service_type]["max"]:
                                print(f"Вагон № {wagon_number:5d}, сцеп № {train_number:3d}:",
                                      f"на дату {str(date)} перепробег от {service_type}!", file=debug_file)
                                no_problem_flag = False
                            elif (date_mileages[service_mileage_type] == 0 and
                                  date_mileages["idle_reason"] in service_types):
                                previous_date = date - delta
                                if previous_date >= wagon_usage_start_date:
                                    previous_date_mileages = wagon_object.mileage[previous_date]
                                    if previous_date_mileages[service_mileage_type] is None:
                                        service_standing_mileage = date_mileages["ne"]
                                    elif previous_date_mileages[service_mileage_type]:
                                        service_standing_mileage = (previous_date_mileages[service_type] +
                                                                    previous_date_mileages["daily"])
                                        if service_standing_mileage > mileage_standards[service_type]["max"]:

                                            print(f"Вагон № {wagon_number:5d}, сцеп № {train_number:3d}:",
                                                  f"{str(date)} запланирован {date_mileages['idle_reason']}.",
                                                  f"От {service_type} перепробег!", file=debug_file)
                                            no_problem_flag = False
                                        elif service_standing_mileage < mileage_standards[service_type]["min"]:
                                            if (date_mileages['idle_reason'] != service_type and
                                                    (service_type != "to1" and
                                                     service_type != "to2" and
                                                     service_type != "tr1")):
                                                print(f"Вагон № {wagon_number:5d}, сцеп № {train_number:3d}:",
                                                      f"{str(date)} запланирован {date_mileages['idle_reason']}.",
                                                      f"От {service_type} недопробег!", file=debug_file)
                                            no_problem_flag = False
    if no_problem_flag:
        print("Замечаний по расчету не обнаружено!")
    else:
        print("Выявленные замечания к расчету записаны в файл Data/debug.txt")
