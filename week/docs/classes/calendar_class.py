from copy import deepcopy
from datetime import timedelta, date, datetime

from docs.database import get_table_data, MachineDB, MachineCalendarDB, Serialize
from docs.classes.machine_groups_class import machine_groups
from docs.classes.calendar_base_class import CalendarBase
from docs.utils import print_red, print_green, print_lblue


class MachineCalendar(CalendarBase):
    """Формат календаря выглядит следующим образом:\n
        {``id_оборудования``:
         {(``дата``, ``смена``):
          {``time_total``: ``n_hours``,\n
          ``time_usage``: ``k_hours``,\n
          ``period``: (``datetime``, ``datetime``),\n
          ``machines_usage``: [(``start, end, boots_id, position_id``)],\n
          ``free_time``: [(``start``, ``end``, ``duration``)]}}}"""

    def __init__(self):
        super().__init__()
        self.name = "КАЛЕНДАРЬ ОБОРУДОВАНИЯ"

    def reset_calendar(self):
        print_lblue("НАЧИНАЮ ФОРМИРОВАНИЕ КАЛЕНДАРЯ ОБОРУДОВАНИЯ")
        super().reset_calendar()
        self.__set_calendar()
        print_green("КАЛЕНДАРЬ ОБОРУДОВАНИЯ УСПЕШНО СФОРМИРОВАН")

    def __set_calendar(self):

        m_list: list[MachineDB] = get_table_data(MachineDB, MachineDB.id > 0)
        mc_dict = self._get_cal_dict(MachineCalendarDB)

        """Заполнение словаря календаря"""
        for machine in m_list:
            if mc_dict.get(machine.machine_calendar_id) is None:
                print_red(f"НЕТ ТАКОГО КАЛЕНДАРЯ МАШИН - {machine.machine_calendar_id}\n"
                          f"ПРОБЛЕМА С МАШИНОЙ - {machine.id}")
            else:
                self.calendar[machine.id] = deepcopy(mc_dict.get(machine.machine_calendar_id))

                """Поиск суммарного количества часов работы всех машин"""
                self.total_work_hours += sum(x["time_total"] for x in self.calendar[machine.id].values())

        """РАСТЯГИВАНИЕ КАЛЕНДАРЯ"""
        self._calendar_expansion()

        for id_machine in self.calendar:
            for machine_group in machine_groups.get_machine_groups(id_machine):
                """Поиск количества смен и их порядок для групп оборудования на каждый день"""
                for (c_date, shift), value in self.calendar.get(id_machine).items():
                    self.max_shift[machine_group, c_date] = (
                        self.max_shift.get((machine_group, c_date), []))
                    if shift not in [x[0] for x in self.max_shift[machine_group, c_date]]:
                        self.max_shift[machine_group, c_date].append((shift, value["period"][0]))
                        self.max_shift[machine_group, c_date] = sorted(
                            self.max_shift[machine_group, c_date], key=lambda x: x[1])

    def get_last_color(self, id_machine: int, cal_date: date, date_and_time: datetime):
        """
        Функция возвращает цвет нитки по заданным параметрам
        :param id_machine: Индекс оборудования в котором необходимо искать цвет нитки.
        :param cal_date: Дата в которую планируется вставить шаг.
        :param date_and_time: Время и дата формата ``datetime`` куда планируется вставить шаг.
        :return: Последний цвет использовавшийся на данной машине до ``date_and_time``
        или ``None`` в случае если не использовались нитки на данном оборудовании до заданного момента.
        """

        machine_shift = 1
        nothing = "Ничего"
        string_color = nothing

        def find_color(id, c_date):
            color = nothing
            for machine_usage in self.get_machine_usage(id, c_date, machine_shift):
                if machine_usage.end > date_and_time:
                    break
                color = machine_usage.string_color
            return color

        while string_color == nothing and cal_date >= Serialize.start_date.date():
            string_color = find_color(id_machine, cal_date)
            cal_date -= timedelta(days=1)

        return None if string_color == nothing else string_color
