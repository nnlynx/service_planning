#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# **************************
# src/changing.py
# **************************

__all__ = [
    "adding_wagon_service_periods",
    "change_preplanned_services",
    "change_trains_daily_mileage",
    "change_unhitched_wagons",
    "update_wagon_service_period",
    "update_wagons_attrs",
    "unify_train_service_period"
]

import datetime
from classes import Registry, Train
from typing import Union
from utility import daterange


def update_wagons_attrs(raw_wagons_attrs: dict):
    """ 
    Получает словарь со списками необработанных атрибутов после парсинга дополнительного файла html.
    Вносит информацию о пробегах от ТО-2 (ТО-1 для АТП) и ТО-3 (ТО-2 для АТП) в объекты вагонов.
    """
    for i, attrs in raw_wagons_attrs.items():
        try:
            wagon_number = int(attrs[2])
        except ValueError:
            print(f"Лог функции update_wagons_attrs.\
                  Для {i} ключа некорректное значение номера вагона {attrs[2]}.")
            continue
        wagon_object = Registry.wagons.get(wagon_number)
        if wagon_object is None:
            continue
        else:
            start_date = wagon_object.usage_start_date
            wagon_mileage_0 = wagon_object.mileage[start_date]
            if attrs[14] == "\xa0":
                mileage_tr2_0 = None
            else:
                try:
                    mileage_tr2_0 = int(attrs[14])
                except ValueError:
                    print(f"Лог функции update_wagons_attrs.\
                      Для {i} ключа некорректное значение пробега от ТР-2 {attrs[14]}")
            if attrs[11] == "\xa0":
                mileage_tr1_0 = None
            else:
                try:
                    mileage_tr1_0 = int(attrs[11])
                except ValueError:
                    print(f"Лог функции update_wagons_attrs.\
                      Для {i} ключа некорректное значение пробега от ТР-1 {attrs[11]}")
            correct_data_flag = False
            if (mileage_tr2_0 == wagon_mileage_0["tr2"] or
                    (mileage_tr2_0 < 100 and wagon_mileage_0["tr2"] == 0)):
                if (mileage_tr1_0 == wagon_mileage_0["tr1"] or
                        (mileage_tr1_0 < 100 and wagon_mileage_0["tr1"] == 0)):
                    correct_data_flag = True
                else:
                    print(f"Значения пробега от ТР-1 для вагона № {wagon_number} в выгрузках из функций",
                          '"Пробеги вагонов" и "Техническое обслуживание вагонов" АСУ Депо не совпадают!',
                          "Убедитесь, что выгрузки сделаны в одну дату.")
            else:
                print(f"Значения пробега от ТР-2 для вагона № {wagon_number} в выгрузках из функций",
                      '"Пробеги вагонов" и "Техническое обслуживание вагонов" АСУ Депо не совпадают!',
                      "Убедитесь, что выгрузки сделаны в одну дату.")
            if correct_data_flag:
                # ТО-3 (ТО-2 для АТП)
                if attrs[6] == "ТО-3":
                    if attrs[8] == "\xa0":
                        mileage_to3_0 = None
                    else:
                        try:
                            mileage_to3_0 = int(attrs[8])
                            if (wagon_mileage_0["tr2"] == 0 and
                                wagon_mileage_0["tr1"] == 0 and
                                    mileage_to3_0 < 100):
                                wagon_mileage_0["to3"] = 0
                            else:
                                wagon_mileage_0["to3"] = mileage_to3_0
                        except ValueError:
                            print(f"Лог функции update_wagons_attrs.\
                            Для {i} ключа некорректное значение пробега от ТО-3 {attrs[8]}")
                elif attrs[6] == "ТО-2":
                    if attrs[8] == "\xa0":
                        mileage_to2_0 = None
                    else:
                        try:
                            mileage_to2_0 = int(attrs[8])
                            if (wagon_mileage_0["tr2"] == 0 and
                                wagon_mileage_0["tr1"] == 0 and
                                    mileage_to2_0 < 100):
                                wagon_mileage_0["to2"] = 0
                            else:
                                wagon_mileage_0["to2"] = mileage_to2_0
                        except ValueError:
                            print(f"Лог функции update_wagons_attrs.\
                            Для {i} ключа некорректное значение пробега от ТО-2 {attrs[8]}")
                # ТО-2 (ТО-1 для АТП)
                if attrs[3] == "ТО-2":
                    if attrs[5] == "\xa0":
                        mileage_to2_0 = None
                    else:
                        try:
                            mileage_to2_0 = int(attrs[5])
                            if (wagon_mileage_0["tr2"] == 0 and
                                wagon_mileage_0["tr1"] == 0 and
                                    mileage_to2_0 < 100):
                                wagon_mileage_0["to2"] = 0
                            else:
                                wagon_mileage_0["to2"] = mileage_to2_0
                        except ValueError:
                            print(f"Лог функции update_wagons_attrs.\
                            Для {i} ключа некорректное значение пробега от ТО-2 {attrs[5]}")
                elif attrs[3] == "ТО-1":
                    if attrs[5] == "\xa0":
                        mileage_to1_0 = None
                    else:
                        try:
                            mileage_to1_0 = int(attrs[5])
                            if (wagon_mileage_0["tr2"] == 0 and
                                wagon_mileage_0["tr1"] == 0 and
                                    mileage_to1_0 < 100):
                                wagon_mileage_0["to1"] = 0
                            else:
                                wagon_mileage_0["to1"] = mileage_to1_0
                        except ValueError:
                            print(f"Лог функции update_wagons_attrs.\
                            Для {i} ключа некорректное значение пробега от ТО-1 {attrs[5]}")


