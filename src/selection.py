#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# **************************
# src/selection.py
# **************************

__all__ = [
    "select_current_idle_end",
    "select_debug_data_path",
    "select_extra_wagon_data_path",
    "select_hitched_wagons",
    "select_idle_wagons",
    "select_line_motion_time",
    "select_main_wagon_data_path",
    "select_output_data_path",
    "select_planning_end_date",
    "select_possible_trains",
    "select_preplanned_services",
    "select_text_result_data_path",
    "select_transportation_values",
    "select_unhitched_wagons",
]


import datetime
from classes import Registry
from os.path import abspath, dirname, join
from utility import daterange


def select_main_wagon_data_path():
    """
    Возвращает абсолютный путь до html-файла выгрузки 
    из функции "Пробеги вагонов" АСУ Депо с данными
    по ТР-1 - КР для парсинга.
    """
    current_dir = dirname(__file__)
    data_path = abspath(
        join(current_dir, "..", "Data", "Пробеги вагонов (ТР-1 - КР)", "Odometer_file_1_for_parcing_2022-03-31.html"))
    return data_path


def select_extra_wagon_data_path():
    """
    Возвращает абсолютный путь до html-файла выгрузки 
    из функции "Техническое обслуживание вагонов" АСУ Депо 
    с данными по ТО-1 - ТР-2 для парсинга.
    """
    current_dir = dirname(__file__)
    data_path = abspath(
        join(current_dir, "..", "Data", "Техническое обслуживание вагонов (ТО-1 - ТР-2)", "Odometer_file_2_for_parcing_2022-03-31.html"))
    return data_path


def select_output_data_path():
    """
    Возвращает абсолютный путь до txt-файла с тестовым выводом расчета.
    """
    current_dir = dirname(__file__)
    data_path = abspath(
        join(current_dir, "..", "Data", "test_planning.txt"))
    return data_path


def select_debug_data_path():
    """
    Возвращает абсолютный путь до отладочного txt-файла.
    """
    current_dir = dirname(__file__)
    data_path = abspath(
        join(current_dir, "..", "Data", "debug.txt"))
    return data_path


def select_text_result_data_path():
    """
    Возвращает абсолютный путь до txt-файла с результатами расчета.
    """
    current_dir = dirname(__file__)
    data_path = abspath(
        join(current_dir, "..", "Data", "result_services.txt"))
    return data_path


def select_planning_end_date():
    """
    Запрашивает у пользователя дату окончания расчета
    (по умолчанию - 01 января года, следующего через один от даты начала расчета)
    Возвращает дату окончания расчета (первая дата, которая не входит в расчет).
    """
    end_date = datetime.datetime.strptime(
        "01.01.2024", "%d.%m.%Y").date()
    return end_date


def select_hitched_wagons():
    """
    Получает словарь вагонов вида {номер_вагона: объект_вагона}.
    Собирает все вагоны, имеющие метку о нахождении в сцепе, в словарь вида
    {номер_сцепа: {номер_вагона: объект_вагона}} и возвращает его
    """
    hitched_wagons = {}
    for wagon_object in Registry.wagons.values():
        tn = wagon_object.train_number
        if wagon_object.in_train:
            hitched_wagons[tn] = hitched_wagons.get(tn, {})
            hitched_wagons[tn][wagon_object.wagon_number] = wagon_object
    return hitched_wagons


def select_unhitched_wagons():
    """
    Обрабатывает словарь вагонов (вида {номер_вагона: объект_вагона}) из реестра.
    Собирает все вагоны, не имеющие метки о нахождении в сцепе, в словарь вида
    {номер_вагона: объект_вагона} и возвращает его
    """
    unhitched_wagons = {}
    for wagon_number, wagon_object in Registry.wagons.items():
        if wagon_object.train_number is None:
            unhitched_wagons[wagon_number] = wagon_object
    return unhitched_wagons


