#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# **************************
# src/calculation.py
# **************************

__all__ = [
    "calculate_line_daily_mileage",
    "calculate_period_idle_max_value",
    "calculate_periods_surplus_wagons",
    "calculate_standing_dates",
    "calculate_standing_trains_wagons",
    "calculate_train_mileage_ne",
    "calculate_train_lenght",
    "calculate_transportation_values",
    "calculate_wagon_daily_mileage",
    "calculate_wagon_mileage_ne",
    "calculate_wagon_service_mileage",
    "count_idle_wagons",
    "count_wagons_in_motion",
]

import datetime
from utility import (
    check_input_dates_planning,
    check_input_dates_usage,
    daterange,
    workdayrange)
from classes import Registry


def calculate_train_lenght(hitched_wagons: dict):
    """
    Получает словарь вагонов, имеющих сцеп, вида {номер_сцепа: {номер_вагона: объект_вагона}}
    Возвращает количество вагонов в составе
    """
    trains_len = set()
    for wagons in hitched_wagons.values():
        trains_len.add(len(wagons))
    if len(trains_len) == 1:
        train_lenght = trains_len.pop()
    else:
        print(f"Лог функции calculate_train_lenght.\
                Невозможно определить количество вагонов в сцепе!")
        raise RuntimeError
    return train_lenght


def calculate_holidays(start_date: datetime.date, end_date: datetime.date):
    """
    Получает даты начала и конца расчетного периода.
    Возвращает множество дат, являющихся выходными или праздничными днями
    """
    state_holidays = ("01.01", "02.01", "03.01", "04.01", "05.01", "06.01", "07.01",
                      "08.01", "23.02", "08.03", "01.05", "02.05", "09.05", "12.06", "04.11")
    res = set()
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    for date in daterange(start_date, end_date):
        if date.strftime("%d.%m") in state_holidays:
            res.add(date)
            if date.month != 1:
                if date.isoweekday() == 7:
                    res.add(date + datetime.timedelta(days=1))
                elif date.isoweekday() == 2:
                    res.add(date - datetime.timedelta(days=1))
                    res.remove(date - datetime.timedelta(days=3))
        elif date.isoweekday() in (6, 7):
            res.add(date)
    return res


def calculate_transportation_values(*,
                                    start_date: datetime.date,
                                    end_date: datetime.date,
                                    basic_values: dict,
                                    line_motion_time: float):
    """
    Получает даты начала и конца расчета, а также словарь с парностями движения
    вида: {дата_начала_периода: {"workday": пар_поездов_будни,
                                 "holiday": пар_поездов_выходные,
                                 "max": максимальная_парность}
    Возвращает словарь с парностями на каждую дату расчетного периода вида:
    {дата: {"pairs_count_sum": суммарная_суточная_парность,
            "trains_count_max": максимальная_часовая_парность},
            "holiday": True/False}
    """
    holidays = calculate_holidays(start_date, end_date)
    res = {}
    period_start_dates = sorted(
        [period_start_date for period_start_date in basic_values.keys()])
    period_start_dates.append(end_date)
    first_date = start_date
    MINUTES_IN_HOUR = 60
    RESERVE_TRAINS = 1
    for i in range(1, len(period_start_dates)):
        pairs_count_max = basic_values[period_start_dates[i-1]]["max"]
        trains_count_max = pairs_count_max * line_motion_time / MINUTES_IN_HOUR
        int_trains_count_max = int(trains_count_max)
        if trains_count_max % int_trains_count_max:
            trains_count_max = int_trains_count_max + 1 + RESERVE_TRAINS
        else:
            trains_count_max = int_trains_count_max + RESERVE_TRAINS
        for date in daterange(first_date, end_date):
            if period_start_dates[i-1] <= date < period_start_dates[i]:
                res[date] = {"pairs_count_sum": (basic_values[period_start_dates[i-1]]["holiday"]
                                                 if date in holidays else
                                                 basic_values[period_start_dates[i-1]]["workday"]),
                             "trains_count_max": trains_count_max,
                             "holiday": True if date in holidays else False}
            else:
                first_date = date
                break
    return res


def calculate_line_daily_mileage():
    """
    Вычисляет суммарный суточный пробег по линии
    в каждую дату из периода расчета и записывает его
    в словарь вида {дата: пробег} в Registry.line_daily_mileage
    """
    PAIR = 2
    for date in daterange(Registry.planning_start_date, Registry.planning_end_date):
        Registry.line_daily_mileage[date] = Registry.transportation_values[date]["pairs_count_sum"] * \
            Registry.line_lenght * PAIR * Registry.train_lenght