def change_unhitched_wagons(wagon_number: int, *, add: bool):
    """
    Получает список с номерами вагонов, которые нужно:
    добавить в словарь unhitched_wagons (при add=True)
    или убрать из словаря unhitched_wagons (при add=False).
    Изменяет на месте словарь unhitched_wagons вида {номер_вагона: объект_вагона}
    """
    if add:
        Registry.unhitched_wagons[wagon_number] = Registry.wagons[wagon_number]
    elif not add:
        Registry.unhitched_wagons.pop(
            wagon_number, f"Вагон {wagon_number} в словаре невцепленных вагонов отсутствует!")

# Пока нигде не применяется
# def change_preplanned_services(wagon_number: int,
#                                date: datetime.date,
#                                new_service: Union[str, None],
#                                verbose=False):
#     """
#     Изменяет для указанного номера вагона в указанную дату
#     отметку о предзапланированном ТОиР
#     """
#     wag_obj = Registry.wagons[wagon_number]
#     if wag_obj.preplanned_services is None:
#         wag_obj.preplanned_services = {new_service}
#     else:
#         wag_obj.preplanned_services.add(new_service)
#     service = Registry.wagons[wagon_number].mileage[date]
#     old_service = service["preplanned_service"]
#     if old_service != new_service:
#         service["preplanned_service"] = new_service
#         if verbose:
#             print(f"Для вагона №{wagon_number} на {date} ",
#                   "отметка о предзапланированном ТОиР изменена ",
#                   f"с {old_service} изменена на {new_service}.", sep="")
#     else:
#         if verbose:
#             print(
#                 f"Для вагона №{wagon_number} на {date} уже стоит отметка о предзапланированном {new_service}")

# Пока нигде не применяется
# def change_allowed_services(wagon_number: int,
#                             date: datetime.date,
#                             new_service: Union[str, None],
#                             verbose=False):
#     """
#     Изменяет для указанного номера вагона в указанную дату
#     отметку о допустимой постановке на ТОиР
#     """
#     level = {"kr": 8, "sr": 7,
#              "tr3": 6, "tr2": 5, "tr1": 4,
#              "to3": 3, "to2": 2, "to1": 1,
#              None: 0}
#     service = Registry.wagons[wagon_number].mileage[date]
#     old_service = service["allowed_service"]
#     # print(f"Ошибка: {wagon_number=} {date=} {old_service=} {new_service=}") # debug
#     if (old_service != new_service and
#             (new_service is None or
#              level[new_service] > level[old_service])):
#         service["allowed_service"] = new_service
#         if verbose:
#             print(f"Для вагона №{wagon_number} на {date} ",
#                   "отметка о допустимой постановке на ТОиР изменена ",
#                   f"с {old_service} на {new_service}.", sep="")
#     else:
#         if verbose:
#             print(
#                 f"Для вагона №{wagon_number} на {date} уже стоит отметка о допустимой постановке на {new_service}")


def change_trains_daily_mileage():
    """
    Устанавливает для вагонов (находящихся в движении) всех сцепов
    значение суточного пробега, равное значению из Registry.wagon_daily_mileage,
    на каждую дату из периода эксплуатации вагона
    """
    for train in Registry.trains.values():
        for wagon in train.wagons.values():
            for date in daterange(wagon.usage_start_date, wagon.usage_end_date):
                if wagon.mileage[date]["idle_reason"] is None:
                    wagon.mileage[date]["daily"] = Registry.wagon_daily_mileage[date]


