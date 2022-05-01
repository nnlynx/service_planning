#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# **************************
# src/definition.py
# **************************

__all__ = [
    "define_periods_startdates",
    "define_wagons_outside_service_periods"
]

import datetime
from classes import Registry


def define_periods_startdates(standing_dates: dict):
    """
    Определяет даты начала каждого из периодов в standing_dates.
    Возвращает словарь этих дат вида {норма_простоя_на_ТОиР: [список_дат_начала_периода_ТОиР]}.
    """
    res = {}
    for delta, priorities in standing_dates.items():
        res[delta] = res.get(delta, [])
        for priority_data in priorities.values():
            for start_date, end_date in priority_data["periods"].keys():
                res[delta].append(start_date)
    for delta in res.keys():
        res[delta].sort()
    return res


def define_wagons_outside_service_periods(service_wagons: dict,
                                          standing_dates: dict,
                                          service_type: str):
    """
    Определяет в service_wagons вагоны, не попадающие
    ни в один из периодов в standing_dates.
    Изменяет периоды возможных дат постановки в ТОиР для таких вагонов,
    проставляет отстой до ближайшей возможной даты постановки вагона в ТОиР.
    """
    from calculation import calculate_wagon_mileage_ne, calculate_wagon_service_mileage
    from changing import change_idle_reason
    from utility import daterange

    for wagon_number in service_wagons.keys():
        delta = service_wagons[wagon_number]["delta"]
        for period in service_wagons[wagon_number]["periods"]:
            periods_startdates = define_periods_startdates(
                standing_dates)[delta]
            for startdate in periods_startdates:
                if startdate in period:
                    break
                nearly_startdate = Registry.wagons[wagon_number].define_nearly_service_startdate(service_wagons,
                                                                                                 periods_startdates)
                if nearly_startdate is not None:
                    for date in daterange(period[-1], nearly_startdate):
                        change_idle_reason(wagon_number, date, "o")
                    period.append(nearly_startdate)
        calculate_wagon_mileage_ne(wagon_number)
        calculate_wagon_service_mileage(wagon_number, service_type)