def count_wagons_in_motion(start_date: datetime.date = None,
                           end_date: datetime.date = None):
    """
    Подсчитывает количество вагонов в движении (находящихся в сцепе
    и не находящихся на ТОиР или в отстое) в каждую дату из заданного периода
    и записывает его в словарь вида {дата: количество_вагонов_в_движении}
    в Registry.wagons_in_motion
    """
    start_date, end_date = check_input_dates_planning(start_date,
                                                      end_date)
    for date in daterange(start_date, end_date):
        counter = 0
        for train in Registry.trains.values():
            for wagon in train.wagons.values():
                if date in wagon.mileage:
                    if wagon.mileage[date]["idle_reason"] is None:
                        counter += 1
        Registry.wagons_in_motion[date] = counter


def count_idle_wagons(idle_reason: str,
                      start_date: datetime.date = None,
                      end_date: datetime.date = None):
    """
    Подсчитывает количество вагонов в отстое по указанной причине
    в каждую дату из заданного периода (по умолчанию - весь период планирования)
    и записывает его в словарь вида {дата: {причина_простоя: количество_вагонов}
    в Registry.idle_wagons
    """
    start_date, end_date = check_input_dates_planning(start_date,
                                                      end_date)
    for date in daterange(start_date, end_date):
        Registry.idle_wagons[date] = Registry.idle_wagons.get(date, {})
        counter = 0
        # Потом исправить, чтобы подсчет был по всем вагонам, а не только
        # по сформированным в сцепы.
        for train in Registry.trains.values():
            for wagon in train.wagons.values():
                if date in wagon.mileage:
                    if wagon.mileage[date]["idle_reason"] == idle_reason:
                        counter += 1
        Registry.idle_wagons[date][idle_reason] = counter


def calculate_wagon_daily_mileage(start_date: datetime.date = None,
                                  end_date: datetime.date = None,
                                  usage_ratio: float = 1.0):
    """
    Вычисляет суточный пробег одного вагона, находящегося в движении,
    в каждую дату из заданного периода и записывает его в словарь
    вида {дата: пробег_вагона} в Registry.wagon_daily_mileage
    """
    start_date, end_date = check_input_dates_planning(start_date,
                                                      end_date)
    for date in daterange(start_date, end_date):
        Registry.wagon_daily_mileage[date] = int(Registry.line_daily_mileage[date] * usage_ratio //
                                                 Registry.wagons_in_motion[date])


def calculate_wagon_mileage_ne(wagon_number: int,
                               start_date: datetime.date = None,
                               end_date: datetime.date = None):
    """
    Вычисляет для указанного вагона значение пробега от н.э. на каждую дату
    из заданного периода эксплуатации вагона на основании значения суточного пробега
    и пробега от н.э. на предыдущую дату
    """
    date_delta = datetime.timedelta(days=1)
    start_date, end_date = check_input_dates_usage(wagon_number,
                                                   start_date,
                                                   end_date)
    wagon_object = Registry.wagons[wagon_number]
    for date in daterange(start_date, end_date - date_delta):
        wagon_object.mileage[date + date_delta]["ne"] = (wagon_object.mileage[date]["ne"] +
                                                         wagon_object.mileage[date]["daily"])


def calculate_train_mileage_ne(start_date: datetime.date = None,
                               end_date: datetime.date = None):
    """
    Вычисляет для вагонов в движении значение пробега от н.э. на каждую дату
    из заданного периода эксплуатации вагона на основании значения суточного пробега
    и пробега от н.э. на предыдущую дату
    """
    for train in Registry.trains.values():
        for wagon_number in train.wagons.keys():
            calculate_wagon_mileage_ne(wagon_number,
                                       start_date,
                                       end_date)


def calculate_wagon_service_mileage(wagon_number: int,
                                    service_type: str,
                                    start_date: datetime.date = None,
                                    end_date: datetime.date = None,
                                    ):
    """
    Получает номер вагона, для которого в указанный период
    (если период не указан, то за весь срок эксплуатации вагона)
    расчитывает и заполняет пробеги от указанного вида ТОиР
    и от более крупных видов ТОиР
    """
    datedelta = datetime.timedelta(days=1)
    if service_type in ("tr3", "tr2", "tr1", "to3", "to2", "to1"):
        service_type = service_type
    elif service_type in ("sr", "kr"):
        service_type = "kr_sr"
    if (start_date is None or
            start_date == Registry.wagons[wagon_number].usage_start_date):
        start_date = Registry.wagons[wagon_number].usage_start_date + datedelta
    else:
        start_date = start_date
    if end_date is None:
        end_date = Registry.wagons[wagon_number].usage_end_date
    else:
        end_date = end_date
    mileage = Registry.wagons[wagon_number].mileage
    for date in daterange(start_date, end_date):
        previous_date = date - datedelta
        for service in ("kr_sr", "tr3", "tr2", "tr1", "to3", "to2", "to1"):
            if mileage[previous_date][service] is not None:
                date_service_mileage = mileage[date][service]
                if (date_service_mileage is None or
                        date_service_mileage > 0):
                    mileage[date][service] = (mileage[previous_date][service] +
                                              mileage[previous_date]["daily"])
            if service == service_type:
                break


