#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# **************************
# src/main.py
# **************************

import datetime

from calculation import (
    calculate_line_daily_mileage,
    calculate_train_lenght,
    calculate_transportation_values
)
from changing import (
    update_wagons_attrs,
)
from classes import (
    Normatives,
    Registry
)
from confirmation import (
    confirm_possible_trains
)
from conversion import (
    convert_confirmed_trains,
    convert_preplanned_services,
    convert_wagons_attrs
)
from creation import (
    create_debug_file_output,
    create_trains,
    create_wagons
)
from normatives import (
    mileage_frequency_standards,
    service_duration_standards
)
from parsing import (
    convert_start_date,
    pars_wagons_data
)
from planning import (
    service_planning
)
from selection import (
    select_current_idle_end,
    select_extra_wagon_data_path,
    select_hitched_wagons,
    select_idle_wagons,
    select_line_motion_time,
    select_main_wagon_data_path,
    select_output_data_path,
    select_planning_end_date,
    select_possible_trains,
    select_preplanned_services,
    select_text_result_data_path,
    select_transportation_values,
    select_unhitched_wagons
)
from utility import (
    daterange,
    print_result_services_to_file
)
from verification import (
    verify_planning_results,
)

raw_start_date, raw_main_wagons_attrs = pars_wagons_data(
    select_main_wagon_data_path())

Registry.planning_start_date = convert_start_date(raw_start_date)

Registry.planning_end_date = select_planning_end_date()

Registry.mileage_standards = mileage_frequency_standards()
Registry.duration_standards = service_duration_standards()
wagons_attrs = convert_wagons_attrs(raw_main_wagons_attrs)

Registry.wagons = create_wagons(wagons_attrs,
                                start_date=Registry.planning_start_date,
                                end_date=Registry.planning_end_date)

update_wagons_attrs(pars_wagons_data(select_extra_wagon_data_path()))

hitched_wagons = select_hitched_wagons()
Registry.train_lenght = calculate_train_lenght(hitched_wagons)
Registry.unhitched_wagons = select_unhitched_wagons()
possible_trains = select_possible_trains()
confirmed_trains = confirm_possible_trains(possible_trains)
Registry.trains = create_trains(
    Registry.train_lenght, hitched_wagons, verbose=False)
if not confirmed_trains is None:
    Registry.trains.update(create_trains(
        Registry.train_lenght, convert_confirmed_trains(confirmed_trains)))

Registry.transportation_values = calculate_transportation_values(
    start_date=Registry.planning_start_date,
    end_date=Registry.planning_end_date,
    basic_values=select_transportation_values(),
    line_motion_time=select_line_motion_time())

calculate_line_daily_mileage()

for wagon_number, wagon_object in Registry.wagons.items():
    serv_date = Registry.wagons[wagon_number].usage_start_date
    wagon_object.change_idle_reason(serv_date,
                                    wagon_object.define_service_type(
                                        serv_date),
                                    verbose=False)

for train_object in Registry.trains.values():
    if not train_object.verify_wagons_idle_reasons(Registry.planning_start_date,
                                                   verbose=False):
        train_object.unify_train_service_type(Registry.planning_start_date,
                                              verbose=False)

# Проставляем на начало расчета отстой сцепу №904 (56009-56010) по ремонту редукторов
# ТОЛЬКО ДЛЯ РАСЧЕТА ОТ 31.03.2022!!!
for wagon_object in Registry.trains[904].wagons.values():
    wagon_object.change_idle_reason(Registry.planning_start_date,
                                    "o",
                                    verbose=False)

Registry.result_services = select_current_idle_end(
    select_idle_wagons(Registry.planning_start_date))

# Вносим в расчет информацию о выходе из ТОиР вагонов,
# находящихся в ТОиР на дату начала расчета
for service_type, periods in Registry.result_services.items():
    for (start_date, end_date), rolling_stock_data in periods.items():
        first_date = start_date + datetime.timedelta(days=1)
        for rolling_stock_type, objects in rolling_stock_data.items():
            for rolling_stock_object in objects:
                if rolling_stock_type == "trains":
                    for wagon_object in rolling_stock_object.wagons.values():
                        for date in daterange(first_date, end_date):
                            wagon_object.change_idle_reason(date,
                                                            service_type,
                                                            verbose=False)
                if rolling_stock_type == "single_wagons":
                    for date in daterange(first_date, end_date):
                        rolling_stock_object.change_idle_reason(date,
                                                                service_type,
                                                                verbose=False)

converted_preplanned_services = convert_preplanned_services(
    select_preplanned_services())
# print(converted_preplanned_services)  # debug
# Вносим в расчет информацию о предзапланированных ТОиР
for wagon_number, services in converted_preplanned_services.items():
    Registry.wagons[wagon_number].preplanned_services = services

service_types = (  # "sr",
    "tr3",
    "tr2",
    "tr1",
    # "to2",
    # "to1"
)

service_planning(service_types)
verify_planning_results(service_types)

create_debug_file_output(select_output_data_path())
print_result_services_to_file(select_text_result_data_path())

print("END")

# Откорректировать метод verify_wagons_idle_reasons для Train
