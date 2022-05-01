#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# **************************
# src/creation.py
# **************************

__all__ = [
    "create_debug_file_output",
    "create_trains",
    "create_wagons",
]

import datetime
from changing import change_unhitched_wagons
from classes import Registry, Train, Wagon
from utility import daterange


def create_wagons(wagons_attrs: list, start_date: datetime.date, end_date: datetime.date):
    """ 
    Получает значение интервала планирования и список со словарями вагонных атрибутов
    Возвращает словарь с экземплярами класса Wagon() вида {номер_вагона: объект_вагона}
    """
    res = {}
    for wagon in wagons_attrs:
        res[wagon["wagon_number"]] = Wagon(
            usage_start_date=start_date, usage_end_date=end_date, **wagon)
    return res


def create_trains(train_lenght: int, hitched_wagons: dict, verbose=False):
    """ 
    Получает словарь вида {номер_сцепа: {номер_вагона: объект_вагона}}.
    Формирует словарь с экземплярами класса Train() вида {номер_сцепа: объект_сцепа}
    """
    if isinstance(train_lenght, int) and isinstance(hitched_wagons, dict):
        res = {}
        for train_number, wagons in hitched_wagons.items():
            res[train_number] = Train(
                train_lenght=train_lenght, train_number=train_number, wagons=wagons)
            if verbose:
                print(
                    f"Создан сцеп № {train_number} из вагонов {[wag_num for wag_num in wagons.keys()]}")
            for wagon_number, wagon_object in res[train_number].wagons.items():
                if not wagon_object.in_train:
                    wagon_object.in_train = True
                    wagon_object.train_number = train_number
                    change_unhitched_wagons(
                        wagon_number=wagon_number, add=False)
                    if verbose:
                        print(
                            f'Вагону № {wagon_number} установлено значение "В сцепе": {True}')
                        print(
                            f'Вагону № {wagon_number} установлено значение "№ сцепа": {train_number}')
                        print(
                            f'Вагон № {wagon_number} удален из списка невцепленных вагонов')
        return res


def create_debug_file_output(write_path):
    """
    Для всех вагонов всех сцепов выгружает содержимое атрибута mileage
    в файл Data/test_planning.txt
    """
    dur = (Registry.planning_end_date - Registry.planning_start_date).days
    with open(write_path, mode="wt", encoding="utf-8") as debug_file:
        print("%12s" % "Сут.пр. |", end="", file=debug_file)
        for date in daterange(Registry.planning_start_date, Registry.planning_end_date):
            res = Registry.wagon_daily_mileage[date]
            print(f"{res:10}|", end="", file=debug_file)
        print("\n", "%11s" % "Ваг.дв. |", end="", file=debug_file)
        for date in daterange(Registry.planning_start_date, Registry.planning_end_date):
            res = Registry.wagons_in_motion[date]
            print(f"{res:10}|", end="", file=debug_file)
        for train_num, train_obj in sorted(Registry.trains.items()):
            print("\n", "%-10s" % "Дата", *[date for date in daterange(
                Registry.planning_start_date, Registry.planning_end_date)], end="", file=debug_file)
            print("\n", f"Сцеп №{train_num:3d} |**********|**********|**********|" *
                  (int(dur/4)), end="", file=debug_file)
            for wag_num, wag_obj in sorted(train_obj.wagons.items()):
                print("\n", f"Ваг.{wag_num:5d} |----------|----------|----------|" *
                      (int(dur/4)), end="", file=debug_file)
                resolver = {  # "preplanned_service": "План |",
                    # "allowed_service": "Допуск |",
                    "idle_reason": "Вид ТОиР |",
                    "daily": "Сут.пр. |",
                    "ne": "От н.э. |",
                    # "kr_sr": "От КР/СР |",
                    "tr3": "От ТР-3 |",
                    "tr2": "От ТР-2 |",
                    "tr1": "От ТР-1 |",
                    # "to3": "От ТО-3 |",
                    "to2": "От ТО-2 |",
                    "to1": "От ТО-1 |"
                }
                for element in (  # "preplanned_service", "allowed_service",
                        "idle_reason", "daily", "ne",  # "kr_sr",
                        "tr3",
                        "tr2", "tr1",
                        # "to3",
                        "to2", "to1"
                ):
                    print("\n", "%11s" %
                          resolver[element], end="", file=debug_file)
                    for date in daterange(Registry.planning_start_date, Registry.planning_end_date):
                        result = wag_obj.mileage[date][element]
                        res = ' ' if result is None else result
                        print(f"{res:10}|", end="", file=debug_file)