def calculate_periods_surplus_wagons(standing_dates: dict,
                                     verbose: bool = False):
    """
    В standing_dates для каждого диапазона дат возможного выполнения ТОиР
    определяет минимальное количество вагонов сверх максимальной парности
    (т.е. которое можно поставить в ТОиР и обеспечить выдачу составов)
    и указывает его в качестве значения "surplus_wagons_count" для периода.
    Для групп периодов "main" и "extra" определяет суммарное за все диапазоны дат,
    количество вагонов, которое можно поставить в ТОиР посоставно, и указывает его
    в качестве значения "available_train_services_count" для каждой группы периодов.
    """
    pair_trains = 2
    for delta, priorities in standing_dates.items():
        for priority, priority_data in priorities.items():
            standing_dates[delta][priority]["available_train_services_count"] = 0
            for period in sorted(priority_data["periods"].keys()):
                start_date, end_date = period
                daily_surplus_wagons = []
                for date in workdayrange(start_date, end_date):
                    max_date_pairs = Registry.transportation_values[date]["trains_count_max"]
                    wagons_in_motion = Registry.wagons_in_motion[date]
                    calc_result = wagons_in_motion - max_date_pairs * \
                        pair_trains * Registry.train_lenght
                    daily_surplus_wagons.append(calc_result)
                if len(daily_surplus_wagons):
                    surplus_wagons_count = min(daily_surplus_wagons)
                    standing_dates[delta][priority]["periods"][period]["surplus_wagons_count"] = surplus_wagons_count
                    if surplus_wagons_count // Registry.train_lenght >= 1:
                        standing_dates[delta][priority]["available_train_services_count"] += surplus_wagons_count
                    if verbose:
                        if surplus_wagons_count <= 0:
                            print(f"В периоде c {start_date} по {end_date},"
                                  "минимальное количество резервных вагонов -"
                                  f"{surplus_wagons_count}!")


def calculate_period_idle_max_value(start_date: datetime.date,
                                    end_date: datetime.date,
                                    idle_reason: str,
                                    verbose: bool = False):
    """
    Определяет максимальное значение количества заданного вида ТОиР
    в указанном диапазоне дат и возвращает это максимальное значение.
    """
    start_date, end_date = check_input_dates_planning(start_date,
                                                      end_date)
    res = max(Registry.idle_wagons[date][idle_reason]
              for date in daterange(start_date, end_date))
    if verbose:
        print(f"В диапазоне {[str(start_date), str(end_date)]}",
              f"максимальное количество {idle_reason} = {res}")
    return res