def select_possible_trains():
    """
    Обрабатывает словарь невцепленных вагонов (вида {номер_вагона: объект_вагона}) из реестра.
    Возвращает словарь списков вагонов (вида {порядковый_номер: [вагон1, вагон2...]}),
    которые возможно ездят в одном сцепе, для последующего одобрения пользователем.
    """
    # tmp_dict вида {дата_изготовления: {счетчик: количество, вагоны: {номер_вагона: объект_вагона}},
    #                   пробег_от_н.э.: {счетчик: количество, вагоны: {номер_вагона: объект_вагона}}}
    tmp_dict = {}
    for wagon_number, wagon_object in Registry.unhitched_wagons.items():
        pd = wagon_object.production_date
        ne = wagon_object.mileage[wagon_object.usage_start_date]["ne"]
        # группируем вагоны по дате изготовления
        tmp_dict[pd] = tmp_dict.get(pd, {})
        tmp_dict[pd]["count"] = tmp_dict[pd].get("count", 0) + 1
        tmp_dict[pd]["wagons"] = tmp_dict[pd].get("wagons", {})
        tmp_dict[pd]["wagons"][wagon_number] = wagon_object
        # группируем вагоны по пробегу от н.э.
        tmp_dict[ne] = tmp_dict.get(ne, {})
        tmp_dict[ne]["count"] = tmp_dict[ne].get("count", 0) + 1
        tmp_dict[ne]["wagons"] = tmp_dict[ne].get("wagons", {})
        tmp_dict[ne]["wagons"][wagon_number] = wagon_object
    possible_trains_list = []
    for wagons_values in tmp_dict.values():
        if wagons_values["count"] == Registry.train_lenght:
            tmp_list = sorted(
                [wagon_number for wagon_number in wagons_values["wagons"].keys()])
            if tmp_list not in possible_trains_list:
                possible_trains_list.append(tmp_list)

    possible_trains_dict = {(num+1): list(val)
                            for num, val in enumerate(possible_trains_list)}
    return possible_trains_dict


def select_transportation_values():
    """
    Запрашивает у пользователя сумму пар поездов за сутки для будней
    и для выходных, а также максимальную часовую парность (по данным от ОЛП).
    Возвращает словарь вида:
    {дата_начала_периода: {"workday": пар_поездов_будни,
                           "holiday": пар_поездов_выходные,
                           "max": максимальная_парность
                           }
    """
    return {datetime.date(2021, 9, 1): {"workday": 390, "holiday": 350, "max": 26},
            datetime.date(2022, 6, 1): {"workday": 371, "holiday": 324, "max": 24},
            datetime.date(2022, 9, 1): {"workday": 390, "holiday": 350, "max": 26},
            datetime.date(2023, 6, 1): {"workday": 371, "holiday": 324, "max": 24},
            datetime.date(2023, 9, 1): {"workday": 390, "holiday": 350, "max": 26},
            # datetime.date(2024, 6, 1): {"workday": 371, "holiday": 324, "max": 24},
            # datetime.date(2024, 9, 1): {"workday": 390, "holiday": 350, "max": 26},
            # datetime.date(2025, 6, 1): {"workday": 371, "holiday": 324, "max": 24},
            # datetime.date(2025, 9, 1): {"workday": 390, "holiday": 350, "max": 26},
            # datetime.date(2026, 6, 1): {"workday": 371, "holiday": 324, "max": 24},
            # datetime.date(2026, 9, 1): {"workday": 390, "holiday": 350, "max": 26},
            # datetime.date(2027, 6, 1): {"workday": 371, "holiday": 324, "max": 24},
            # datetime.date(2027, 9, 1): {"workday": 390, "holiday": 350, "max": 26}
            }


def select_line_motion_time():
    """
    Запрашивает у пользователя данные о времени движения поезда по линии
    (общее время из режимов ведения поездов) и времени оборота состава.
    Возвращает время движения + оборота в минутах.
    """
    # Время движения - 40 мин., время оборота - 1 мин 29 сек
    return 41.48333333333333


