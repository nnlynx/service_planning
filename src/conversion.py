#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# **************************
# src/conversion.py
# **************************

__all__ = [
    "convert_confirmed_trains",
    "convert_preplanned_services",
    "convert_wagons_attrs",
]

import datetime
from classes import Registry
from utility import daterange


#       in_train    train_number    -           wagon_number    production_date     wagon_model     mileage_ne_0    mileage_kr_sr_0 mileage_tr3_0   -           -       -               -           mileage_tr1_0   mileage_tr2_0   -       -
# attrs 0           1               2           3               4                   5               6               7               8               9           10      11              12          13              14              15      16                           17
# 0: [  '-',        '\xa0',         'ТЧ-5/3',   '0205',         '05.04.2014',       '81-714.5П',    '490277',       '\xa0',         '0',            'ТР-3',     '0',    '08.01.2018',   '\xa0',     '0',            '0',            '0',    'Октябpьский вагоноремонтный', 'завод']


def convert_wagons_attrs(raw_attrs: dict):
    """ 
    Получает словарь со списками необработанных атрибутов после парсинга основного файла html.
    Возвращает список со словарями обработанных атрибутов для создания экземпляров класса Wagon()
    """
    wagon_attrs = []
    for i, attrs in raw_attrs.items():
        attrs_dict = {}
        # train_number
        if attrs[1] == "\xa0":
            attrs_dict["train_number"] = None
        else:
            try:
                attrs_dict["train_number"] = int(attrs[1])
            except ValueError:
                print(f"Лог функции convert_wagon_attrs.\
                      Для {i} ключа некорректное значение номера сцепа {attrs[1]}.")
        # in_train
        if attrs[0] == "+":
            attrs_dict["in_train"] = True
        elif attrs[0] == "-":
            if attrs_dict["train_number"] is None:
                attrs_dict["in_train"] = False
            elif isinstance(attrs_dict["train_number"], int):
                attrs_dict["in_train"] = True
        # wagon_number
        try:
            attrs_dict["wagon_number"] = int(attrs[3])
        except ValueError:
            print(f"Лог функции convert_wagon_attrs.\
                  Для {i} ключа некорректное значение номера вагона {attrs[3]}.")
            continue
        # production_date
        attrs_dict["production_date"] = attrs[4]
        # wagon_model
        if attrs[5][:3] == "81-":
            attrs_dict["wagon_model"] = attrs[5]
        else:
            print(f"Лог функции convert_wagon_attrs.\
                  Для {i} ключа некорректное значение номера вагона {attrs[5]}.")
            continue
        # mileage_ne_0
        try:
            attrs_dict["mileage_ne_0"] = int(attrs[6])
        except ValueError:
            print(f"Лог функции convert_wagon_attrs.\
                  Для {i} ключа некорректное значение пробега от н.э. {attrs[6]}")
        # mileage_kr_sr_0
        if attrs[7] == "\xa0":
            attrs_dict["mileage_kr_sr_0"] = None
        else:
            try:
                attrs_dict["mileage_kr_sr_0"] = int(attrs[7])
            except ValueError:
                print(f"Лог функции convert_wagon_attrs.\
                      Для {i} ключа некорректное значение пробега от КР/СР {attrs[7]}")
        # mileage_tr3_0
        if attrs[8] == "\xa0":
            attrs_dict["mileage_tr3_0"] = None
        else:
            try:
                mileage_tr3_0 = int(attrs[8])
                if attrs_dict["mileage_kr_sr_0"] == 0:
                    if mileage_tr3_0 < 100:
                        attrs_dict["mileage_tr3_0"] = 0
                    else:
                        attrs_dict["mileage_tr3_0"] = mileage_tr3_0
                else:
                    attrs_dict["mileage_tr3_0"] = mileage_tr3_0
            except ValueError:
                print(f"Лог функции convert_wagon_attrs.\
                      Для {i} ключа некорректное значение пробега от ТР-3 {attrs[8]}")
        # mileage_tr2_0
        if attrs[14] == "\xa0":
            attrs_dict["mileage_tr2_0"] = None
        else:
            try:
                mileage_tr2_0 = int(attrs[14])
                if attrs_dict["mileage_tr3_0"] == 0:
                    if mileage_tr2_0 < 100:
                        attrs_dict["mileage_tr2_0"] = 0
                    else:
                        attrs_dict["mileage_tr2_0"] = mileage_tr2_0
                        # Пока вагон в АСУ Депо не отмечен как принятый с ТР-3,
                        # пробег от ТР-3 будет оставаться равным нулю
                        # даже после возобновления эксплуатации с пассажирами,
                        # в то время как пробеги от ТО-1 до ТР-2 будут ненулевыми
                        attrs_dict["mileage_tr3_0"] = mileage_tr2_0
                else:
                    attrs_dict["mileage_tr2_0"] = mileage_tr2_0
            except ValueError:
                print(f"Лог функции convert_wagon_attrs.\
                      Для {i} ключа некорректное значение пробега от ТР-2 {attrs[14]}")
        # mileage_tr1_0
        if attrs[13] == "\xa0":
            attrs_dict["mileage_tr1_0"] = None
        else:
            try:
                mileage_tr1_0 = int(attrs[13])
                if attrs_dict["mileage_tr2_0"] == 0:
                    if mileage_tr1_0 < 100:
                        attrs_dict["mileage_tr1_0"] = 0
                    else:
                        attrs_dict["mileage_tr1_0"] = mileage_tr1_0
                else:
                    attrs_dict["mileage_tr1_0"] = mileage_tr1_0
            except ValueError:
                print(f"Лог функции convert_wagon_attrs.\
                      Для {i} ключа некорректное значение пробега от ТР-1 {attrs[13]}")
        wagon_attrs.append(attrs_dict)
    return wagon_attrs