def calculate_standing_dates(service_type: str,
                             service_wagons: dict):
    """
    Внутри периода планирования определяет диапазоны дат возможного выполнения ТОиР.
    Формирует файл standing_dates вида:
    standing_dates =    {
        норма_простоя_ТОиР: {
            "main": {
                "periods":  {
                    (начальная_дата, конечная дата):    {
                        "surplus_wagons_count": запас_вагонов_сверх_max_парности,
                        "single_wagons": {
                            объект_вагона: доля_пробега_от_максимальной_нормы_на_начало_периода,
                            ...           },
                        "trains": {
                            объект_сцепа: доля_пробега_от_максимальной_нормы_на_начало_периода,
                            ...    }
                                                        },
                    ...     },
                "available_train_services_count": суммарное_количество_возможных_посоставных_ТОиР_за_все_периоды
                    }
            "extra":    {
                "periods": {
                    (начальная_дата, конечная дата):    {
                        "surplus_wagons_count": запас_вагонов_сверх_max_парности,
                        "single_wagons":    {
                            объект_вагона: доля_пробега_от_максимальной_нормы_на_начало_периода,
                            ...             },
                        "trains":   {
                            объект_сцепа: доля_пробега_от_максимальной_нормы_на_начало_периода,
                            ...     }
                                                        },
                    ...     },
                "available_train_services_count": суммарное_количество_возможных_посоставных_ТОиР_за_все_периоды
                      }
                            }
    """
    from utility import workdate

    durations = {Registry.wagons[wagon_number].define_wagon_service_duration(service_type)
                 for wagon_number in service_wagons.keys()}
    standing_dates = {}
    for delta in durations:
        standing_dates[delta] = {"main": {"periods": {},
                                          "available_train_services_count": 0},
                                 "extra": {"periods": {},
                                           "available_train_services_count": 0}}
        # Для режима работы ремонтного участка 2/2
        if service_type in ("kr", "sr", "tr3"):
            # Старый вариант (цепочка непрерывных диапазонов
            # от конца периода планирования к началу)
            start_date = Registry.planning_end_date
            end_date = Registry.planning_start_date + delta
            subdelta = datetime.timedelta(days=int(delta.days/2))
            for date in daterange(start_date, end_date, -delta):
                standing_dates[delta]["main"]["periods"][(
                    date - delta, date)] = {}
                standing_dates[delta]["extra"]["periods"][(
                    date - subdelta, (date - subdelta + delta) if (date - subdelta + delta) < start_date else start_date)] = {}

            # Новый вариант (цепочка непрерывных диапазонов
            # от начала периода планирования к концу)
            # start_date = Registry.planning_start_date + delta
            # end_date = Registry.planning_end_date
            # subdelta = datetime.timedelta(days=int(delta.days/2))
            # for date in daterange(start_date, end_date - delta, delta):
            #     standing_dates[delta]["main"]["periods"][(
            #         date, date + delta)] = {}
            #     standing_dates[delta]["extra"]["periods"][(
            #         date + subdelta, (date + subdelta + delta) if (date + subdelta + delta) < end_date else end_date)] = {}
        # Для режима работы ремонтного участка 5/2
        # elif service_type in ("tr2", "tr1", "to3", "to2, to1"):
        else:
            start_date = Registry.planning_start_date
            end_date = Registry.planning_end_date
            nextday = datetime.timedelta(days=1)
            date = start_date
            while True:
                if date >= end_date:
                    break
                date_is_holiday = Registry.transportation_values[date]["holiday"]
                last_date = workdate(date, delta)
                if not date_is_holiday:
                    if last_date is not None:
                        if date.month == last_date.month or\
                                last_date.day == 1:
                            standing_dates[delta]["main"]["periods"][(date,
                                                                      last_date)] = {}
                            date = last_date
                        else:
                            date = datetime.date(
                                last_date.year, last_date.month, 1)
                    else:
                        break
                else:
                    date += nextday
    return standing_dates


def calculate_standing_trains_wagons(service_type,
                                     service_wagons,
                                     standing_dates,
                                     sim_service_trains,
                                     single_service_wagons):
    """
    В standing_dates для каждого диапазона дат возможного выполнения ТОиР
    определяем из service_wagons сцепы, которые должны вставать в ТОиР посоставно,
    и вагоны, которые должны вставать в ТОиР по одиночке.
    Указываем их в "trains" и "single_wagons" соответственно.
    """
    for delta, priorities in standing_dates.items():
        for priority, priority_data in priorities.items():
            for period, period_data in priority_data["periods"].items():
                start_date, end_date = period
                period_data["single_wagons"] = {}
                period_data["trains"] = {}
                for wagon_number, periods_deltas in service_wagons.items():
                    # debug
                    # if wagon_number in (56009, 56010, 57009, 57010, 58009, 58010):
                    #     print(f"Вагон № {wagon_number}, диапазоны дат начала ТОиР:"
                    #           f"{sorted([(str(datelist[0]), str(datelist[-1])) for datelist in service_wagons[wagon_number]['periods'] if len(datelist)])}")
                    if periods_deltas["delta"] == delta:
                        for dates in periods_deltas["periods"]:
                            if start_date in dates:
                                mileage = Registry.wagons[wagon_number].mileage[start_date]
                                for wagon_models, mileage_standards in Registry.mileage_standards.items():
                                    if Registry.wagons[wagon_number].wagon_model in wagon_models:
                                        max_mileage = mileage_standards[service_type]["max"]
                                serv_type = ("kr_sr"
                                             if service_type in ("kr", "sr") else
                                             service_type)
                                service_mileage = (mileage["ne"]
                                                   if mileage[serv_type] is None else
                                                   mileage[serv_type])
                                service_mileage_percentage = service_mileage / max_mileage
                                if wagon_number in single_service_wagons:
                                    period_data["single_wagons"][wagon_number] = service_mileage_percentage
                                else:
                                    train_obj = Registry.trains[Registry.wagons[wagon_number].train_number]
                                    if train_obj in sim_service_trains:
                                        train_mileage_percentage = period_data["trains"].get(
                                            train_obj)
                                        if (train_mileage_percentage is None or
                                                train_mileage_percentage < service_mileage_percentage):
                                            period_data["trains"][train_obj] = service_mileage_percentage
