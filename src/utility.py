#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# **************************
# src/utility.py
# **************************

__all__ = [
    "daterange",
    "check_input_dates_planning",
    "check_input_dates_usage",
    "print_result_services_to_file",
    "print_service_wagons_to_file",
    "print_standing_dates_to_file",
    "workdate",
    "workdayrange"
]

import datetime


def daterange(start_date: datetime.date,
              end_date: datetime.date,
              delta: datetime.timedelta = datetime.timedelta(days=1)):
    """
    Генерирует даты из диапазона от start_date (включая) до end_date (не включая)
    с шагом delta. Аналог range для дат.
    """
    from math import ceil
    if isinstance(start_date, datetime.date) and \
            isinstance(end_date, datetime.date):
        if isinstance(delta, datetime.timedelta):
            if not delta.days:
                raise ValueError("Значение шага не должно быть равно нулю!")
            dur = (end_date - start_date).days
            if (dur > 0 and delta.days > 0) or \
                    (dur < 0 and delta.days < 0):
                res_date = start_date
                count = ceil(abs(dur/delta.days))
                for i in range(count):
                    yield res_date
                    res_date += delta
            elif not dur:
                pass
            else:
                print("Неверно указан знак шага")
        else:
            raise TypeError("Шаг должен быть типа datetime.timedelta!")
    else:
        raise TypeError(
            "Даты начала и конца диапазона должны быть типа datetime.date!")


def workdayrange(start_date: datetime.date,
                 end_date: datetime.date,
                 delta: datetime.timedelta = datetime.timedelta(days=1)):
    """
    Генерирует рабочие даты из диапазона от start_date (включая) до end_date (не включая)
    с шагом delta. Аналог range для рабочих дней.
    """
    from classes import Registry
    if isinstance(start_date, datetime.date) and \
            isinstance(end_date, datetime.date):
        if isinstance(delta, datetime.timedelta):
            if not delta.days:
                raise ValueError("Значение шага не должно быть равно нулю!")
            dur = (end_date - start_date).days
            res_date = start_date
            count = 0
            if dur > 0 and delta.days > 0:
                while res_date < end_date:
                    if not Registry.transportation_values[res_date]["holiday"]:
                        if count % delta.days == 0:
                            yield res_date
                        count += 1
                    res_date += datetime.timedelta(days=1)
            elif dur < 0 and delta.days < 0:
                while res_date > end_date:
                    if not Registry.transportation_values[res_date]["holiday"]:
                        if count % delta.days == 0:
                            yield res_date
                        count -= 1
                    res_date -= datetime.timedelta(days=1)
            elif not dur:
                pass
            else:
                print("Неверно указан знак шага")
        else:
            raise TypeError("Шаг должен быть типа datetime.timedelta!")
    else:
        raise TypeError(
            "Даты начала и конца диапазона должны быть типа datetime.date!")


def workdate(start_date: datetime.date, delta: datetime.timedelta):
    """
    Возвращает дату, которая будет через delta рабочих дней после start_date.
    (start_date включается, end_date не включается).
    """
    from classes import Registry
    days = delta.days
    if days > 0:
        res_date = start_date
        count = 0
        while count < days:
            current_date = Registry.transportation_values.get(res_date)
            if current_date is not None:
                if not current_date["holiday"]:
                    count += 1
            else:
                return None
            res_date += datetime.timedelta(days=1)
        return res_date
    else:
        raise ValueError("Значение шага должно быть больше нуля!")


def print_standing_dates_to_file(standing_dates: dict,
                                 debug_file_path,
                                 delta: datetime.date = None,
                                 priority: str = None,
                                 priority_data: dict = None):
    """
    Выводит на печать информацию из standing_dates
    """
    from classes import Registry

    def subfunc(standing_dates: dict,
                delta: datetime.date,
                priority: str,
                priority_data: dict,
                debug_file_path):
        with open(debug_file_path, mode="at", encoding="utf-8") as debug_file:
            print("*****Начало выгрузки print_standing_dates_to_file*****",
                  file=debug_file)
            print(f"Норма простоя: {delta.days} дней. ",
                  f"В {'основные' if priority == 'main' else 'дополнительные'} периоды "
                  f"возможных ТОиР суммарно: ",
                  f"{priority_data['available_train_services_count']}", sep="", file=debug_file)
            for period, period_data in sorted(priority_data["periods"].items()):
                if period_data['surplus_wagons_count'] // Registry.train_lenght >= 1:
                    if (len(period_data["trains"]) or
                            len(period_data["single_wagons"])):
                        print(f"    Период: {[str(date) for date in period]}. Возможна постановка ",
                              f"в ТОиР {period_data['surplus_wagons_count']} ",
                              "вагонов.", sep="", file=debug_file)
                        for unit, unit_data in period_data.items():
                            if unit == "single_wagons":
                                for wagon_number, wagon_mileage in unit_data.items():
                                    print(f"        Вагон {wagon_number}, "
                                          f"доля пробега от максимальной нормы на начало периода {wagon_mileage}", sep="", file=debug_file)
                            elif unit == "trains":
                                for train_obj, train_mileage in sorted(unit_data.items()):
                                    print(f"        Сцеп {train_obj.train_number:3d} из вагонов ",
                                          f"{sorted([wag_num for wag_num in train_obj.wagons.keys()])}, ",
                                          f"доля пробега от максимальной нормы на начало периода {train_mileage}", sep="", file=debug_file)
    if (delta is None and
        priority is None and
            priority_data is None):
        for delta, priorities in standing_dates.items():
            for priority, priority_data in priorities.items():
                subfunc(standing_dates,
                        delta,
                        priority,
                        priority_data,
                        debug_file_path)
    else:
        subfunc(standing_dates,
                delta,
                priority,
                priority_data,
                debug_file_path)