def convert_confirmed_trains(confirmed_trains: list):
    """
    Получает список подтвержденных возможных составов вида [[номера_вагонов], [номера_вагонов]]
    Возвращает словарь вида {номер_сцепа: {номер_вагона: объект_вагона}}
    """
    if not confirmed_trains is None:
        count = len(confirmed_trains)
        new_train_numbers = []
        for train_number in range(901, 930):
            if Registry.trains.get(train_number) is None:
                new_train_numbers.append(train_number)
                if len(new_train_numbers) == count:
                    break
        trains_for_creation = {}
        for train_wagons in confirmed_trains:
            train_number = new_train_numbers.pop()
            trains_for_creation[train_number] = {}
            for wagon_number in train_wagons:
                trains_for_creation[train_number][wagon_number] = Registry.wagons[wagon_number]
        return trains_for_creation


def convert_preplanned_services(preplanned_services: list):
    """
    Преобразует список предварительно запланированных ТОиР,
    заданный пользователем (вида [[номер_вагона, "вид_ТОиР", "месяц.год"], ...]), 
    к формату для внесения в расчет вида {номер_вагона: {вид_ТОиР: [(дата_начала, дата_конца), ...]}},
    где дата_начала и дата_конца - границы периода возможной постановки (!) вагона в ТОиР.
    """
    service_types = {"КР": "kr", "СР": "sr",
                     "ТР-3": "tr3", "ТР-2": "tr2",
                     "ТР-1": "tr1", "ТО-3": "to3",
                     "ТО-2": "to2", "ТО-1": "to1"}
    res = {}
    for data_list in preplanned_services:
        wagon_number, raw_service_type, service_end = data_list
        res[wagon_number] = res.get(wagon_number, {})
        month_number = int(service_end[:2])
        year_number = int(service_end[3:])
        service_type = service_types[raw_service_type]
        res[wagon_number][service_type] = res[wagon_number].get(
            service_type, [])
        if month_number == 12:
            end_date = datetime.datetime.strptime(
                ".".join([str(1),
                          str(year_number + 1)]), "%m.%Y").date()
        else:
            end_date = datetime.datetime.strptime(
                ".".join([str(month_number + 1),
                          str(year_number)]), "%m.%Y").date()
        for wagon_models, durations in Registry.duration_standards.items():
            if Registry.wagons[wagon_number].wagon_model in wagon_models:
                date_delta = durations[service_types[raw_service_type]]
        begin_service_end = (end_date -
                             date_delta +
                             datetime.timedelta(days=1))
        begin_service_start = (datetime.datetime.strptime(service_end, "%m.%Y").date() -
                               date_delta +
                               datetime.timedelta(days=1))
        # begin_service_start = datetime.date(
        #     begin_service_end.year, begin_service_end.month, 1)
        res[wagon_number][service_type].append((begin_service_start,
                                               begin_service_end))
    return res