def adding_wagon_service_periods(wagon_number: int,
                                 date: datetime.date,
                                 service_wagons: dict):
    """
    Проверяет наличие ключа (номера вагона) в словаре service_wagons.
    При отсутствии создает соотвествующую пару ключ-значение со структурой данных.
    При наличии формирует в service_wagons[wagon_number]["periods"] список
    со списками непрерывных диапазонов дат, в которые возможно выполнение ТОиР.
    """
    service_wagons[wagon_number] = service_wagons.get(
        wagon_number, {"periods": [[]]})
    next_date = date + datetime.timedelta(days=1)
    periods = service_wagons[wagon_number]["periods"]
    if next_date < Registry.wagons[wagon_number].usage_end_date:
        next_date_mileage = Registry.wagons[wagon_number].mileage[next_date]
        if len(periods[-1]):
            if (date - periods[-1][-1]).days == 1:
                if next_date_mileage["daily"]:
                    periods[-1].append(date)
                else:
                    periods.pop()
                    if not len(periods):
                        periods.append([])
            elif (date - periods[-1][-1]).days > 1:
                if all([date not in period for period in periods]):
                    if next_date_mileage["daily"]:
                        periods.append([date])
        else:
            if next_date_mileage["daily"]:
                periods[-1].append(date)


def update_wagon_service_period(wagon_number: int,
                                service_type: str,
                                service_wagons: dict):
    """
    Если для вагона предзапланировано выполнении вида ТОиР,
    определяет результирующий диапазон дат возможной постановки вагона 
    на этот вид ТОиР с учетом предзапланированного периода, 
    а для ТР-2 и меньших видов ТОиР - и с учетом выходных.    
    """
    from verification import verify_allowed_service_start_date

    wagon_data = service_wagons[wagon_number]
    wagon_preplanned_services = Registry.wagons[wagon_number].preplanned_services
    duration = Registry.wagons[wagon_number].define_wagon_service_duration(
        service_type)
    service_wagons[wagon_number]["delta"] = duration
    if wagon_preplanned_services is not None:
        if wagon_preplanned_services.get(service_type) is not None:
            no_intersections_flag = True
            for period in wagon_preplanned_services[service_type]:
                start_date, end_date = period
                # debug
                # print(f"Для вагона {wagon_number} доступные интервалы {service_type} до изменения:",
                #       f"{[(str(spis[0]), str(spis[-1])) for spis in service_wagons[wagon_number]['periods'] if len(spis)]}",
                #       f"предзапланированные интервалы: {[(str(spis[0]), str(spis[-1])) for spis in wagon_preplanned_services[service_type]]}")
                preplanned_dates = {
                    date for date in daterange(start_date, end_date)}
                for list_index in range(len(wagon_data["periods"])):
                    date_list = wagon_data["periods"][list_index]
                    dates = set(date_list)
                    x_dates = preplanned_dates & dates
                    if len(x_dates):
                        no_intersections_flag = False
                        date_list = sorted(list(x_dates))
                        if service_type in ("tr2, tr1", "to3", "to2", "to1"):
                            for date in reversed(date_list):
                                if not verify_allowed_service_start_date(service_type,
                                                                         date,
                                                                         duration):
                                    date_list.remove(date)
                        service_wagons[wagon_number]["periods"][list_index] = date_list
                        # debug
                        # print(f"Для вагона {wagon_number} интервалы {service_type} изменены на:",
                        #       f"{[(str(spis[0]), str(spis[-1])) for spis in service_wagons[wagon_number]['periods'] if len(spis)]}")
                        if not len(date_list):
                            print(f"Для вагона № {wagon_number} постановка на {service_type} ",
                                  "в предзапланированный период с учетом норм межремонтных пробегов ",
                                  "и выходных дней невозможна!", sep="")
            # if no_intersections_flag:
                # print(f"Для вагона № {wagon_number} постановка на {service_type} ",
                #       "в предзапланированный период по нормам межремонтных пробегов невозвожна!", sep="")


def unify_train_service_period(sim_service_trains: list,
                               service_wagons: dict):
    """
    Для сцепов из sim_service_trains проверяем, что для всех вагонов сцепа
    в service_wagons установлены одинаковые диапазоны возможных дат выполнения ТОиР.
    Если нет - приводим к единообразию.
    """
    for train_object in sim_service_trains:
        flag_different = False
        x_dates = None
        for wagon_number in train_object.wagons.keys():
            if x_dates is None:
                x_dates = [set(period)
                           for period in service_wagons[wagon_number]["periods"]]
            else:
                for period_index in range(len(service_wagons[wagon_number]["periods"])):
                    dates_period = set(
                        service_wagons[wagon_number]["periods"][period_index])
                    if dates_period != x_dates[period_index]:
                        flag_different = True
                        x_dates[period_index] &= dates_period
        if flag_different:
            # print(f"Сцеп №{train_object.train_number:3d} ",
            #       f"вагоны {[wagon_number for wagon_number in train_object.wagons.keys()]} ",
            #       "- корректировка периодов", sep="")
            new_periods = [sorted(list(period)) for period in x_dates]
            for wagon_number in train_object.wagons.keys():
                service_wagons[wagon_number]["periods"] = new_periods
        # else:
        #     print(f"Сцеп №{train_object.train_number:3d} ",
        #           f"вагоны {[wagon_number for wagon_number in train_object.wagons.keys()]} ",
        #           "- периоды ОК", sep="")