def select_preplanned_services():
    """
    Запрашивает у пользователя информацию о заранее запланированных ТОиР:
    номер вагона, дату, вид ТО или ТР
    Возвращает список списков вида [[номер_вагона, вид_ТОиР, дата_окончания], [...]]
    """
    services = [
        # ТР-3
        [22081, "ТР-3", "06.2022"],
        [22082, "ТР-3", "06.2022"],
        [23121, "ТР-3", "06.2022"],
        [23122, "ТР-3", "06.2022"],
        [24081, "ТР-3", "06.2022"],
        [24082, "ТР-3", "06.2022"],

        [22095, "ТР-3", "06.2022"],
        [22096, "ТР-3", "06.2022"],
        [23135, "ТР-3", "06.2022"],
        [23136, "ТР-3", "06.2022"],
        [24095, "ТР-3", "06.2022"],
        [24096, "ТР-3", "06.2022"],

        [56035, "ТР-3", "08.2022"],
        [56036, "ТР-3", "08.2022"],
        [57035, "ТР-3", "08.2022"],
        [57036, "ТР-3", "08.2022"],
        [58035, "ТР-3", "08.2022"],
        [58036, "ТР-3", "08.2022"],

        [22115, "ТР-3", "08.2022"],
        [22116, "ТР-3", "08.2022"],
        [23155, "ТР-3", "08.2022"],
        [23156, "ТР-3", "08.2022"],
        [24115, "ТР-3", "08.2022"],
        [24116, "ТР-3", "08.2022"],

        [22113, "ТР-3", "09.2022"],
        [22114, "ТР-3", "09.2022"],
        [23153, "ТР-3", "09.2022"],
        [23154, "ТР-3", "09.2022"],
        [24113, "ТР-3", "09.2022"],
        [24114, "ТР-3", "09.2022"],

        [56009, "ТР-3", "10.2022"],
        [56010, "ТР-3", "10.2022"],
        [57009, "ТР-3", "10.2022"],
        [57010, "ТР-3", "10.2022"],
        [58009, "ТР-3", "10.2022"],
        [58010, "ТР-3", "10.2022"],

        [56037, "ТР-3", "10.2022"],
        [56038, "ТР-3", "10.2022"],
        [57037, "ТР-3", "10.2022"],
        [57038, "ТР-3", "10.2022"],
        [58037, "ТР-3", "10.2022"],
        [58038, "ТР-3", "10.2022"],

        [22109, "ТР-3", "10.2022"],
        [22110, "ТР-3", "10.2022"],
        [23149, "ТР-3", "10.2022"],
        [23150, "ТР-3", "10.2022"],
        [24109, "ТР-3", "10.2022"],
        [24110, "ТР-3", "10.2022"],

        [56039, "ТР-3", "12.2022"],
        [56040, "ТР-3", "12.2022"],
        [57039, "ТР-3", "12.2022"],
        [57040, "ТР-3", "12.2022"],
        [58039, "ТР-3", "12.2022"],
        [58040, "ТР-3", "12.2022"],

        [22099, "ТР-3", "12.2022"],
        [22100, "ТР-3", "12.2022"],
        [23139, "ТР-3", "12.2022"],
        [23140, "ТР-3", "12.2022"],
        [24099, "ТР-3", "12.2022"],
        [24100, "ТР-3", "12.2022"],

        # ТР-2
        [22005, "ТР-2", "04.2022"],
        [22006, "ТР-2", "04.2022"],
        [23005, "ТР-2", "04.2022"],
        [23006, "ТР-2", "04.2022"],
        [24005, "ТР-2", "04.2022"],
        [24006, "ТР-2", "04.2022"],

        [22021, "ТР-2", "04.2022"],
        [22022, "ТР-2", "04.2022"],
        [23021, "ТР-2", "04.2022"],
        [23022, "ТР-2", "04.2022"],
        [24021, "ТР-2", "04.2022"],
        [24022, "ТР-2", "04.2022"],

        # ТР-1
        [56011, "ТР-1", "04.2022"],
        [56012, "ТР-1", "04.2022"],
        [57011, "ТР-1", "04.2022"],
        [57012, "ТР-1", "04.2022"],
        [58011, "ТР-1", "04.2022"],
        [58012, "ТР-1", "04.2022"],

        [56043, "ТР-1", "05.2022"],
        [56044, "ТР-1", "05.2022"],
        [57043, "ТР-1", "05.2022"],
        [57044, "ТР-1", "05.2022"],
        [58043, "ТР-1", "05.2022"],
        [58044, "ТР-1", "05.2022"],

        [56027, "ТР-1", "05.2022"],
        [56028, "ТР-1", "05.2022"],
        [57027, "ТР-1", "05.2022"],
        [57028, "ТР-1", "05.2022"],
        [58027, "ТР-1", "05.2022"],
        [58028, "ТР-1", "05.2022"],
    ]
    return services


