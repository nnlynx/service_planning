#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# **************************
# src/classes.py
# **************************

__all__ = [
    "Registry",
    "Train",
    "Wagon",
]

from typing import Union
import datetime


class Normatives:
    mileage_frequency_standards = {
        ("81-556", "81-556.1", "81-556.2",
         "81-557", "81-557.1", "81-557.2",
         "81-558", "81-558.1", "81-558.2",
         ): {"to1": {"min": 6_500, "max": 8_500},           # 7_500
             "to2": {"min": 70_000, "max": 80_000},         # 75_000
             "tr1": {"min": 100_000, "max": 140_000},       # 120_000
             "tr2": {"min": 215_000, "max": 265_000},       # 240_000
             "tr3": {"min": 440_000, "max": 520_000},       # 480_000
             "sr": {"min": 1_360_000, "max": 1_520_000},    # 1_440_000
             "kr": {"min": 3_500_000, "max": 5_100_000}     # 4_300_000
             },
        ("81-722", "81-722.1", "81-722.3",
         "81-723", "81-723.1", "81-723.3",
         "81-724", "81-724.1", "81-724.3"
         ): {"to1": {"min": 8_000, "max": 12_000},          # 10_000
             "to2": {"min": 60_000, "max": 80_000},         # 70_000
             "tr1": {"min": 120_000, "max": 160_000},       # 140_000
             "tr2": {"min": 240_000, "max": 320_000},       # 280_000
             "tr3": {"min": 480_000, "max": 640_000},       # 560_000
             "sr": {"min": 1_440_000, "max": 1_920_000},    # 1_680_000
             "kr": {"min": 3_500_000, "max": 5_100_000}     # 4_300_000
             }
    }
    service_duration_standards = {
        ("81-556", "81-556.1", "81-556.2",
         "81-557", "81-557.1", "81-557.2",
         "81-558", "81-558.1", "81-558.2",
         "81-722", "81-722.3",
         "81-723", "81-723.3",
         "81-724", "81-724.3"
         ): {"to1": datetime.timedelta(days=1),
             "to2": datetime.timedelta(days=2),
             "tr1": datetime.timedelta(days=3),
             "tr2": datetime.timedelta(days=5),
             "tr3": datetime.timedelta(days=45),
             "sr": datetime.timedelta(days=110),
             "kr": datetime.timedelta(days=200)
             }
    }

    @classmethod
    def calculate_standing(cls,
                           standing_min_percentage=0.6,
                           standing_max_percentage=1.0):
        """ 
        Получает процент от диапазона ТОиР, для вычисления пробега из этого диапазона,
        при котором вагону будет планироваться постановка в этот вид ТОиР.
        Добавляет на месте ключ "standing" с его значением в словарь 
        с нормативами межремонтных пробегов по видам ТОиР.
        """
        for services in cls.mileage_frequency_standards.values():
            for service_type, mileages in services.items():
                if service_type in ("sr", "kr"):
                    mileages["standing_min"] = mileages["min"]
                    mileages["standing_max"] = mileages["max"]
                else:
                    mileages["standing_min"] = int((mileages["max"] - mileages["min"]) *
                                                   standing_min_percentage + mileages["min"])
                    mileages["standing_max"] = int((mileages["max"] - mileages["min"]) *
                                                   standing_max_percentage + mileages["min"])


Normatives.calculate_standing()


class Registry:
    # длина линии в километрах
    line_lenght = 27.62
    # начальная дата расчета
    planning_start_date = None
    # конечная дата расчета (следующая за диапазоном расчета)
    planning_end_date = None
    # словарь вагонов вида {номер_вагона: объект_вагона}
    wagons = None
    # словарь сцепов вида {номер_сцепа: объект_сцепа}
    trains = None
    # количество вагонов в сцепе
    train_lenght = None
    # словарь невцепленных вагонов
    unhitched_wagons = None
    # словарь с парностями на каждую дату расчетного периода вида:
    # {дата: {"pairs_count_sum": суммарная_суточная_парность,
    #         "pairs_count_max": максимальная_часовая_парность,
    #         "holiday": True/False}}
    transportation_values = None
    # словарь с суммарным суточным пробегом линии вида {дата: пробег}
    line_daily_mileage = {}
    # словарь с суточным пробегом одного вагона в движении вида {дата: пробег}
    wagon_daily_mileage = {}
    # словарь с суточным количеством вагонов в движении вида {дата: количество}
    wagons_in_motion = {}
    # словарь с суточным количеством вагонов в простое
    # вида {дата: {причина_простоя: количество_вагонов}}
    idle_wagons = {}
    # словарь с нормами межремонтных пробегов
    mileage_standards = None
    # словарь с нормами простоя вагонов в ремонте
    duration_standards = None
    """
    словарь со всеми запланированными ТОиР по периодам вида
    result_services =   {
    вид_ТОиР:   {
        (начальная_дата, конечная дата):    {
            "trains": [объект_сцепа, ...],
            "single_wagons": [объект_вагона, ...]
                                            },
        ...     }
    ...             }
    """
    result_services = None


