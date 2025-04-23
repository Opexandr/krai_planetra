from copy import deepcopy
from datetime import date, timedelta, datetime
from collections import namedtuple, defaultdict

from docs.database import Serialize, get_table_data
from docs.classes.singleton_meta_class import SingletonMeta
from docs.utils import print_red


machine_usage_tuple = namedtuple("machine_usage_tuple","start end boots_id position_id string_color")


class CalendarBase(metaclass=SingletonMeta):
    """Базовый класс для календарей оборудования и работников"""

    def __init__(self):
        self.__get_period()
        self.total_work_hours = None
        self.max_shift = None
        self.max_date = Serialize.start_date + timedelta(days=self.period)
        self.calendar_copy = None
        self.calendar = None
        self.name = None

    def __get_period(self):
        """Задает горизонт планирования"""
        match Serialize.get_command():
            case "Трехмесячный оптимизатор":
                self.period = 100
            case "Недельный оптимизатор":
                self.period = 7
            case _:
                self.period = None
        return

    def reset_calendar(self):
        self.calendar = {}
        self.calendar_copy = self.calendar.copy()
        self.max_date = Serialize.start_date + timedelta(days=self.period)
        self.max_shift = {}
        self.total_work_hours = 0.0
        self.__get_period()
        return

    @staticmethod
    def _get_cal_dict(cls):
        obj_cal_list: list = get_table_data(cls, cls.id > 0)
        obj_cal_dict = defaultdict(dict)

        for c_obj in obj_cal_list:
            if not c_obj.duration or c_obj.duration <= 0.0:
                continue
            duration = (c_obj.date_end - c_obj.date_start).total_seconds()
            obj_cal_dict[c_obj.calendar_id][(c_obj.date_start.date(), c_obj.shift)] = \
                {
                    "time_total": duration,
                    "time_usage": 0.0,
                    "period": (c_obj.date_start, c_obj.date_end),
                    "machine_usage": [],
                    "free_time": [(c_obj.date_start,
                                   c_obj.date_end,
                                   duration)],
                }

        return obj_cal_dict

    def _calendar_expansion(self):
        if self.period is not None:
            for id_obj, value in self.calendar.items():
                max_date = max(value)[0]
                while (max_date - Serialize.start_date.date()).days + 1 < self.period:
                    max_date += timedelta(days=1)
                    date_for_copy = max_date - timedelta(days=7)
                    shift = 1
                    while self.calendar[id_obj].get((date_for_copy, shift)):
                        self.calendar[id_obj][max_date, shift] = (
                            deepcopy(self.calendar[id_obj][date_for_copy, shift]))
                        shift += 1
        return

    def _get_element(self, id_obj, cal_date, shift, element):
        """
        Возвращает заданный элемент данного дня, данной смены, данного оборудования
        :param id_obj: Индекс соответствующего объекта
        :type id_obj: int
        :param cal_date: Дата формата ``date``
        :type cal_date: date
        :param shift: Рабочая смена
        :type shift: int
        :param element: Один из элементов данного списка:
         ``time_total time_usage period machine_usage free_time``
        :type element: str
        :returns: Значение для данного элемента в календаре или ``None``,
         если такой элемент отсутствует в календаре
        """

        cal_elem = self.calendar[id_obj][(cal_date, shift)].get(element)
        if cal_elem is None:
           print_red(f"!!!НЕПРАВИЛЬНОЕ НАЗВАНИЕ ЭЛЕМЕНТА В {self.name}!!!")
        return cal_elem

    def get_free_time(self, id_obj, cal_date, shift) -> list[tuple[datetime, datetime, float]]:
        """
        Возвращает свободные промежутки времени работы машины заданного дня
        :param id_obj: Индекс соответствующего объекта
        :type id_obj: int
        :param cal_date: Дата формата ``date``
        :type cal_date: date
        :param shift: Рабочая смена
        :type shift: int
        :returns: Возвращает список следующего формата:
        [(``start_datetime``, ``end_datetime``, ``duration_float``),]
        """
        if self.calendar.get(id_obj) is None or self.calendar[id_obj].get((cal_date, shift)) is None:
            return []
        return self._get_element(id_obj, cal_date, shift, "free_time")

    def get_time_total(self, id_obj, cal_date, shift) -> float:
        """
        Возвращает общее время работы машины для заданного дня
        :param id_obj: Индекс соответствующего объекта
        :type id_obj: int
        :param cal_date: Дата формата ``date``
        :type cal_date: date
        :param shift: Рабочая смена
        :type shift: int
        :returns: Возвращает время формата ``float``
        """
        return self._get_element(id_obj, cal_date, shift, "time_total")

    def get_time_usage(self, id_obj, cal_date, shift) -> float:
        """
        Возвращает уже использованное время заданного дня
        :param id_obj: Индекс соответствующего объекта
        :type id_obj: int
        :param cal_date: Дата формата ``date``
        :type cal_date: date
        :param shift: Рабочая смена
        :type shift: int
        :returns: Возвращает время формата ``float``
        """
        return self._get_element(id_obj, cal_date, shift, "time_usage")

    def get_period(self, id_obj, cal_date, shift) -> tuple[datetime, datetime]:
        """
        Возвращает период работы машины заданного дня
        :param id_obj: Индекс соответствующего объекта
        :type id_obj: int
        :param cal_date: Дата формата ``date``
        :type cal_date: date
        :param shift: Рабочая смена
        :type shift: int
        :returns: Возвращает кортеж формата (``start``, ``end``)
        """
        return self._get_element(id_obj, cal_date, shift, "period")

    def get_machine_usage(self, id_obj, cal_date, shift) \
            -> list[machine_usage_tuple[datetime, datetime, int, int, str]]:
        """
        Возвращает занятые промежутки времени работы машины заданного дня
        :param id_obj: Индекс соответствующего объекта
        :type id_obj: int
        :param cal_date: Дата формата ``date``
        :type cal_date: date
        :param shift: Рабочая смена
        :type shift: int
        :returns: Возвращает список следующего формата:
        [(``start end boots_id position_id string_color``),]
        """
        return self._get_element(id_obj, cal_date, shift, "machine_usage")

    def get_shifts(self, machine_group: int, c_date: date) -> list[int]:
        """
        Возвращает отсортированный по дате начала смены список смен
        :param machine_group: Индекс группы машин
        :param c_date: Дата формата ``date``
        :return: Отсортированный список формата [``shift1_int shift2_int ...``]
        """
        if self.max_shift.get((machine_group, c_date)):
            return [x[0] for x in self.max_shift[machine_group, c_date]]
        else:
            return []

    def __free_time(self, id_obj, cal_date, shift) -> list[tuple[datetime, datetime, float]]:
        """Возвращает свободные промежутки использования машины в заданный день
        :param id_obj: Индекс соответствующего объекта
        :type id_obj: int
        :param cal_date: Дата формата ``date``
        :type cal_date: date
        :param shift: Рабочая смена
        :type shift: int
        """
        free_time = []
        free_end = self.calendar[id_obj][(cal_date, shift)]["period"][0]
        end_shift = self.calendar[id_obj][(cal_date, shift)]["period"][1]

        for start_usage, end_usage, _, _, _ in self.calendar[id_obj][(cal_date, shift)]["machine_usage"]:
            if start_usage == free_end:
                free_end = end_usage
            else:
                duration = (start_usage - free_end).total_seconds()
                free_time.append((free_end, start_usage, duration))
                free_end = end_usage

        if free_end < end_shift:
            duration = (end_shift - free_end).total_seconds()
            free_time.append((free_end, end_shift, duration))

        return free_time

    def add_time_usage(self,
                       id_obj: int,
                       cal_date: date,
                       shift: int,
                       hours: float
                       ) -> None:
        """Добавляет параметр ``hours`` к ``time_usage`` заданного дня"""
        self.calendar[id_obj][(cal_date, shift)]["time_usage"] += hours

    def add_machine_usage(self,
                          id_obj: int,
                          cal_date: date,
                          shift: int,
                          machine_usage: tuple[datetime, datetime, int|str|None, int|None, str|None]) -> None:
        """
        Добавление использования машины, в заданный день
        :param id_obj: Индекс объекта
        :param cal_date: Дата формата ``date``
        :param shift: Смена
        :param machine_usage: Использование машины формата:
         (начало работы оборудования формата ``datetime``,
         конец работы оборудования формата ``datetime``,
         индекс ботинка формата ``int``,
         индекс заказа формата ``int``,
         цвет используемых нитей формата ``str``)
        """
        machine_usage = machine_usage_tuple(*machine_usage)
        self.calendar[id_obj][(cal_date, shift)]["machine_usage"].append(machine_usage)
        "Сортируем, чтобы все шло по порядку"
        self.calendar[id_obj][(cal_date, shift)]["machine_usage"] = (
            sorted(self.calendar[id_obj][(cal_date, shift)]["machine_usage"], key=lambda x: (x.start, x.end)))
        duration: float = (machine_usage.end - machine_usage.start).total_seconds()
        self.add_time_usage(id_obj, cal_date, shift, duration)
        self.calendar[id_obj][(cal_date, shift)]["free_time"] = self.__free_time(id_obj, cal_date, shift)
        return

    def add_frozen(self, id_machine, cal_date, shift, machine_usage):
        """
        Разрешает проблемы, которые могут возникнуть в процессе заморозки шагов и закрепляет их в календаре
        :param id_machine: Индекс оборудования
        :type id_machine: int
        :param cal_date: Дата формата ``date``
        :type cal_date: date
        :param shift: Смена
        :type shift: int
        :param machine_usage: Использование машины формата:
         (начало работы оборудования формата ``datetime``,
         конец работы оборудования формата ``datetime``,
         индекс ботинка формата ``int``,
         индекс заказа формата ``int``,
         цвет используемых нитей формата ``str``)
        :type machine_usage: tuple[datetime, datetime, int, int, str]
        :rtype: None
        """

        start_freeze, end_freeze, id_boots, id_position, string_color = machine_usage

        # Проверяем есть ли такое оборудование и существует ли в данном оборудовании данные за заданную дату и смену
        if self.calendar.get(id_machine) is None or self.calendar[id_machine].get((cal_date, shift)) is None:
            return

        # Если время шага выходит за границы смены, сокращаем заморозку до границ смены
        start_period, end_period = self.get_period(id_machine, cal_date, shift)
        if start_period > start_freeze:
            start_freeze = start_period
        if end_period < end_freeze:
            end_freeze = end_period

        # На случай, если придется разбивать это время на несколько частей
        freeze_list = [(start_freeze, end_freeze)]

        for start_usage, end_usage, _, _ in self.calendar[id_machine][(cal_date, shift)].get("machine_usage"):
            for start_freeze, end_freeze in freeze_list.copy():
                # Замороженное время уже полностью занято -> убираем из списка
                if start_usage <= start_freeze < end_freeze <= end_usage:
                    freeze_list.remove((start_freeze, end_freeze))

                # Замороженное время правой границей заходит в занятое время -> меняем правую границу
                # на начало занятого участка
                elif start_freeze < start_usage < end_freeze <= end_usage:
                    freeze_list.remove((start_freeze, end_freeze))
                    freeze_list.append((start_freeze, start_usage))

                # Замороженное время левой границей заходит в занятое время -> меняем левую границу
                # на конец занятого участка
                elif start_usage <= start_freeze < end_usage <= end_freeze:
                    freeze_list.remove((start_freeze, end_freeze))
                    freeze_list.append((end_usage, end_freeze))

                # Занятое время находится внутри замороженного времени -> разделяем замороженный на 2 участка
                elif start_freeze < start_usage < end_usage < end_freeze:
                    freeze_list.remove((start_freeze, end_freeze))
                    freeze_list.append((start_freeze, start_usage))
                    freeze_list.append((end_usage, end_freeze))

        for start_freeze, end_freeze in freeze_list:
            machine_usage = (start_freeze, end_freeze, id_boots, id_position, string_color)
            self.add_machine_usage(id_machine, cal_date, shift, machine_usage)

    # def get_days_shift(self,
    #                    id_machine: int,
    #                    cal_date: date) -> dict:
    #     """
    #     Возвращает отсортированный словарь смен следующего формата:\n
    #     {
    #     ``Смена``: {
    #                 ``time_total``: ``n_hours``,\n
    #                 ``time_usage``: ``k_hours``,\n
    #                 ``period``: (``datetime``, ``datetime``),\n
    #                 ``machines_usage``: [(``start, end, boots_id, position_id``)]
    #                }
    #     }
    #     """
    #
    #     days_shifts = {}
    #     is_going = True
    #     shift = 1
    #     while is_going:
    #         if self.calendar[id_machine].get((cal_date, shift)) is not None:
    #             days_shifts[shift] = self.calendar[id_machine][cal_date, shift]
    #         else:
    #             is_going = False
    #         shift += 1
    #
    #     new_days_shifts = {}
    #     for shift in sorted(days_shifts, key=lambda x: days_shifts[x]["period"][0]):
    #         new_days_shifts[shift] = days_shifts[shift]
    #
    #     return new_days_shifts

    def copy_nested_dict(self, obj):
        """
        Рекурсивно создает глубокую копию вложенных словарей, списков и множеств.
        """
        if isinstance(obj, dict):
            return {key: self.copy_nested_dict(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.copy_nested_dict(item) for item in obj]
        elif isinstance(obj, set):
            return {self.copy_nested_dict(item) for item in obj}
        return obj


    def set_calendar_copy(self) -> None:
        """Снимает копию с календаря и записывает в соответствущую переменную"""
        #self.calendar_copy = deepcopy(self.calendar)
        self.calendar_copy = self.copy_nested_dict(self.calendar)

    def calendar_rollback(self) -> None:
        """Возвращает календарь к состоянию на момент снятия копии календаря"""
        self.calendar = self.calendar_copy
