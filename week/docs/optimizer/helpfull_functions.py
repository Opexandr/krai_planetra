from copy import deepcopy
from datetime import timedelta


def position_free_space(position):
    """
    Возвращает время в рамках которого можно двигать данную позицию относительно его границ
    :param position: позиция
    :type position: Positions
    :return: время свободного пространства
    """
    answer = position.right_border - position.left_border - timedelta(hours=position.duration)
    return answer


# def shift_step_to_date(step, shift_date):
#     """
#     Сдвигает шаг к определенной дате.
#     :param step: шаг
#     :type step: Steps
#     :param shift_date: дата к которой нужно сдвинуть шаг
#     :type shift_date: datetime
#     """
#     step.start_date = shift_date
#     step.end_date = shift_date + timedelta(minutes=step.duration)
#
#
# def shift_pair_to_date(pair, shift_date):
#     """Сдвигает пару к определенной дате, после чего обрабатывает шаги.
#     :param pair: пара
#     :type pair: Pairs
#     :param shift_date: дата к которой нужно сдвинуть пару
#     :type shift_date: datetime
#     """
#     pair.start_date = shift_date
#     pair.end_date = pair.start_date + timedelta(hours=pair.duration)
#     start_step = shift_date
#     for step in pair.steps:
#         shift_step_to_date(step, start_step)
#         start_step = step.end_date


def split_pair_step(pair, step, time_from_start):
    """
    Разбивает шаг на два на time_from_start минут от начала.
    Уменьшает исходный шаг, добавляет новый в список шагов пары.
    :param pair: пара
    :param step: шаг пары
    :param time_from_start: через сколько минут от начала разбить шаг
    :return:
    """
    if time_from_start is timedelta:
        time_from_start = time_from_start.total_seconds()
    border = step.start_date + timedelta(minutes=time_from_start)
    new_step = deepcopy(step)
    step.end_date = border
    step.duration = (step.end_date - step.start_date).total_seconds() / 60
    new_step.start_date = border
    new_step.duration = (new_step.end_date - new_step.start_date).total_seconds() / 60
    pair.steps.append(new_step)



if __name__ == '__main__':
    ...