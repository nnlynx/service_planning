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


class Main_parser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.raw_start_date = None
        self.wagon_attrs = {}
        self.row_count = 0
        self.th_flag = False  # Заголовок таблицы
        self.tbody_flag = False  # Ячейка строки таблицы
        self.tr_flag = False  # Строка таблицы
        self.td_flag = False  # Ячейка строки таблицы

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.tr_flag = True
        elif tag == "td":
            self.td_flag = True
        elif tag == "tbody":
            self.tbody_flag = True
        elif tag == "th":
            self.th_flag = True

    def handle_endtag(self, tag):
        if tag == "tr":
            self.tr_flag = False
            if self.tbody_flag:
                self.row_count += 1
        elif tag == "td":
            self.td_flag = False
        elif tag == "tbody":
            self.tbody_flag = False
        elif tag == "th":
            self.th_flag = False

    def handle_data(self, data):
        if self.tbody_flag:
            if self.tr_flag:
                self.wagon_attrs[self.row_count] = self.wagon_attrs.get(
                    self.row_count, [])
                if self.td_flag:
                    self.wagon_attrs[self.row_count].append(data)
        if self.th_flag:
            if (self.raw_start_date is None) and (" по " in data):
                self.raw_start_date = data[-10:]


class Extra_parser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.wagon_attrs = {}
        self.row_count = 0
        self.tbody_flag = False  # Ячейка строки таблицы
        self.tr_flag = False  # Строка таблицы
        self.td_flag = False  # Ячейка строки таблицы

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.tr_flag = True
        elif tag == "td":
            self.td_flag = True
        elif tag == "tbody":
            self.tbody_flag = True

    def handle_endtag(self, tag):
        if tag == "tr":
            self.tr_flag = False
            if self.tbody_flag:
                self.row_count += 1
        elif tag == "td":
            self.td_flag = False
        elif tag == "tbody":
            self.tbody_flag = False

    def handle_data(self, data):
        if self.tbody_flag:
            if self.tr_flag:
                self.wagon_attrs[self.row_count] = self.wagon_attrs.get(
                    self.row_count, [])
                if self.td_flag:
                    self.wagon_attrs[self.row_count].append(data)


def wagon_data_main_parser(pars_path):
    """ 
    Выполняет парсинг html-файла выгрузки из функции "Пробеги вагонов" АСУ Депо.
    Возвращает начальную даты для расчета, а также словарь 
    со списками необработанных аргументов для экземпляров класса Wagon()
    """
    with open(pars_path, mode='r', encoding='cp1251') as html_lines:
        parser = Main_parser()
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
        parser = Extra_parser()
        for line in html_lines:
            parser.feed(line.strip())
        raw_wagon_attrs = parser.wagon_attrs
        parser.close()
        return raw_wagon_attrs