class Train:
    def __init__(
        self, *,
        # количество вагонов в сцепе
        train_lenght: int,
        # номерё сцепа
        train_number: int,
        # словарь вагонов, входящих в этот сцеп (вида {номер_вагона: объект_вагона})
        wagons: dict,
    ):
        # формирование поезда (какие модели могут быть)
        train_forming = (("81-556", "81-557", "81-558"),
                         ("81-556.1", "81-557.1", "81-558.1"),
                         ("81-556.2", "81-557.2", "81-558.2"),
                         ("81-722", "81-723", "81-724"),
                         ("81-722.3", "81-723.3", "81-724.3")
                         )
        unified_wagon_models = ("81-556", "81-556.1", "81-556.2",
                                "81-557", "81-557.1", "81-557.2",
                                "81-558", "81-558.1", "81-558.2",
                                "81-722", "81-722.3",
                                "81-723", "81-723.3",
                                "81-724", "81-724.3"
                                )
        self.train_lenght = train_lenght
        if any([all([wagon_object.wagon_model in models for wagon_object in wagons.values()])
                for models in train_forming]):
            self.train_number, self.wagons = train_number, wagons
        else:
            raise ValueError(f"""Лог Train.__init__
                  Невозможно создать сцеп № {train_number}!
                  Вагоны {[wagon_number for wagon_number in wagons.keys()]} несцепляемы между собой!""")
        if all([wagon_object.wagon_model in unified_wagon_models for wagon_object in self.wagons.values()]):
            self.simultaneous_service = True
        else:
            self.simultaneous_service = False

    def __lt__(self, other):
        if isinstance(other, Train):
            if self.train_number < other.train_number:
                return True
            else:
                return False
        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Train):
            if self.train_number > other.train_number:
                return True
            else:
                return False
        else:
            return NotImplemented

    def change_service_objects_lists(self,
                                     sim_service_trains: list,
                                     single_service_wagons: list):
        """
        Проверяет полученный объект класса Train на наличие отметки о посоставном ТОиР.
        При ее наличии добавляет этот объект сцепа в sim_service_trains.
        При ее отсутствии добавляет в single_service_wagons все объекты вагонов, 
        входящих в этот сцеп.
        """
        if self.simultaneous_service:
            sim_service_trains.append(self)
        else:
            for wagon_object in self.wagons.values():
                single_service_wagons.append(wagon_object)

    def verify_wagons_idle_reasons(self,
                                   date: datetime.date,
                                   verbose=False):
        """
        Для заданного номера сцепа проверяет, что у всех вагонов сцепа на указанную дату
        установлена одинаковая причина простоя.
        Возвращает bool.
        """
        reasons = {wagon_object.mileage[date]["idle_reason"]
                   for wagon_object in self.wagons.values()}
        res = all(reasons)
        if not res:
            if all(reason is None for reason in reasons):
                res = True
        if verbose:
            print(
                f"Дата: {date}, cцеп № {self.train_number}: {'ОК' if res else 'не ОК'}")
            if not res:
                print(
                    f"{[(wagon_object.wagon_number, wagon_object.mileage[date]['idle_reason']) for wagon_object in self.wagons.values()]}")
        return res

    def unify_wagons_service_type(self,
                                  date: datetime.date,
                                  verbose=False):
        """
        Для вагонов одного сцепа, у которых не установлена отметка о ТОиР,
        устанавливает отметку о ТОиР, установленную для других вагонов этого же сцепа
        """
        reasons = [(wagon_object, wagon_object.mileage[date]["idle_reason"])
                   for wagon_object in self.wagons.values()]
        none_reason_wagons = []
        true_reason = []
        for wagon_object, reason in reasons:
            if reason is None:
                none_reason_wagons.append(wagon_object)
            else:
                true_reason.append(reason)
        true_reason = set(true_reason)
        if len(true_reason) == 1:
            new_reason = true_reason.pop()
        else:
            print(f"Для вагонов сцепа №{self.train_number} установлены отметки",
                  f"о различных видах ТОиР: ",
                  f"{reasons}", sep="")
        for wagon_object in none_reason_wagons:
            wagon_object.change_idle_reason(date, new_reason, verbose=verbose)
    # Состав
    # (свои:
    # - количество вагонов в сцепе : int (задаваемое пользователем),
    # - вагонная формула формирования сцепа,
    # - номера вагонов сцепа,
    # - флаг постоянства формирования сцепа : bool (в зависимости от серии вагонов)
    # - флаг посоставного обслуживания и ремонта : bool (в зависимости от серии,
    #   изменяемый пользователем в крайних случаях),
    # )