def select_idle_wagons(date: datetime.date):
    """
    Выбирает из общего списка вагоны всех сцепов, не находящиеся в движении
    (то есть находящиеся на ТОиР или в отстое) в указанную дату
    Возвращает словарь вида {дата: {номер_сцепа: {номер_вагона: причина_простоя}}}
    """
    res = {}
    for train in Registry.trains.values():
        train_number = train.train_number
        for wagon in train.wagons.values():
            wagon_number = wagon.wagon_number
            if date in wagon.mileage:
                idle_reason = wagon.mileage[date]["idle_reason"]
                if idle_reason is not None:
                    res[date] = res.get(date, {})
                    res[date][train_number] = res[date].get(
                        train.train_number, {})
                    res[date][train_number][wagon_number] = idle_reason
    return res


def select_current_idle_end(idle_wagons: dict):
    """
    Получает словарь вагонов, не находящихся в движении
    (то есть находящиеся на ТОиР или в отстое)
    вида {дата: {номер_сцепа: {номер_вагона: причина_простоя}}}
    Запрашивает у пользователя для каждого вагона ввод даты начала движения
    Возвращает список словарей вида [{номер_вагона: {причина_простоя: (дата_начала, дата_конца)}}]
    """
    # def ask_date(usage_start_date: datetime.date,
    #              usage_end_date: datetime.date):
    #     """
    #     Получает даты начала и конца эксплуатации сцепа/вагона.
    #     Запрашивает у пользователя ввод даты в формате "ДД.ММ.ГГГГ"
    #     После выполнения проверок корректности ввода возвращает дату
    #     типа datetime.date.
    #     """
    #     while True:
    #         date_for_check = input(
    #             "Введите дату начала эксплуатации с пассажирами в формате ДД.ММ.ГГГГ:\n")
    #         if not date_for_check:
    #             print("Повторите ввод. Пустой ввод недопустим!")
    #             continue
    #         try:
    #             service_end_date = datetime.datetime.strptime(
    #                 date_for_check, "%d.%m.%Y").date()
    #             if usage_start_date < service_end_date <= usage_end_date:
    #                 if Registry.planning_start_date < service_end_date <= Registry.planning_end_date:
    #                     break
    #                 else:
    #                     print("Повторите ввод. Вводимая дата должна",
    #                           "находиться в диапазоне планирования!")
    #             else:
    #                 print("Повторите ввод. Вводимая дата должна",
    #                       "находиться в диапазоне эксплуатации вагона!")
    #         except ValueError:
    #             print(f"Повторите ввод! Дата должна быть введена в формате ДД.ММ.ГГГГ!")
    #     return service_end_date

    # print("Для корректного выполнения расчета обслуживаний и ремонтов ",
    #       "необходимо для каждого сцепа (вагона), находящегося на дату ", "\n",
    #       "начала расчета в обслуживании/ремонте/отстое, указать дату ",
    #       "предполагаемого начала эксплуатации на линии с пассажирами.", sep="")
    # res = {}
    # for service_start_date, trains_data in idle_wagons.items():
    #     print(f"На дату {str(service_start_date)}")
    #     for train_number, wagons_data in trains_data.items():
    #         train_object = Registry.trains[train_number]
    #         if train_object.simultaneous_service:
    #             services = {trains_data[train_number].get(wagon_number)
    #                         for wagon_number in train_object.wagons.keys()}
    #             if len(services) > 1:
    #                 raise ValueError(f"В сцепе № {train_number} с посоставным способом ремонта",
    #                                  f"на дату {service_start_date} установлены различные виды ремонта для вагонов:",
    #                                  f"{sorted([wagon_number for wagon_number in train_object.wagons.keys()])}!")
    #             idle_reason = services.pop()
    #             res[idle_reason] = res.get(idle_reason, {})
    #             print(f"    Cцеп № {train_number} из вагонов",
    #                   f"{sorted([wagon_number for wagon_number in train_object.wagons.keys()])}",
    #                   f"находится в {idle_reason if idle_reason != 'o' else 'отстое'}.")
    #             train_usage_start_date = {wagon_object.usage_start_date
    #                                       for wagon_object in train_object.wagons.values()}
    #             train_usage_end_date = {wagon_object.usage_end_date
    #                                     for wagon_object in train_object.wagons.values()}
    #             if (len(train_usage_start_date) > 1 or
    #                     len(train_usage_end_date) > 1):
    #                 raise ValueError(f"В сцепе № {train_number} с посоставным способом ремонта",
    #                                  f"установлены различные периоды эксплуатации для вагонов:",
    #                                  f"{sorted([wagon_number for wagon_number in train_object.wagons.keys()])}!")
    #             train_usage_start_date = train_usage_start_date.pop()
    #             train_usage_end_date = train_usage_end_date.pop()
    #             service_end_date = ask_date(train_usage_start_date,
    #                                         train_usage_end_date)
    #             res[idle_reason][(service_start_date, service_end_date)] = res[idle_reason].get(
    #                 (service_start_date, service_end_date), {"trains": []})
    #             res[idle_reason][(service_start_date, service_end_date)]["trains"].append(
    #                 train_object)
    #         else:
    #             for wagon_number, idle_reason in wagons_data.items():
    #                 res[idle_reason] = res.get(idle_reason, {})
    #                 print(f"    Вагон № {wagon_number} сцепа № {train_number}"
    #                       f"находится в {idle_reason if idle_reason != 'o' else 'отстое'}.")
    #                 wagon_object = Registry.wagons[wagon_number]
    #                 service_end_date = ask_date(wagon_object.usage_start_date,
    #                                             wagon_object.usage_end_date)
    #                 res[idle_reason][(service_start_date, service_end_date)] = res[idle_reason].get(
    #                     (service_start_date, service_end_date), {"single_wagons": []})
    #                 res[idle_reason][(service_start_date, service_end_date)]["single_wagons"].append(
    #                     wagon_object)
    res = {
        'tr3':  {
            (datetime.date(2022, 3, 31),
             datetime.date(2022, 5, 26)): {
                 'trains': [
                     Registry.trains[906]
                 ]
            },
            (datetime.date(2022, 3, 31),
             datetime.date(2022, 4, 11)): {
                'trains': [
                    Registry.trains[907],
                    Registry.trains[910]
                ]
            },
            (datetime.date(2022, 3, 31),
             datetime.date(2022, 4, 29)): {
                'trains': [
                    Registry.trains[901]
                ]
            },
            (datetime.date(2022, 3, 31),
             datetime.date(2022, 4, 22)): {
                'trains': [
                    Registry.trains[909]
                ]
            },
            (datetime.date(2022, 3, 31),
                datetime.date(2022, 4, 1)): {
                'trains': [
                    Registry.trains[32]
                ]
            }
        },
        'o':  {
            (datetime.date(2022, 3, 31),
             datetime.date(2022, 7, 15)): {
                 'trains': [
                     Registry.trains[904]
                 ]
            },
            (datetime.date(2022, 7, 18),
             datetime.date(2022, 8, 18)): {
                 'trains': [
                     Registry.trains[21]
                 ]
            },
            (datetime.date(2022, 9, 1),
             datetime.date(2022, 10, 15)): {
                 'trains': [
                     Registry.trains[37]
                 ]
            }
        }
    }

    return res
