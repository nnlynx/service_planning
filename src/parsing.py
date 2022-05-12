#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# **************************
# src/parser.py
# **************************

__all__ = [
    "wagon_data_main_parser",
    "wagon_data_extra_parser"
]

import datetime
from html.parser import HTMLParser


class BaseDataParser(HTMLParser):
    def __init__(self):
        super().__init__()
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
        if self.is_table_row():
            self.fill_wagon_attrs(data)

    def is_row_ended(self, tag):
        return tag == "tr" and self.flag["tbody"]

    def is_table_row(self):
        return self.flag["tbody"] and self.flag["tr"]

    def fill_wagon_attrs(self, data):
        self.wagon_attrs[self.row_count] = self.wagon_attrs.get(
            self.row_count, [])
        if self.flag["td"]:
            self.wagon_attrs[self.row_count].append(data)


class ExtraDataParser(BaseDataParser):
    def __init__(self):
        super().__init__()
        self.raw_start_date = None

    def handle_data(self, data):
        if self.if_header_contains_date(data):
            self.raw_start_date = data[-10:]
        if self.is_table_row():
            self.fill_wagon_attrs(data)

    def if_header_contains_date(self, data):
        return self.flag["th"] and (self.raw_start_date is None) and (" по " in data)


def wagon_data_main_parser(pars_path):
    """ 
    Выполняет парсинг html-файла выгрузки из функции "Пробеги вагонов" АСУ Депо.
    Возвращает начальную даты для расчета, а также словарь 
    со списками необработанных аргументов для экземпляров класса Wagon()
    """
    with open(pars_path, mode='r', encoding='cp1251') as html_lines:
        parser = ExtraDataParser()
        for line in html_lines:
            parser.feed(line.strip())
        start_date = datetime.datetime.strptime(
            parser.raw_start_date, "%d.%m.%Y").date()
        raw_wagon_attrs = parser.wagon_attrs
        parser.close()
        return start_date, raw_wagon_attrs


def wagon_data_extra_parser(pars_path):
    """ 
    Выполняет парсинг html-файла выгрузки из функции "Техническое обслуживание вагонов" АСУ Депо.
    Возвращает словарь со списками необработанных аргументов для экземпляров класса Wagon()
    """
    with open(pars_path, mode='r', encoding='cp1251') as html_lines:
        parser = BaseDataParser()
        for line in html_lines:
            parser.feed(line.strip())
        raw_wagon_attrs = parser.wagon_attrs
        parser.close()
        return raw_wagon_attrs