def print_result_services_to_file(result_file_path):
    """
    Выводит на печать информацию обо всех ТОиР в периоде планирования.
    Вывод отсортирован по дате окончания ТОиР.
    """
    from classes import Registry
    delta = datetime.timedelta(days=1)
    current_month_year = ""
    with open(result_file_path, mode="wt", encoding="utf-8") as result_file:
        for service_type, service_data in Registry.result_services.items():
            print(f"ЗАПЛАНИРОВАННЫЕ {service_type}:", file=result_file)
            for (start_date, end_date), period_data in sorted(service_data.items(),
                                                              key=lambda x: x[0][1]):
                period_month_year = (end_date - delta).strftime("%Y.%m")
                if period_month_year != current_month_year:
                    current_month_year = period_month_year
                    print("Год, месяц окончания:",
                          f"{current_month_year}", file=result_file)
                for rolling_stock_type, objects in sorted(period_data.items(), reverse=True):
                    if len(objects):
                        print(
                            f"    Период: {str(start_date)} - {str(end_date - delta)}:", file=result_file)
                        for rolling_stock_object in objects:
                            if rolling_stock_type == 'trains':
                                print(f"        Сцеп № {rolling_stock_object.train_number:3d},",
                                      f"вагоны {sorted([wagon_number for wagon_number in rolling_stock_object.wagons.keys()])}.", file=result_file)
                            elif rolling_stock_type == 'wagons':
                                print(
                                    f"        Вагон № {rolling_stock_object.wagon_number:5d}", file=result_file)


def print_service_wagons_to_file(service_wagons: dict,
                                 service_type: str,
                                 sim_service_trains: list,
                                 single_service_wagons: list,
                                 debug_file_path):
    """
    Выводит в файл информацию из service_wagons.
    Для сцепов с посоставным ремонтом вывод сгруппирован по сцепам.
    service_wagons = {
    номер_вагона: {
        "periods":  [
            [список_дат_ТОиР],
            ...     ],
        "delta": норма_простоя_на_ТОиР
                  }
                 }
    """
    with open(debug_file_path, mode="at", encoding="utf-8") as debug_file:
        print("*****Начало выгрузки print_service_wagons_to_file*****", file=debug_file)
        for train_object in sorted(sim_service_trains):
            if all([service_wagons.get(wagon_number) is not None for wagon_number in train_object.wagons.keys()]):
                print(f"Вид ТОиР: {service_type}, сцеп № {train_object.train_number}",
                      f"из вагонов {sorted([wagon_number for wagon_number in train_object.wagons.keys()])}.",
                      "\n", f"диапазоны дат начала ТОиР: {sorted([(str(datelist[0]), str(datelist[-1])) for datelist in service_wagons[min([wagon_number for wagon_number in train_object.wagons.keys()])]['periods'] if len(datelist)])}", file=debug_file)
        for wagon_object in single_service_wagons:
            if service_wagons.get(wagon_object.wagon_number) is not None:
                print(f"Вид ТОиР: {service_type}, вагон № {wagon_object.wagon_number}", "\n",
                      f"диапазоны дат начала ТОиР: {sorted([(str(datelist[0]), str(datelist[-1])) for datelist in service_wagons[wagon_object.wagon_number]['periods'] if len(datelist)])}", file=debug_file)


def check_input_dates_planning(start_date: datetime.date,
                               end_date: datetime.date):
    """
    Проверяет переданные границы диапазона на попадание
    в границы периода планирования.
    Возвращает значения начала и конца периода.
    """
    from classes import Registry

    planning_start_date = Registry.planning_start_date
    planning_end_date = Registry.planning_end_date
    if end_date is None:
        end_date = planning_end_date
    else:
        if planning_start_date <= end_date <= planning_end_date:
            end_date = end_date
        else:
            raise ValueError(f"Дата {end_date} находится вне диапазона",
                             f"{planning_start_date} - {planning_end_date}")
    if start_date is None:
        start_date = planning_start_date
    else:
        if planning_start_date <= start_date <= end_date:
            start_date = start_date
        else:
            raise ValueError(f"Дата {start_date} находится вне диапазона",
                             f"{planning_start_date} - {planning_end_date}")

    return start_date, end_date


def check_input_dates_usage(wagon_number: int,
                            start_date: datetime.date,
                            end_date: datetime.date):
    """
    Проверяет переданные границы диапазона на попадание
    в границы периода эксплуатации вагона.
    Возвращает значения начала и конца периода.
    """
    from classes import Registry

    usage_start_date = Registry.wagons[wagon_number].usage_start_date
    usage_end_date = Registry.wagons[wagon_number].usage_end_date
    if end_date is None:
        end_date = usage_end_date
    else:
        if usage_start_date <= end_date <= usage_end_date:
            end_date = end_date
        else:
            raise ValueError(f"Дата {end_date} находится вне диапазона",
                             f"{usage_start_date} - {usage_end_date}!")
    if start_date is None:
        start_date = usage_start_date
    else:
        if usage_start_date <= start_date <= end_date:
            start_date = start_date
        else:
            raise ValueError(f"Дата {start_date} находится вне диапазона",
                             f"{usage_start_date} - {usage_end_date}!")
    return start_date, end_date
