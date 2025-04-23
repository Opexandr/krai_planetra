from collections import defaultdict
from datetime import date, datetime, timedelta
from sqlalchemy import and_

from docs.classes.calendar_class import MachineCalendar
from docs.classes.workers_class import WorkersCalendar
from docs.database import get_table_data, WorkplaceDB, EmergencyDB
from docs.classes.machine_groups_class import machine_groups
from docs.classes.singleton_meta_class import SingletonMeta
from docs.utils import print_lblue


shift_for_machines = 1
recursion_counter = 0
recursion_limit = 14


class WorkPlaces(metaclass=SingletonMeta):
    """Класс рабочих мест"""

    def __init__(self):
        self.worker_calendar = WorkersCalendar()
        self.machine_calendar = MachineCalendar()
        self.workplaces = {}
        self.wp_by_machines = defaultdict(list)
        self.m_req_ft = {} # machine required free time
        self.w_req_ft = {} # worker required free time
        self.free_time = {}
        self.__setup_workplaces()

    def __setup_workplaces(self) -> None:
        """
        Подготавливает словарь рабочих мест формата:\n
        {``id_workplace``: (``id_machine``, ``id_worker``)
        """
        downloaded_workplaces: list[WorkplaceDB] = get_table_data(WorkplaceDB)
        for workplace in downloaded_workplaces:
            self.workplaces[workplace.id] = {
                "machine": workplace.machine_id,
                "worker": workplace.worker_id,
            }

            self.wp_by_machines[workplace.machine_id].append(workplace.id)

    def reset_calendar(self) -> None:
        self.worker_calendar.reset_calendar()
        self.machine_calendar.reset_calendar()
        self.workplaces = {}
        self.wp_by_machines = defaultdict(list)
        self.m_req_ft = {}  # machine required free time
        self.w_req_ft = {}  # worker required free time
        self.free_time = {}
        self.__setup_workplaces()
        self.__emergency_accounting()
        return

    def freeze_position(self, position):
        """
        Замораживает позицию и закрепляет его в календарях
        :param position: Позиция, который необходимо заморозить
        :type position: Positions
        :rtype: None
        """
        for pair in position.pairs:
            for step in pair.steps:
                id_workplace = step.id_workplace
                cal_date = step.start_date.date()
                id_machine = self.workplaces[id_workplace]['machine']
                id_worker = self.workplaces[id_workplace]['worker']
                period = self.machine_calendar.get_period(id_machine, cal_date, shift_for_machines)
                if step.start_date < period[0]:
                    cal_date -= timedelta(days=1)
                shift = step.shift
                machine_usage = (
                    step.start_date,
                    step.end_date,
                    pair.id_boots,
                    position.id,
                    step.color
                )
                self.machine_calendar.add_frozen(id_machine, cal_date, shift_for_machines, machine_usage)
                self.worker_calendar.add_frozen(id_worker, cal_date, shift, machine_usage)

    def __emergency_change_date_shift(self, obj_calendar, id_obj, cal_date, shift, duration_tuple):
        """
        Функция сдвига даты или смены для вставки аварийных ситуаций
        :param obj_calendar: объект календаря работников или оборудования
        :param id_obj: индекс сущности (работника или оборудования)
        :type id_obj: int
        :param cal_date: дата
        :type cal_date: date
        :param shift: смена
        :type shift: int
        :param duration_tuple: кортеж, с началом и концом аварийной ситуации
        :type duration_tuple: tuple[datetime, datetime]
        :return: None
        """

        "Переход по сменам"
        for i in self.get_shifts():
            if i > shift and obj_calendar.calendar[id_obj].get((cal_date, i)) is not None:
                self.__emergency_freeze(obj_calendar, id_obj, cal_date, i, duration_tuple)
                return

        "Переход по дням"
        self.__emergency_freeze(obj_calendar, id_obj, cal_date + timedelta(days=1), 1, duration_tuple)
        return

    def __emergency_freeze(self, obj_calendar, id_obj, cal_date, shift, duration_tuple):
        """
        Рекурсивно закрепляет аварийные ситуации в необходимом календаре
        :param obj_calendar: объект календаря
        :param id_obj: индекс сущности
        :type id_obj: int
        :param cal_date: дата
        :type cal_date: date
        :param shift: смена
        :type shift: int
        :param duration_tuple: кортеж, с началом и концом аварийной ситуации
        :type duration_tuple: tuple[datetime, datetime]
        :return: None
        """

        global recursion_counter

        start, end = duration_tuple

        "Если индекса нет в объекте календаря -> ничего не делаем"
        if obj_calendar.calendar.get(id_obj) is None:
            return

        "Если комбинации даты и смены нет в объекте календаря -> пытаемся перейти на другую смену/день"
        if obj_calendar.calendar[id_obj].get((cal_date, shift)) is None:
            "Чтобы рекурсия не длилась вечно задан предел рекурсии"
            if recursion_counter > recursion_limit:
                recursion_counter = 0
                return
            recursion_counter += 1
            self.__emergency_change_date_shift(obj_calendar, id_obj, cal_date, shift, duration_tuple)
            return

        recursion_counter = 0

        s = max(start, obj_calendar.get_period(id_obj, cal_date, shift)[0])
        e = min(end, obj_calendar.get_period(id_obj, cal_date, shift)[1])

        if s > e:
            self.__emergency_change_date_shift(obj_calendar, id_obj, cal_date, shift, duration_tuple)
            return
        elif s < e:
            machine_usage = (s, e, None, None, None)
            obj_calendar.add_frozen(id_obj, cal_date, shift, machine_usage)

        if e < end:
            duration_tuple = (e, end)
            self.__emergency_change_date_shift(obj_calendar, id_obj, cal_date, shift, duration_tuple)

        return

    def __emergency_machines(self):
        """
        Функция закрепления аварийных ситуаций в календаре машин
        """
        e_filter = and_(EmergencyDB.machine_id != None, EmergencyDB.start_date != None, EmergencyDB.end_date != None)
        em_list: list[EmergencyDB] = get_table_data(EmergencyDB, e_filter)

        for emergency in em_list:
            start = emergency.start_date
            cal_date = start.date()
            end = emergency.end_date
            id_machine = emergency.machine_id

            if start < self.machine_calendar.get_period(id_machine, cal_date, shift_for_machines)[0]:
                cal_date -= timedelta(days=1)

            self.__emergency_freeze(self.machine_calendar,
                                    id_machine,
                                    cal_date,
                                    shift_for_machines,
                                    (start, end))

    def __emergency_workers(self):
        """
        Функция закрепления аварийных ситуаций в календаре рабочих
        """
        e_filter = and_(EmergencyDB.worker_id != None, EmergencyDB.start_date != None, EmergencyDB.end_date != None)
        ew_list: list[EmergencyDB] = get_table_data(EmergencyDB, e_filter)

        for emergency in ew_list:
            start = emergency.start_date
            cal_date = start.date()
            end = emergency.end_date
            id_worker = emergency.worker_id

            if start < self.worker_calendar.get_period(id_worker, cal_date, shift_for_machines)[0]:
                cal_date -= timedelta(days=1)

            self.__emergency_freeze(self.worker_calendar,
                                    id_worker,
                                    cal_date,
                                    shift_for_machines,
                                    (start, end))

    def __emergency_accounting(self):
        """Функция учета аварийных ситуаций"""

        self.__emergency_machines()
        self.__emergency_workers()

    def set_calendar_copy(self) -> None:
        """Снимает копию с календаря и записывает в соответствущую переменную"""
        self.worker_calendar.set_calendar_copy()
        self.machine_calendar.set_calendar_copy()

    def calendar_rollback(self) -> None:
        """Возвращает календари к состоянию на момент снятия копии календарей"""
        self.worker_calendar.calendar_rollback()
        self.machine_calendar.calendar_rollback()

    def max_date(self) -> date:
        """Возвращает максимальную дату календарей"""
        return self.machine_calendar.max_date.date()

    @staticmethod
    def get_shifts() -> list[int]:
        """ДОДЕЛАНО"""
        return [1, 2]

    def get_workplaces(self, id_machine_group) -> list[int]:
        """Возвращает список всех индексов рабочих мест,
        машины в которых входят в заданный индекс группы машин"""
        wp_list = list()
        for machine in machine_groups.get_machines(id_machine_group):
            wp_list.extend(self.wp_by_machines.get(machine, []))
        return wp_list

    def get_worker_by_workplace(self, workplace_id):
        """Возвращает id работника указанного рабочего места."""
        return self.workplaces.get(workplace_id, {}).get("worker")

    def get_machine_by_workplace(self, workplace_id):
        """Возвращает id работника указанного рабочего места."""
        return self.workplaces.get(workplace_id, {}).get("machine")

    def get_workers_name(self, workplace_id):
        """Возвращает имя работника для данного рабочего места"""
        id_worker = self.get_worker_by_workplace(workplace_id)
        return self.worker_calendar.get_workers_name(id_worker)

    def get_free_time(self, id_workplace, cal_date, shift) -> list[dict]:
        """
        Возвращает список словарей свободного времени рабочего места следующего формата:\n
        [{``"start"``: ``datetime``, ``"end"``: ``datetime``, ``"dur"``: ``float``},]

        :param id_workplace: Индекс рабочего места
        :type id_workplace: int
        :param cal_date: Дата формата ``date``
        :type cal_date: date
        :param shift: Номер смены
        :type shift: int
        """
        id_machine = self.workplaces[id_workplace]["machine"]
        id_worker = self.workplaces[id_workplace]["worker"]

        # if (not self.m_req_ft.get((id_machine, cal_date), True) and not self.w_req_ft.get((id_worker, cal_date, shift), True)):
        #     result = self.free_time.get((id_workplace, cal_date, shift))
        #     if result is not None:
        #         return result

        machine_free_time = self.machine_calendar.get_free_time(
            id_machine,
            cal_date,
            shift_for_machines
        )

        worker_free_time = self.worker_calendar.get_free_time(
            id_worker,
            cal_date,
            shift
        )

        workplace_free_time = []
        m_idx, w_idx = 0, 0
        m_len = len(machine_free_time)
        w_len = len(worker_free_time)

        while m_idx < m_len and w_idx < w_len:
            m_start, m_end, _ = machine_free_time[m_idx]
            w_start, w_end, _ = worker_free_time[w_idx]

            # Находим пересечение интервалов
            start = max(m_start, w_start)
            end = min(m_end, w_end)
            if start < end:
                # Добавляем пересечение в результат
                workplace_free_time.append({
                    "start": start,
                    "end": end,
                    "dur": (end - start).total_seconds()
                })
                # Перемещаем указатель интервала, который раньше заканчивается
                if m_end < w_end:
                    m_idx += 1
                else:
                    w_idx += 1
            else:
                # Перемещаем указатель интервала с более ранним началом
                if m_start < w_start:
                    m_idx += 1
                else:
                    w_idx += 1

        self.free_time[(id_workplace, cal_date, shift)] = workplace_free_time
        self.m_req_ft[(id_machine, cal_date)] = False
        self.w_req_ft[(id_worker, cal_date, shift)] = False
        return workplace_free_time

    def add_machine_usage(self,
                          id_workplace: int,
                          spaces,
                          id_boots,
                          id_position) -> None:
        """
        Добавление использования рабочего места, в заданный день
        :param id_workplace: Индекс рабочего места
        :param spaces: Список временных интервалов, выбранных для выполнения производственного шага
        :param id_boots: Индекс ботинка
        :param id_position: Индекс позиции
         """
        id_machine = self.workplaces[id_workplace]["machine"]
        id_worker = self.workplaces[id_workplace]["worker"]
        for space in spaces:
            cal_date = space["start"].date()
            shift = space["shift"]
            color = space.get("color")

            machine_usage = (
                space["start"],
                space["end"],
                id_boots,
                id_position,
                color
            )

            if space.get("changeover"):
                changeover_m_u = (
                    space["start"] - timedelta(seconds=space["changeover"]),
                    space["start"],
                    "переналадка",
                    id_position,
                    None
                )
                self.machine_calendar.add_machine_usage(id_machine, cal_date, shift_for_machines, changeover_m_u)
                self.worker_calendar.add_machine_usage(id_worker, cal_date, shift, changeover_m_u)

            self.machine_calendar.add_machine_usage(id_machine, cal_date, shift_for_machines, machine_usage)
            self.worker_calendar.add_machine_usage(id_worker, cal_date, shift, machine_usage)
            self.m_req_ft[(id_machine, cal_date)] = True
            self.w_req_ft[(id_worker, cal_date, shift)] = True
        return

    def get_nearest_color(self, id_workplace: int, start: datetime) -> str|None:
        """
        Возвращает ближайший цвет ниток или None, если можно вставить любой цвет ниток без переналадок
        :param id_workplace: Индекс рабочего места
        :param start: Время до которого ищется ближайший цвет ниток
        :return: Цвет ниток
        """

        id_machine = self.workplaces[id_workplace]["machine"]
        cal_date = start.date()

        if start < self.machine_calendar.get_period(id_machine, cal_date, shift_for_machines)[0]:
            cal_date -= timedelta(days=1)

        return self.machine_calendar.get_last_color(id_machine, cal_date, start)

    def print_changeovers(self):
        print_lblue("Информация по переналадкам:")
        total_count = 0
        total_duration = 0.0
        for id_machine in self.machine_calendar.calendar:
            count = 0
            duration = 0.0
            for date_and_shift in self.machine_calendar.calendar[id_machine]:
                for machine_usage in self.machine_calendar.calendar[id_machine][date_and_shift]["machine_usage"]:
                    if machine_usage.boots_id == "переналадка":
                        count += 1
                        duration += (machine_usage.end - machine_usage.start).total_seconds()
            if count:
                print_lblue(f"\tОборудование {id_machine}:")
                print_lblue(f"\t\tКол-во переналадок = {count}")
                print_lblue(f"\t\tСуммарная длительность переналадок = {duration} секунд = {duration / 60} минут")
                total_count += count
                total_duration += duration
        print_lblue(f"\tСуммарное кол-во переналадок на всем оборудовании  = {total_count}")
        print_lblue(f"\tСуммарная длительность переналадок на всем оборудовании = {total_duration} секунд = {total_duration / 60} минут")

    def print_colors_with_date(self):
        def format_dt(dt):
            return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:23]
        print_lblue("Информация по цветам ниток:")
        for id_machine in self.machine_calendar.calendar:
            is_printed = False
            for date_and_shift in self.machine_calendar.calendar[id_machine]:
                for machine_usage in self.machine_calendar.calendar[id_machine][date_and_shift]["machine_usage"]:
                    if machine_usage.string_color is not None:
                        if not is_printed:
                            print_lblue(f"\tОборудование {id_machine}:")
                            is_printed = True
                        print_lblue(f"\t\t{format_dt(machine_usage.start)} - "
                                    f"{format_dt(machine_usage.end)} - "
                                    f"{machine_usage.string_color} - "
                                    f"Ботинки: {machine_usage.boots_id}")
                    elif machine_usage.boots_id == "переналадка":
                        if not is_printed:
                            print_lblue(f"\tОборудование {id_machine}:")
                            is_printed = True
                        print_lblue(f"\t\t{format_dt(machine_usage.start)} - "
                                    f"{format_dt(machine_usage.end)} - "
                                    f"{machine_usage.boots_id}")

