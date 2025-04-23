from copy import deepcopy

from docs.database import get_table_data, WorkerDB, WorkerCalendarDB
from docs.classes.calendar_base_class import CalendarBase
from docs.utils import print_red, print_green, print_lblue


class WorkersCalendar(CalendarBase):

    def __init__(self):
        super().__init__()
        self.name = "КАЛЕНДАРЬ РАБОТНИКОВ"
        self.workers_names = {}

    def reset_calendar(self):
        print_lblue("НАЧИНАЮ ФОРМИРОВАНИЕ КАЛЕНДАРЯ РАБОТНИКОВ")
        super().reset_calendar()
        self.__set_calendar()
        print_green("КАЛЕНДАРЬ РАБОТНИКОВ УСПЕШНО СФОРМИРОВАН")

    def __set_calendar(self):

        w_list: list[WorkerDB] = get_table_data(WorkerDB, WorkerDB.id > 0)
        wc_dict = self._get_cal_dict(WorkerCalendarDB)

        """Заполнение словаря календаря"""
        for worker in w_list:
            if wc_dict.get(worker.worker_calendar_id) is None:
                print_red(f"НЕТ ТАКОГО КАЛЕНДАРЯ РАБОТНИКА - {worker.worker_calendar_id}\n"
                          f"ПРОБЛЕМА С РАБОТНИКОМ - {worker.id}")
            else:
                self.calendar[worker.id] = deepcopy(wc_dict.get(worker.worker_calendar_id))

                """Поиск суммарного количества часов работы всех рабочих"""
                self.total_work_hours += sum(x["time_total"] for x in self.calendar[worker.id].values())

            """Заполнение словаря именами работников"""
            self.workers_names[worker.id] = worker.name

        """РАСТЯГИВАНИЕ КАЛЕНДАРЯ"""
        self._calendar_expansion()

    def get_workers_name(self, id_worker):
        return self.workers_names.get(id_worker)
