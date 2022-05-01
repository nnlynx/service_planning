#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# **************************
# src/confirmation.py
# **************************

__all__ = [
    "confirm_possible_trains",
]


def confirm_possible_trains(possible_trains: dict):
    """ Получает словарь вида {порядковый_номер: [вагон1, вагон2...]}
        Запрашивает у пользователя ввод порядковых номеров предположительных сцепов,
        которые определены правильно, и должны быть сформированы.
        Возвращает список порядковых номеров сцепов из входного словаря, которые должны быть сформированы,
        или None, если передан пустой словарь.
    """
    if not len(possible_trains):
        return None
    while True:
        print("Автоматически определены вагоны, возможно составляющие один сцеп:")
        for number, wagons in possible_trains.items():
            print(f"Возможный сцеп № {number:2d}:  вагоны {wagons}")
        input_value = input(
            """Введите через пробел номера сцепов, которые определены правильно.\nЕсли таковых нет, нажмите Enter\n""")
        if not input_value:
            return None
        try:
            numbers = [int(num) for num in input_value.strip().split()]
        except ValueError:
            print(f"Должны быть введены целые числа!")
            continue
        if not all(possible_trains.get(number, False) for number in numbers):
            print(f"Должны быть введены только номера сцепов из указанных!\n")
            continue
        confirmed_trains = []
        for number in numbers:
            confirmed_trains.append(possible_trains[number])
        # print(f"Подтверждены для создания сцепы из следующих вагонов:")
        # print(*[wagons for wagons in confirmed_trains], end="\n")
        print("Будут созданы сцепы из следующих вагонов:",
              *[wagons for wagons in confirmed_trains], sep="\n", end="\n")
        confirm = input(
            "Введите YES для подтверждения или NO, чтобы ввести номера сцепов заново\n")
        if confirm.lower() == "yes":
            return confirmed_trains
        elif confirm.lower() == "no":
            continue