class Wagon:
    def __init__(
        self, *,
        # дата начала эксплуатации вагона в периоде планирования (или начало периода)
        usage_start_date: datetime,
        # дата окончания эксплуатации вагона в периоде планирования - первая дата,
        # когда вагон уже не эксплуатируется (или конец периода)
        usage_end_date: datetime,
        in_train: bool,                # флаг наличия вагона в сцепе
        train_number: int,             # номер сцепа
        wagon_number: int,             # номер вагона
        production_date: str,          # дата изготовления
        wagon_model: str,              # модель вагона
        mileage_ne_0: int,             # пробег от н.э. на дату начала расчета
        mileage_kr_sr_0: int,          # пробег от КР/СР на дату начала расчета
        mileage_tr3_0: int,            # пробег от ТР-3 на дату начала расчета
        mileage_tr2_0: int,            # пробег от ТР-2 на дату начала расчета
        mileage_tr1_0: int,            # пробег от ТР-1 на дату начала расчета
        # заранее запланированные ТОиР (тип - list, вида [{вид_ТОиР: (дата_начала, дата конца)}])
        # preplanned_services=[],
    ):
        if usage_start_date < usage_end_date:
            self.default_start_date = usage_start_date
            self.default_end_date = usage_end_date
        else:
            raise ValueError(f"Лог Wagon.__init__\
                    Для вагона {wagon_number} дата начала эксплуатации больше даты окончания эксплуатации")
        self.in_train = in_train
        self.train_number = train_number
        self.wagon_number = wagon_number
        self.production_date = production_date
        self.wagon_model = wagon_model
        self.usage_start_date = usage_start_date
        self.usage_end_date = usage_end_date
        # self.preplanned_services вида {вид_ТОиР: [(дата_начала, дата_конца), ...]}
        self.preplanned_services = None
        # "daily" может быть:
        #   None - если элемент еще не заполнялся либо для элементов [:usage_start_date] и [usage_end_index:],
        #   0 - если вагон в эту дату находится на ТОиР или в отстое,
        #   int > 0 - если вагон в сцепе и эксплуатируется
        # "idle_reason" может быть:
        #   None - если ежесуточный пробег равен None или int > 0,
        #   str ("kr", "sr", "tr3", "tr2", "tr1", "o") - если ежесуточный пробег равен 0
        self.mileage = {usage_start_date: {"preplanned_service": None,
                                           "allowed_service": None,
                                           "idle_reason": None,
                                           "daily": None,
                                           "ne": mileage_ne_0,
                                           "kr_sr": mileage_kr_sr_0,
                                           "tr3": mileage_tr3_0,
                                           "tr2": mileage_tr2_0,
                                           "tr1": mileage_tr1_0,
                                           "to3": None,
                                           "to2": None,
                                           "to1": None
                                           }
                        }
        self.fill_period_mileage()

    def fill_period_mileage(self):
        from utility import daterange
        usage_second_date = self.usage_start_date + datetime.timedelta(days=1)
        for date in daterange(usage_second_date, self.usage_end_date):
            self.mileage[date] = {"preplanned_service": None,
                                  "allowed_service": None,
                                  "idle_reason": None,
                                  "daily": None,
                                  "ne": None,
                                  "kr_sr": None,
                                  "tr3": None,
                                  "tr2": None,
                                  "tr1": None,
                                  "to3": None,
                                  "to2": None,
                                  "to1": None,
                                  }

    def set_usage_start_date(self, new_date):
        if len(self.mileage) > 1:
            raise RuntimeError(
                f"Изменение даты возможно только до начала расчета!")
        if not self.default_start_date < new_date < self.default_end_date:
            raise IndexError(
                f"Введенная дата {new_date} находится вне диапазона расчета!")
        else:
            old_date = self.usage_start_date
            self.usage_start_date = new_date
            self.mileage[new_date] = self.mileage.pop(old_date)
            print(
                f"Установлено новое значение usage_start_date = {self.usage_start_date}")

    def set_usage_end_date(self, new_date):
        if len(self.mileage) > 1:
            raise RuntimeError(
                f"Изменение даты возможно только до начала расчета!")
        if not self.default_start_date < new_date < self.default_end_date:
            raise IndexError(
                f"Введенная дата {new_date} находится вне диапазона расчета!")
        else:
            old_date = self.usage_end_date
            self.usage_end_date = new_date
            print(
                f"Установлено новое значение usage_end_date = {self.usage_end_date}")

    def change_idle_reason(self,
                           date: datetime.date,
                           new_idle_reason: Union[str, None],
                           verbose=False):
        """
        Изменяет для указанного номера вагона в указанную дату
        значение причины простоя, суточного пробега,
        а при установке отметки о нахождении в ТОиР - обнуляет пробеги
        для этого и меньших видов ТОиР.
        """

        service_types = ("to1", "to2",  # "to3",
                         "tr1", "tr2", "tr3",
                         "sr", "kr")
        service = self.mileage[date]
        old_idle_reason = service["idle_reason"]
        if old_idle_reason != new_idle_reason:
            if new_idle_reason is None:
                service["idle_reason"] = None
                service["daily"] = None
                if verbose:
                    print(f"Для вагона №{self.wagon_number} на {date} ",
                          f"снята отметка о нахождении в {'отстое' if old_idle_reason == 'o' else old_idle_reason}.", sep="")
            elif new_idle_reason in service_types:
                if old_idle_reason is None:
                    service["idle_reason"] = new_idle_reason
                    service["daily"] = 0
                    for idle_reason in service_types:
                        service_type = ("kr_sr"
                                        if idle_reason in ("sr", "kr") else
                                        idle_reason)
                        service[service_type] = 0
                        if idle_reason == new_idle_reason:
                            break
                    if verbose:
                        print(f"Для вагона №{self.wagon_number} на {date} ",
                              f"установлена отметка о нахождении в {new_idle_reason} ",
                              f"взамен {old_idle_reason}.", sep="")
                else:
                    print(f"Попытка установки для вагона {self.wagon_number} на {date} ",
                          f"отметки {new_idle_reason} взамен {old_idle_reason}!", sep="")
            elif new_idle_reason == "o":
                if old_idle_reason is None:
                    service["idle_reason"] = "o"
                    service["daily"] = 0
                    if verbose:
                        print(f"Для вагона №{self.wagon_number} на {date} ",
                              f"установлена отметка о постановке в отстой.", sep="")
                elif old_idle_reason in service_types:
                    print(
                        f"Попытка постановки в отстой вагона, находящегося на {old_idle_reason}!")
        else:
            if verbose:
                print(
                    f"Для вагона №{self.wagon_number} на {date} уже стоит отметка {new_idle_reason}")

    def define_nearly_service_startdate(self,
                                        service_wagons: dict,
                                        periods_startdates: list):
        """
        Определяет для указанного вагона ближайший возможный период
        выполнения ТОиР, следующий за последней датой возможного
        выполнения ТОиР по пробегу.
        Возвращает дату начала такого периода.
        """
        nearly_startdate = None
        if service_wagons[self.wagon_number]["periods"][-1]:
            last_possible_service_date = service_wagons[self.wagon_number]["periods"][-1][-1]
            for date in periods_startdates:
                datedelta = date - last_possible_service_date
                if datedelta.days > 0:
                    nearly_startdate = date
                    break
        return nearly_startdate

    def define_service_type(self,
                            date: datetime.date):
        """
        Проверяет по пробегам вагона с указанным номером, находится ли он в указанную дату
        на каком-либо виде ТОиР
        Возвращает название вида ТОиР типа str.
        """
        service = self.mileage[date]
        if service["to1"] == 0:
            if service["to2"] == 0:
                if service["tr1"] == 0:
                    if service["tr2"] == 0:
                        if service["tr3"] == 0:
                            if service["kr_sr"] == 0:
                                return "kr_sr"
                            return "tr3"
                        return "tr2"
                    return "tr1"
                return "to2"
            return "to1"
        return None

    def define_wagon_service_duration(self,
                                      service_type: str):
        """
        Получает номер вагона и вид ТОиР.
        Определяет и возвращает норму простоя на этом виде ТОиР
        в формате datetime.timedelta(days=X)
        """
        for wagon_models, duration in Registry.duration_standards.items():
            if self.wagon_model in wagon_models:
                service_duration = duration[service_type]
        return service_duration

    def define_wagon_mileage_stardards(self):
        """
        Получает номер вагона и вид ТОиР.
        Определяет и возвращает норму простоя на этом виде ТОиР
        в формате datetime.timedelta(days=X)
        """
        for wagon_models, standards in Registry.mileage_standards.items():
            if self.wagon_model in wagon_models:
                mileage_standards = standards
        return mileage_standards

    def verify_allowed_service_date(self,
                                    date: datetime.date,
                                    service_type: str):
        """
        Проверяет по пробегам, возможно ли указанному вагону  
        в указанную дату выполнение указанного вида ТОиР 
        ("to1", "to2", "to3", "tr1, "tr2", "tr3", "sr", "kr").
        Возвращает bool
        """
        # debug
        # from selection import select_debug_data_path

        for wagon_models, standards in Registry.mileage_standards.items():
            if self.wagon_model in wagon_models:
                mileage_standards = standards
        preplanned_services = self.preplanned_services
        if (preplanned_services is not None and
                service_type in preplanned_services.keys()
                # and (any(date in daterange(startdate, enddate)
                #      for startdate, enddate in preplanned_services[service_type]))
            ):
            min_mileage = mileage_standards[service_type]["min"]
            max_mileage = mileage_standards[service_type]["max"]
        else:
            min_mileage = mileage_standards[service_type]["standing_min"]
            max_mileage = mileage_standards[service_type]["standing_max"]
        mileage_ne = self.mileage[date]["ne"]
        if service_type in ("to1", "to2", "to3", "tr1", "tr2", "tr3", "sr"):
            if service_type == "sr":
                mileage_service = self.mileage[date]["kr_sr"]
            else:
                mileage_service = self.mileage[date][service_type]
            if mileage_service is None:
                if mileage_ne < min_mileage:
                    return False
                elif mileage_ne >= min_mileage:
                    if mileage_ne <= max_mileage:
                        # debug
                        # with open(select_debug_data_path(), mode="at", encoding="utf-8") as debug_file:
                        #     print(f"Вагон {wagon_number}, дата {str(date)}: из функции ",
                        #           f"{mileage_ne} от н.э., {mileage_service} от {service_type}.",
                        #           f"Диапазон норматива: {min_mileage} - {max_mileage}",
                        #           file=debug_file)
                        return True
                    else:
                        return False
            elif mileage_service < min_mileage:
                return False
            elif min_mileage <= mileage_service <= max_mileage:
                # debug
                # with open(select_debug_data_path(), mode="at", encoding="utf-8") as debug_file:
                #     print(f"Вагон {wagon_number}, дата {str(date)}: ",
                #           f"{mileage_ne} от н.э., {mileage_service} от {service_type}.",
                #           f"Диапазон норматива: {min_mileage} - {max_mileage}",
                #           file=debug_file)
                return True
        elif service_type == "kr":
            if (self.verify_allowed_service_date(date, "sr") and
                    min_mileage <= mileage_ne <= max_mileage):
                return True
            else:
                return False

    def verify_allowed_service_period(self,
                                      service_type: str,
                                      start_date: datetime.date = None,
                                      end_date: datetime.date = None):
        """
        Получает номер вагона и наименование вида ТОиР 
        ("to1", "to2", "to3", "tr1, "tr2", "tr3", "sr", "kr").
        Проверяет, возможно ли указанному вагону выполнение указанного вида ТОиР
        за указанный период (по умолчанию - за период использования вагона).
        Возвращает bool
        """
        from utility import check_input_dates_usage

        start_date, end_date = check_input_dates_usage(self.wagon_number,
                                                       start_date,
                                                       end_date)
        date_delta = datetime.timedelta(days=1)
        for wagon_models, standards in Registry.mileage_standards.items():
            if self.wagon_model in wagon_models:
                mileage_standards = standards
        # min_mileage = mileage_standards[service_type]["min"]
        min_mileage = mileage_standards[service_type]["standing_min"]
        if start_date == self.usage_end_date:
            return False
        mileage_ne_first = self.mileage[start_date]["ne"]
        mileage_ne_last = self.mileage[end_date - date_delta]["ne"]
        mileage_period = mileage_ne_last - mileage_ne_first
        if service_type in ("sr", "kr"):
            mileage_service_first = self.mileage[start_date]["kr_sr"]
        else:
            mileage_service_first = self.mileage[start_date][service_type]
        if mileage_service_first is None:
            mileage_service_last = None
        else:
            mileage_service_last = mileage_service_first + mileage_period
        if mileage_ne_last < min_mileage:
            return False
        elif mileage_ne_last >= min_mileage:
            if mileage_service_last is None:
                return True
            else:
                if service_type == "kr":
                    # min_mileage = mileage_standards["sr"]["min"]
                    min_mileage = mileage_standards["sr"]["standing_min"]
                return True if mileage_service_last >= min_mileage else False

    def verify_preplanned_service_date(self,
                                       service_type: str,
                                       date: datetime.date):
        """
        Проверяет, что для указанного вагона указанная дата входит хотя бы
        в один из диапазонов дат начала предзапланированного вида указанного ТОиР 
        Возвращает bool
        """
        from utility import daterange

        if self.preplanned_services is None:
            return False
        else:
            if service_type in self.preplanned_services:
                for start_date, end_date in self.preplanned_services[service_type]:
                    if date in daterange(start_date, end_date):
                        return True
                return False
            else:
                return False

    def __repr__(self):
        from utility import daterange

        formatted_start_date = datetime.date.strftime(
            self.usage_start_date, "%d.%m.%Y")
        formatted_end_date = datetime.date.strftime(
            self.usage_end_date, "%d.%m.%Y")
        res = f"""
        Вагон №{self.wagon_number} модели {self.wagon_model}:
        Введен в эксплуатацию {self.production_date}
        В сцепе: {self.in_train}, № сцепа: {self.train_number}
        Эксплуатируется с {formatted_start_date} до {formatted_end_date} (не включительно)
        Ежесуточные пробеги: {[self.mileage[i]["daily"] for i in daterange(
            self.usage_start_date, (self.usage_start_date + datetime.timedelta(days=len(self.mileage))))]}
        Пробеги от н.э.: {[self.mileage[i]["ne"] for i in daterange(
            self.usage_start_date, (self.usage_start_date + datetime.timedelta(days=len(self.mileage))))]}
        Пробеги от КР/СР: {[self.mileage[i]["kr_sr"] for i in daterange(
            self.usage_start_date, (self.usage_start_date + datetime.timedelta(days=len(self.mileage))))]}
        Пробеги от ТР-3: {[self.mileage[i]["tr3"] for i in daterange(
            self.usage_start_date, (self.usage_start_date + datetime.timedelta(days=len(self.mileage))))]}
        Пробеги от ТР-2: {[self.mileage[i]["tr2"] for i in daterange(
            self.usage_start_date, (self.usage_start_date + datetime.timedelta(days=len(self.mileage))))]}
        Пробеги от ТР-1: {[self.mileage[i]["tr1"] for i in daterange(
            self.usage_start_date, (self.usage_start_date + datetime.timedelta(days=len(self.mileage))))]}
               """
        return res

    # Непосредственно конкретный вагон конкретной модели
    # (свои:
    # - тип вагона : str (неизменяемый, Г/ПМ/ПБ)
    # + даты начала и окончания расчета пробегов для ТОиР : datetime.date
    #   (неизменяемые),
    # + флаг резервности : bool (для перецепляемых серий вагонов)
    #   при непосоставном обслуживании и ремонте),
    # )
