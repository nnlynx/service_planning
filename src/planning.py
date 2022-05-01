#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# **************************
# src/planning.py
# **************************

__all__ = [
    "service_planning"
]

import datetime

from calculation import (
    calculate_period_idle_max_value,
    calculate_periods_surplus_wagons,
    calculate_standing_dates,
    calculate_standing_trains_wagons,
    calculate_train_mileage_ne,
    calculate_wagon_daily_mileage,
    calculate_wagon_service_mileage,
    count_idle_wagons,
    count_wagons_in_motion,
)
from changing import (
    adding_wagon_service_periods,
    change_trains_daily_mileage,
    update_wagon_service_period,
    unify_train_service_period,
)
from classes import (
    Registry
)
from definition import (
    define_periods_startdates,
    define_wagons_outside_service_periods
)
from selection import (
    select_debug_data_path,
)
from utility import (
    daterange,
    print_service_wagons_to_file,
    print_standing_dates_to_file,
    workdate,
    workdayrange
)


def service_planning(service_types):
    """
    Алгоритм распределения заданных видов ТОиР
    для всех вагонов всех сцепов в периоде планирования
    """
    count_wagons_in_motion()
    calculate_wagon_daily_mileage(usage_ratio=0.8)
    change_trains_daily_mileage()
    calculate_train_mileage_ne()

    # Для каждого вагона каждого сцепа, которому возможно выполнение вида ТОиР,
    # определяем диапазоны дат постановки вагона на это ТОиР и формируем словарь
    for service_type in service_types:
        print(f"************ РАСЧЕТ {service_type} ************")
        """
        service_wagons = {
            номер_вагона: {
                "periods":  [
                    [список_дат_ТОиР],
                    ...     ],
                "delta": норма_простоя_на_ТОиР
                          }
                         }
        """
        service_wagons = {}
        """
        sim_service_trains = [
        объект_сцепа,
        ...              ]

        single_service_wagons = [
            объект_вагона,
            ...                 ]
        """
        sim_service_trains = []  # объекты сцепов для посоставного ремонта
        single_service_wagons = []  # объекты вагонов для одиночного ремонта
        for train_object in Registry.trains.values():
            check_train_flag = True
            for wagon_number, wagon_object in train_object.wagons.items():
                if wagon_object.verify_allowed_service_period(service_type):
                    calculate_wagon_service_mileage(wagon_number, service_type)
                    # debug
                    # if wagon_number in (56009, 56010, 57009, 57010, 58009, 58010):
                    #     print(f"Вагон № {wagon_number}, пробег от ТР-3:",
                    #           f"на 2022-09-17 - {Registry.wagons[wagon_number].mileage[datetime.date(2022, 9, 17)]['tr3']},",
                    #           f"на 2022-09-21 - {Registry.wagons[wagon_number].mileage[datetime.date(2022, 9, 21)]['tr3']}.")
                    for date in daterange(wagon_object.usage_start_date,
                                          wagon_object.usage_end_date):
                        if wagon_object.verify_allowed_service_date(date, service_type):
                            adding_wagon_service_periods(wagon_number,
                                                         date,
                                                         service_wagons)
                            if check_train_flag:
                                train_object.change_service_objects_lists(sim_service_trains,
                                                                          single_service_wagons)
                                check_train_flag = False
        # debug
        print_service_wagons_to_file(service_wagons, service_type,
                                     sim_service_trains, single_service_wagons,
                                     select_debug_data_path())
        if len(service_wagons):
            Registry.result_services[service_type] = Registry.result_services.get(
                service_type, {})

        for wagon_number in service_wagons.keys():
            update_wagon_service_period(wagon_number,
                                        service_type,
                                        service_wagons)

        unify_train_service_period(sim_service_trains,
                                   service_wagons)

        # debug
        print_service_wagons_to_file(service_wagons, service_type,
                                     sim_service_trains, single_service_wagons,
                                     select_debug_data_path())

        standing_dates = calculate_standing_dates(service_type,
                                                  service_wagons)

        # Не работает! Требуется допиливание функции define_wagons_outside_service_periods
        # define_wagons_outside_service_periods(service_wagons,
        #                                       standing_dates,
        #                                       service_type)

        # count_wagons_in_motion()

        # print_service_wagons_to_file(service_wagons, service_type,
        #                              sim_service_trains, single_service_wagons,
        #                              select_debug_data_path())

        calculate_periods_surplus_wagons(standing_dates,
                                         verbose=False)
        calculate_standing_trains_wagons(service_type,
                                         service_wagons,
                                         standing_dates,
                                         sim_service_trains,
                                         single_service_wagons)
        # Определяем общее количество вагонов, которые должны вставать на ТОиР посоставно,
        # и количество вагонов, которые могут вставать на ТОиР отдельно.
        # ТРЕБУЕТСЯ ТОЛЬКО ДЛЯ ОТЛАДКИ!!!
        sim_service_wagons_count = len(
            sim_service_trains) * Registry.train_lenght
        single_service_wagons_count = len(single_service_wagons)
        # debug
        print(f"Для постановки в {service_type}: ",
              f"{sim_service_wagons_count} вагонов - партиями по {Registry.train_lenght} шт., ",
              f"{single_service_wagons_count} вагонов - поштучно.", sep="")

        count_idle_wagons(service_type)

        # ПЛАНИРОВАНИЕ
        confirmed_trains = []
        while True:
            for delta, priorities in sorted(standing_dates.items(), reverse=True):
                # Для посоставного ремонта вагонов
                for priority, priority_data in sorted(priorities.items(), reverse=True):
                    while True:
                        # debug
                        print_service_wagons_to_file(service_wagons, service_type,
                                                     sim_service_trains, single_service_wagons,
                                                     select_debug_data_path())
                        print_standing_dates_to_file(standing_dates, select_debug_data_path(),
                                                     #  delta, priority, priority_data
                                                     )
                        confirmed_trains_current_iteration = []
                        for period, period_data in sorted(priority_data["periods"].items()):
                            start_date, end_date = period
                            # debug
                            # print(f"Период: {period}")
                            if len(period_data["trains"]):
                                if period_data["surplus_wagons_count"] >= Registry.train_lenght:
                                    # Определяем максимальное количество вагонов на этом виде ТОиР
                                    # из всех периодов обоих приоритетов, кроме текущего периода
                                    current_period_max_idle_count = calculate_period_idle_max_value(start_date,
                                                                                                    end_date,
                                                                                                    service_type)
                                    other_periods_max_idle_count = 0
                                    for dates_period, dates_period_data in priority_data["periods"].items():
                                        startdate, enddate = dates_period
                                        if dates_period != period:
                                            other_periods_max_idle_count = max(other_periods_max_idle_count,
                                                                               calculate_period_idle_max_value(startdate,
                                                                                                               enddate,
                                                                                                               service_type))
                                    # Проверяем, что в этом периоде количество вагонов на этом виде ТОиР
                                    # меньше или равно максимальному количеству вагонов на этом виде ТОиР
                                    # в других периодах обоих приоритетов
                                    if current_period_max_idle_count <= other_periods_max_idle_count:
                                        sorted_trains = []
                                        # Определяем, есть ли в текущем периоде сцепы, которым предзапланировано ТОиР
                                        for train_object, percentage in period_data["trains"].items():
                                            for wagon_object in train_object.wagons.values():
                                                for subperiod in service_wagons[wagon_number]["periods"]:
                                                    if (start_date in subperiod and
                                                            wagon_object.verify_preplanned_service_date(service_type,
                                                                                                        start_date)):
                                                        preplanned_train_data = (percentage,
                                                                                 train_object)
                                                        if preplanned_train_data not in sorted_trains:
                                                            sorted_trains.append(
                                                                preplanned_train_data)
                                        # Добавляем все остальные сцепы текущего периода, кроме предзапланированного,
                                        # отсортированные по убыванию процента пробега
                                        sorted_trains.extend(sorted([(percentage, train_object)
                                                                    for train_object, percentage in period_data["trains"].items()
                                                                    if (percentage, train_object) not in sorted_trains],
                                                                    reverse=True))
                                        for train_mileage_percentage, train_object in sorted_trains:
                                            confirmed_trains_current_iteration.append(
                                                train_object)
                                            Registry.result_services[service_type][period] = Registry.result_services[service_type].get(period, {
                                                "trains": []})
                                            Registry.result_services[service_type][period]["trains"].append(
                                                train_object)
                                            # debug
                                            # if train_object == Registry.trains[6]:
                                            #     with open(select_debug_data_path(), mode="at", encoding="utf-8") as debug_file:
                                            #         print(f"Одобрен сцеп № 6. Период: {str(start_date)} - {str(end_date)}."
                                            #               f"Пробег от ТР-3: на 2024-04-21 - {Registry.wagons[56021].mileage[datetime.date(2024, 4, 21)]['tr3']},",
                                            #               f"на 2024-07-02 - {Registry.wagons[56021].mileage[datetime.date(2024, 7, 2)]['tr3']},",
                                            #               f"на 2024-07-20 - {Registry.wagons[56021].mileage[datetime.date(2024, 7, 20)]['tr3']}.",
                                            #               file=debug_file)
                                            # if train_object == Registry.trains[4]:
                                            #     with open(select_debug_data_path(), mode="at", encoding="utf-8") as debug_file:
                                            #         print(f"Одобрен сцеп № 4. Период: {str(start_date)} - {str(end_date)}."
                                            #               f"Пробег от ТР-3: на 2027-04-05 - {Registry.wagons[56017].mileage[datetime.date(2027, 4, 5)]['tr3']},",
                                            #               f"на 2027-06-26 - {Registry.wagons[56017].mileage[datetime.date(2027, 6, 26)]['tr3']},",
                                            #               f"на 2027-07-05 - {Registry.wagons[56017].mileage[datetime.date(2027, 7, 5)]['tr3']}.",
                                            #               file=debug_file)
                                            for wagon_number, wagon_object in train_object.wagons.items():
                                                # В портянке проставляем отметки выполнения вида ТОиР
                                                for date in daterange(start_date, end_date):
                                                    wagon_object.change_idle_reason(date,
                                                                                    service_type,
                                                                                    verbose=False)
                                                # В service_wagons для этого вагона убираем диапазон дат постановки в ТОиР,
                                                # из которого дата постановки выбрана
                                                for index in reversed(range(len(service_wagons[wagon_number]["periods"]))):
                                                    if start_date in service_wagons[wagon_number]["periods"][index]:
                                                        startdates_for_train_deleting = service_wagons[wagon_number]["periods"].pop(
                                                            index)
                                                        if not len(service_wagons[wagon_number]["periods"]):
                                                            service_wagons[wagon_number]["periods"].append(
                                                                [])
                                                        # debug
                                                        # print(f"Для вагона {wagon_number} удален список дат ",
                                                        #       f"{[str(date) for date in startdates_for_train_deleting]}, "
                                                        #       f"содержащий {str(start_date)}", sep="")
                                            # Удаляем объект сцепа, вагонам которого проставлена отметка о ТОиР,
                                            # из всех периодов, в которых он мог встать на ТОиР, включая итоговый принятый.
                                            for prior, prior_data in sorted(priorities.items(), reverse=True):
                                                for dates_period, dates_period_data in prior_data["periods"].items():
                                                    startdat, enddat = dates_period
                                                    if startdat in startdates_for_train_deleting:
                                                        dates_period_data["trains"].pop(
                                                            train_object, None)
                                                        # debug
                                                        # print(f"В {prior} из периода {[str(date) for date in dates_period]} ",
                                                        #       f"удален сцеп {train_object.train_number}", sep="")
                                            # Из каждого периода берем только по одному сцепу с максимальным пробегом
                                            break
                                    # debug
                                    # else:
                                    #     print(f"Для периода {[str(start_date), str(end_date)]}",
                                    #           f"{current_period_max_idle_count=}",
                                    #           f"{other_periods_max_idle_count=}")
                        count_wagons_in_motion()
                        calculate_periods_surplus_wagons(standing_dates)
                        count_idle_wagons(service_type)

                        # calculate_wagon_daily_mileage()
                        # change_trains_daily_mileage()
                        calculate_train_mileage_ne()
                        for tra_obje in Registry.trains.values():
                            for wago_nu in tra_obje.wagons.keys():
                                calculate_wagon_service_mileage(wago_nu,
                                                                service_type)

                        confirmed_trains.extend(
                            confirmed_trains_current_iteration)
                        if len(confirmed_trains_current_iteration):
                            stop_repeating_flag = False
                        else:
                            stop_repeating_flag = True
                        if stop_repeating_flag:
                            break
            for priority, priority_data in sorted(priorities.items(), reverse=True):
                for (startdate, enddate), dates_period_data in priority_data["periods"].items():
                    if len(dates_period_data["trains"]):
                        print(f"В периоде {[str(startdate), str(enddate)]}",
                              f"невозможно выполнение {service_type}",
                              f"сцепу {[unconf_train.train_number for unconf_train in dates_period_data['trains'].keys()]}. ",
                              f"Количество возможных ТОиР - {dates_period_data['surplus_wagons_count']}")
            stop_repeating_flag = True
            for tr_o in sim_service_trains:
                for wagon_numb, wagon_obj in tr_o.wagons.items():
                    periods_list = service_wagons[wagon_numb]["periods"]
                    wagon_periods_before = ([[]] if periods_list == [[]] else
                                            [[dat for dat in perd] for perd in periods_list])
                    for date in daterange(wagon_obj.usage_start_date,
                                          wagon_obj.usage_end_date):
                        if wagon_obj.verify_allowed_service_date(date, service_type):
                            adding_wagon_service_periods(wagon_numb,
                                                         date,
                                                         service_wagons)
                    wagon_periods_after = periods_list
                    # debug
                    with open(select_debug_data_path(), mode="at", encoding="utf-8") as debug_file:
                        print(f"Вагон {wagon_numb}. Периоды до добавления: {wagon_periods_before},",
                              f"Периоды после добавления: {wagon_periods_after}",
                              f"сам список: {service_wagons[wagon_numb]['periods']}", file=debug_file)
                    if (wagon_periods_after != wagon_periods_before):
                        stop_repeating_flag = False
            # debug
            # if service_type == "to1":
            print_service_wagons_to_file(service_wagons, service_type,
                                         sim_service_trains, single_service_wagons,
                                         select_debug_data_path())
            if stop_repeating_flag:
                break
            for tra_o in sim_service_trains:
                for wagon_numbe in tra_o.wagons.keys():
                    update_wagon_service_period(wagon_numbe,
                                                service_type,
                                                service_wagons)
            unify_train_service_period(sim_service_trains,
                                       service_wagons)
            calculate_standing_trains_wagons(service_type,
                                             service_wagons,
                                             standing_dates,
                                             sim_service_trains,
                                             single_service_wagons)
            # Для ремонта одиночных вагонов
            # confirmed_wagons = []
            # for priority, priority_data in sorted(priorities.items(), reverse=True):
            #     for period, period_data in sorted(priority_data["periods"].items()):
            #         pass

        # debug
        print(f"Сцепы для подтверждения: {sorted([tr.train_number for tr in sim_service_trains])},"
              f"всего: {len(sim_service_trains)}")
        print(f"Подтвержденные сцепы: {sorted([tr.train_number for tr in confirmed_trains])},",
              f"всего: {len(confirmed_trains)}")

