#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# **************************
# src/parsing.py
# **************************

__all__ = [
    "convert_start_date",
    "pars_wagons_data"
]

import datetime
from html.parser import HTMLParser


class TableDataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.raw_start_date = None
        self.wagon_attrs = {}
        self.row_count = 0
        self.flag = {
            "th": False,  # Заголовок таблицы
            "tbody": False,  # Таблица
            "tr": False,  # Строка таблицы
            "td": False  # Ячейка строки таблицы
        }

    def handle_starttag(self, tag, attrs):
        self.flag[tag] = True

    def handle_endtag(self, tag):
        if self.is_row_ended(tag):
            self.row_count += 1
        self.flag[tag] = False

    def handle_data(self, data):
        if self.is_header_contains_date(data):
            self.raw_start_date = data[-10:]
        if self.is_table_row():
            self.fill_wagon_attrs(data)

    def is_row_ended(self, tag):
        return tag == "tr" and self.flag["tbody"]

    def is_table_row(self):
        return self.flag["tbody"] and self.flag["tr"]

    def is_header_contains_date(self, data):
        return self.flag["th"] and (self.raw_start_date is None) and (" по " in data)

    def fill_wagon_attrs(self, data):
        self.wagon_attrs[self.row_count] = self.wagon_attrs.get(
            self.row_count, [])
        if self.flag["td"]:
            self.wagon_attrs[self.row_count].append(data)


def pars_wagons_data(pars_path):
    """ 
    Выполняет парсинг html-файла выгрузки из функции "Пробеги вагонов" (для ТР-1 - КР) или
    "Техническое обслуживание вагонов" (для ТО-2 (ТО-1 для АТП) - ТО-3 (ТО-2 для АТП)) АСУ Депо.
    Возвращает кортеж (дата, словарь) или только словарь со списками необработанных аргументов
    для создания экземпляров класса Wagon()
    """
    with open(pars_path, mode='r', encoding='cp1251') as html_lines:
        parser = TableDataParser()
        for line in html_lines:
            parser.feed(line.strip())
        raw_wagon_attrs = parser.wagon_attrs
        raw_start_date = parser.raw_start_date
        parser.close()
        if raw_start_date is None:
            return raw_wagon_attrs
        return raw_start_date, raw_wagon_attrs


def convert_start_date(raw_start_date):
    """
    Преобразует дату из строкового формата в формат datetime.date
    """
    try:
        start_date = datetime.datetime.strptime(
            raw_start_date, "%d.%m.%Y").date()
    except TypeError:
        return -1
    else:
        return start_date
