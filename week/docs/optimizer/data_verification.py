from datetime import timedelta, datetime
from sqlalchemy import and_

from docs.classes import WorkPlaces, Steps, Positions
from docs.database import get_table_data, TechCard, Serialize, get_table_first, OptimizeParams
from docs.utils import print_red, copy_all_same_attrs, print_blue


def check_impossible_position(positions=None, period=90, plan_id=None):
    """Проверяет данные, а именно - какие позиции невозможно произвести в заданный период планирования
    :param positions: Список объектов позиций
    :type positions: list
    :param start_date: Дата начала планирования
    :type start_date: datetime
    :param period: Количество дней планирования
    :type period: int
    :return: None"""
    print_blue("Проверка данных")
    workplaces = WorkPlaces()
    if not positions:
        workplaces.reset_calendar()
        optimize_params = get_table_first(OptimizeParams, conditions=OptimizeParams.id == 1)
        positions = Positions.get_positions(optimize_params, plan_id)
    positions_to_check = [position for position in positions if not position.freeze]
    impossible_position = set()
    step_to_positions = group_positions_by_step(positions_to_check)
    impossible_steps = check_steps_wp(period)
    for step in impossible_steps:
        if step_to_positions.get(step):
            for position in step_to_positions.get(step):
                impossible_position.add(position)
    for position in impossible_position:
        print_red(f"Позицию {position.id} невозможно произвести.")
        position.status = Serialize.get_pos_status("data")
    print_blue("Проверка окончена")


def group_positions_by_step(positions):
    """Формирует словарь, для работы с позициями.
    :param positions: Список объектов позиций
    :type positions: list
    :return: Словарь, где ключ id шага, а значение список id позиций, относящихся к этому шагу.
    """
    step_to_positions = {}
    for position in positions:
        for step in position.steps:
            step_to_positions[step.id] = step_to_positions.get(step.id, [])
            step_to_positions[step.id].append(position)
    return step_to_positions


def check_steps_wp(period):
    """Проверяет, возможно ли выполнить шаги для всех техкарт в заданном периоде времени.
    :param start_date: Дата начала планирования
    :type start_date: datetime
    :param period: Количество дней планирования
    :type period: int
    :return: Список id невыполнимых шагов."""
    all_dates = get_weekdays_in_range(period)
    set_worker, set_machine = set(), set()
    impossible_steps = []
    tech_cards: list[TechCard] = get_table_data(TechCard, and_(TechCard.id > 0, TechCard.id_group_machine > 0))
    for tech_card in tech_cards:
        step = Steps()
        copy_all_same_attrs(step, tech_card)
        if not process_workplaces(step, all_dates, set_worker, set_machine):
            print_red(f"Шаг {step.id} невозможно выполнить.")
            impossible_steps.append(step.id)
    return impossible_steps


def process_workplaces(step, all_dates, set_worker, set_machine):
    """Проверяет, возможно ли выполнить шаг для всех рабочих мест в заданном периоде.
    :param step: Объект шага
    :type step: Steps
    :param all_dates: Список дней для проверки
    :type all_dates: list[datetime]
    :param set_worker: Набор id работников
    :type set_worker: set
    :param set_machine: Набор id оборудования
    :type set_machine: set
    return True/False"""
    workplaces = WorkPlaces()
    all_wp = workplaces.get_workplaces(step.id_group_machine)
    if not all_wp:
        print_red(f"Нет рабочих мест для шага с группой машин {step.id_group_machine}")
        return False
    step_possible = False
    for prod_day in all_dates:
        for wp in all_wp:
            if workplaces.get_free_time(wp, prod_day, 1):
                step_possible = True
            else:
                print_red(f"У рабочего места {wp} нет пересечений")
            worker_id, machine_id = workplaces.get_worker_by_workplace(wp), workplaces.get_machine_by_workplace(wp)
            if machine_id not in set_machine:
                set_machine.add(machine_id)
                check_machine_and_worker_schedule(machine_id, all_dates, 'Оборудование')
            if worker_id not in set_worker:
                set_worker.add(worker_id)
                check_machine_and_worker_schedule(worker_id, all_dates, 'Работник')
    return step_possible


def check_machine_and_worker_schedule(id, all_dates, object_type):
    """Проверяет, есть ли у работника или оборудования записи на каждый день в заданном периоде.
    :param id: Идентификатор объекта
    :type id: int
    :param all_dates: Список дней для проверки
    :type all_dates: list[datetime]
    :param object_type: Тип объекта (работник/оборудование)
    :type object_type: str
    :return: None"""
    recorded_dates = set()
    workplaces = WorkPlaces()
    calendar = workplaces.worker_calendar.calendar if object_type == 'Работник' else workplaces.machine_calendar.calendar
    for key, value in calendar[id].items():
        recorded_dates.add(key[0])
        time_total = value['time_total']
        if time_total <= 0:
            print(f"Время работы {object_type} {id} равно {time_total}")
    missing_dates = all_dates - recorded_dates
    if missing_dates:
        print_red(f"{object_type} {id} не имеет записей на следующие дни:")
        for date in sorted(missing_dates):
            print_red(f" - {date}")


def get_weekdays_in_range(period):
    """Генерирует множество дат в указанном диапазоне, исключая выходные (субботу и воскресенье).
    :param start_date: Дата начала планирования
    :type start_date: datetime
    :param period: Количество дней планирования
    :type period: int
    :return: Множество дат в указанном диапазоне, исключая выходные (субботу и воскресенье)."""
    all_dates = set()
    for i in range(period + 1):
        date = (Serialize.start_date + timedelta(days=i)).date()
        if date.weekday() in [5, 6]:
            continue
        all_dates.add(date)
    return all_dates


if __name__ == '__main__':
    pass


# 'УДАЛИТЬ ПОСЛЕ ТЕСТОВ'
# workplaces.reset_calendar()
# plan_id = 0
# optimize_params = get_table_first(OptimizeParams, conditions=OptimizeParams.id == 1)
#
# start_date = datetime(2025, 4, 1)
#
# positions = Positions.get_positions(optimize_params, datetime(2025, 4, 1), plan_id)