# Разобраться с 107 и 108 строками в verification!!!
# С ними 904 сцепу назначается два периода ТР-3 - предзапланированный и начинающийся со standing_min


"""
Реализовать:
1.  Функцию, которая проставляет плановый отстой от даты достижения
    верхней границы нормы пробега до даты начала ближайшего диапазона ТОиР
    в main или extra для вагонов из define_wagons_outside_service_periods

Разобраться:
    С предпланом и отстоем:
1.  Не запланирован ТР-3 сцепу № 11 (56039-56040) - с 2022-11-10 перепробег ТР-3 (предзапланированный)
2.  Не запланирован ТР-3 сцепу № 35 (22095-22096) - с 2022-05-15 перепробег ТР-3 (предзапланированный) *
3.  Не запланирован ТР-3 сцепу №908 (22081-22082) - с 2022-05-26 перепробег ТР-3 (предзапланированный) *
4.  Не запланирован ТР-2 сцепу № 20 (22021-22022) - с 2022-04-02 перепробег ТР-2 (предзапланированный) *
    С автоматическим распределением всех ТОиР:
1.  Не запланирован ТР-3 сцепу № 35 (22095-22096) - с 2022-05-15 перепробег ТР-3 *
2.  Не запланирован ТР-3 сцепу №908 (22081-22082) - с 2022-05-27 перепробег ТР-3 *
3.  Не запланирован ТР-2 сцепу № 20 (22021-22022) - с 2022-04-02 перепробег ТР-2 *

Устранить ошибки:
1.  Неназначение ТО-1, если норматив достигается на длинных выходных,
    и в первый будний день уже получается перепробег.
    Реализовать отстой вагона до ближайшего буднего дня.
2.  При долгосрочном планировании повторное назначение ТР-3 из-за увеличения
    суточных пробегов при назначении ТОиР остальным составам.
3.  Постановка в ТР-3 с недопробегом:
    С предпланом и отстоем:
    - сцеп №  4 (56017-56018) 2023-10-03 - от ТР-1
    - сцеп № 12 (56041-56042) 2022-10-08 - от ТР-1
    - сцеп № 18 (22013-22014) 2023-12-10 - от ТР-1 *
    - сцеп № 21 (22109-22110) 2022-05-26 - от ТР-1 и ТР-2 (предзапланированный ТР-3, с отстоем) *
    - сцеп № 27 (22017-22018) 2023-12-10 - от ТР-1 *
    - сцеп № 37 (22099-22100) 2022-07-10 - от ТР-1 и ТР-2 (предзапланированный ТР-3, с отстоем) *
    - сцеп № 42 (22113-22114) 2022-05-26 - от ТР-1 и ТР-2 (предзапланированный ТР-3) *
    - сцеп № 43 (22115-22116) 2022-05-04 - от ТР-1 и ТР-2 (предзапланированный ТР-3) *
    С автоматическим распределением всех ТОиР:
    - сцеп № 15 (56035-56036) 2022-08-24 - от ТР-1 и ТР-2
    - сцеп №904 (56009-56010) 2022-07-10 - от ТР-1 и ТР-2
    - сцеп № 18 (22013-22014) 2023-12-10 - от ТР-1 *
    - сцеп № 21 (22109-22110) 2022-05-26 - от ТР-1 и ТР-2 *
    - сцеп № 27 (22017-22018) 2023-12-10 - от ТР-1 *
    - сцеп № 37 (22099-22100) 2022-07-10 - от ТР-1 и ТР-2 *
    - сцеп № 42 (22113-22114) 2022-05-26 - от ТР-1 и ТР-2 *
    - сцеп № 43 (22115-22116) 2022-05-04 - от ТР-1 и ТР-2 *
"""
