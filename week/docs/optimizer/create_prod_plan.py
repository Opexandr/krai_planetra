from copy import deepcopy
from datetime import timedelta, datetime, date

from docs.database import SortCriteria, get_table_data, Serialize
from docs.classes import Pairs, WorkPlaces, Steps, Positions
from docs.utils import print_blue, copy_all_same_attrs


def sorted_positions(positions):
    """
    Cортирует позиции по указанным критериям и направлениям.
    :param positions: Список позиций.
    :type positions: list[Positions]
    :return: Отсортированный список позиций.
    """
    criteria = get_table_data(SortCriteria)
    sort_criteria = sorted(criteria, key=lambda x: x.priority)
    # cортировка по именам критериев
    positions = sorted(positions, key=lambda x: (
        # Сначала проверяем freeze
            (not getattr(x, 'freeze'),) +
            # Затем сортируем по остальным критериям
            tuple(
                getattr(x, criterion.name) if not criterion.reverse else -getattr(x, criterion.name)
                for criterion in sort_criteria if criterion.name != 'freeze'
            )
    ))

    return positions


def week_pos_sort(positions):
    """Функция сортировки недельных позиций"""
    def sort_key(x):
        def key_helper(value):
            return (1, value) if value is not None else (2, None)

        return (
            key_helper(x.right_border),
            key_helper(x.top),
            key_helper(x.bot),
            key_helper(x.sole)
        )
    positions = sorted(positions, key=sort_key)
    return positions


def min_free_space(machine_spaces: dict):
    """
    Находит минимальный свободный диапазон в работе оборудования
    :param machine_spaces:
    :return: кортеж, состоящий из id машины и минимального свободный промежутка
    """
    min_range = None
    min_id = None
    for id_machine, spaces in machine_spaces.items():
        if min_range is None or spaces[0] < min_range:
            min_range = spaces[0]
            min_id = id_machine

    return min_id, min_range


def is_space_enough(prev_step_end: datetime | None, space: tuple, step_duration: float, coefficient: int):
    """
    Проверяет, достаточно ли времени промежутка для продолжения шага
    :param prev_step_end: конец предыдущего шага
    :param space: кортеж (``start_datetime``, ``end_datetime``, ``duration_float``)
    :param step_duration: длительность шага
    :param coefficient: коэффициент длительности
    :return: True / False
    """
    duration = step_duration / coefficient
    if prev_step_end is None and space[2] >= duration:
        return True
    elif space[0] < prev_step_end < space[1] and (space[1] - prev_step_end).total_seconds() >= duration:
        return True
    elif space[0] >= prev_step_end and space[2] >= duration:
        return True
    return False


def split_step(step, split_data):
    """
    Функция разделяет заданный шаг на несколько шагов по патерну указанному в ``split_data``
    :param step: Шаг, который необходимо разделить на несколько
    :type step: Steps
    :param split_data: Патерн разделения шага формата - [((``start end duration``), ``shift``), ``...``]
    :type split_data: list
    :return: Возвращает список шагов получившихся в ходе разделения изначального шага
    :rtype: list[Steps]
    """

    ln = len(split_data)

    splitted_steps = [None] * ln
    i = 0
    for space in split_data:
        start = space['start']
        end = space['end']
        duration = space['dur']
        shift = space['shift']
        new_step = Steps()
        copy_all_same_attrs(new_step, step)

        new_step.splited = True
        new_step.duration = duration
        new_step.start_date = start
        new_step.end_date = end
        new_step.shift = shift

        splitted_steps[i] = new_step
        i += 1
    del step

    return splitted_steps


def _get_prioritized_workplaces(group_id, preferred_worker):
    workplaces = WorkPlaces()
    """Получает и сортирует рабочие места с учётом предпочтительного работника"""
    all_wp = workplaces.get_workplaces(group_id)
    if preferred_worker is None:
        return all_wp

    preferred = [wp for wp in all_wp
                if workplaces.get_worker_by_workplace(wp) == preferred_worker]
    remaining = [wp for wp in all_wp if wp not in preferred]
    return preferred + remaining


def _initialize_wp_data(all_wp):
    """Инициализирует структуры данных для отслеживания времени"""
    return ({wp: 0 for wp in all_wp},
            {wp: [] for wp in all_wp})


def _is_valid_space(prev_end, space):
    """Проверяет, подходит ли временной промежуток для обработки"""
    return prev_end < space["end"]


def _adjust_final_space(choosen_spaces, wp_id, step_duration, start, current_wp_time_total):
    """Корректирует последний добавленный промежуток"""
    last_index = len(choosen_spaces[wp_id]) - 1
    extra_time = current_wp_time_total - step_duration
    req_dur = choosen_spaces[wp_id][last_index]["dur"] - extra_time
    end = start + timedelta(seconds=req_dur)

    choosen_spaces[wp_id][last_index].update({
        "end": end,
        "dur": req_dur
    })


def _handle_changeover(workplaces, step, choosen_spaces, wp_id, start, space):
    """Обрабатывает время переналадки оборудования"""
    if not Serialize.is_week or step.color is None:
        return True

    changeover_time_secs = 300
    prev_color = workplaces.get_nearest_color(wp_id, start)

    if prev_color is None or step.color == prev_color:
        choosen_spaces[wp_id][-1]["changeover"] = 0
        choosen_spaces[wp_id][-1]["color"] = step.color
        return True

    start_with_changeover = max(space["start"], start - timedelta(seconds=changeover_time_secs))
    start_with_changeover += timedelta(seconds=changeover_time_secs)
    end_with_changeover = start_with_changeover + timedelta(seconds=choosen_spaces[wp_id][-1]["dur"])

    if end_with_changeover <= space["end"]:
        choosen_spaces[wp_id][-1].update({
            "start": start_with_changeover,
            "end": end_with_changeover,
            "changeover": changeover_time_secs,
            "color": step.color
        })
        return True
    else:
        choosen_spaces[wp_id].pop()
        return False


def _check_space_sufficiency(step_duration, space_duration, wp_time_total, wp_id,
                             choosen_spaces, space, shift, start, workplaces, step):
    """Проверяет достаточность времени и обрабатывает переналадку"""
    wp_time_total[wp_id] += space_duration
    choosen_spaces[wp_id].append({
        "start": start,
        "end": space["end"],
        "dur": space_duration,
        "shift": shift
    })

    if wp_time_total[wp_id] >= step_duration:
        _adjust_final_space(choosen_spaces, wp_id, step_duration, start, wp_time_total[wp_id])
        is_enough_time = _handle_changeover(workplaces, step, choosen_spaces, wp_id, start, space)
        return is_enough_time

    return False


def _process_production_day(step, prod_day, prev_end,
                           all_wp, wp_time_total, choosen_spaces):
    """Обрабатывает один производственный день"""
    workplaces = WorkPlaces()
    for shift in workplaces.get_shifts():
        for wp_id in all_wp:
            spaces = workplaces.get_free_time(wp_id, prod_day, shift)
            for space in spaces:
                if not _is_valid_space(prev_end, space):
                    continue

                start = max(prev_end, space['start'])
                space_duration = (space["end"] - start).total_seconds()

                if _check_space_sufficiency(
                    step.duration, space_duration, wp_time_total, wp_id,
                    choosen_spaces, space, shift, start, workplaces, step
                ):
                    return True

                if Serialize.is_week:
                    wp_time_total[wp_id] = 0
                    choosen_spaces[wp_id] = []
    return False


def workplaces_spaces_traversing(pair, step, prod_day, prev_step_end, preferred_worker=None):
    """
    Функция отбора подходящих промежутков для шага и их выборка.
    Обход идет пока не выйдем за min(дедлайн, наибольшая дата в календаре машин).
    Вернет (dict(``machine``: [(``space``, ``shift``)]), bool, datetime)
    :param pair: Пара для которой идет обход.
    :type pair: Pairs
    :param step: Шаг для которого идет обход.
    :type step: Steps
    :param prod_day: День с которого начинается производство.
    :type prod_day: date
    :param prev_step_end: Конец предыдущего шага.
    :type prev_step_end: datetime
    :param preferred_worker: Предпочтительный работник для выполнения шага.
    :type preferred_worker: int | None
    :return: ``choosen_spaces``, ``enough_space``, ``prod_day``
    :rtype: (dict, bool, datetime)
    """
    workplaces = WorkPlaces()
    all_wp = _get_prioritized_workplaces(step.id_group_machine, preferred_worker)
    wp_time_total, choosen_spaces = _initialize_wp_data(all_wp)
    enough_space = False
    prev_step_end = prev_step_end or pair.left_border

    while not enough_space and prod_day <= workplaces.max_date():
        enough_space = _process_production_day(
            step, prod_day, prev_step_end, all_wp,
            wp_time_total, choosen_spaces
        )

        if not enough_space:
            prod_day += timedelta(days=1)

    return choosen_spaces, enough_space, prod_day


def find_space_for_step(pair, step, prod_day, prev_step_end):
    """
    Ищет промежутки в работе рабочих мест. Возвращает словарь подходящих по длительности промежутков, идущих
    после предыдущего шага, словарь промежутков: смен к которым они относятся, день производства.
    :param pair: Объект ``Pairs``.
    :type pair: Pairs
    :param step: Объект ``Steps``.
    :type step: Steps
    :param prod_day:  ``datetime`` день с которого ищем промежутки.
    :type prod_day: date
    :param prev_step_end: ``datetime`` конец обработки предыдущего ``step`` этой ``pair``
    :type prev_step_end: datetime | None
    :returns: ``dict(id_machine: space)``, ``dict(space: shift)``, ``prod_day``, ``min_end``
    :rtype: (dict, dict, date, datetime)
    """
    # Если есть предыдущий шаг, берем работника, который его выполнил
    preferred_worker = None
    if step.step_num > 1:
        previous_step = pair.steps[step.step_num - 2]
        if hasattr(previous_step, "id_workplace"):
            workplaces = WorkPlaces()
            preferred_worker = workplaces.get_worker_by_workplace(previous_step.id_workplace)

    # обход в поиске подходящий промежутков
    choosen_spaces, enough_space, prod_day = workplaces_spaces_traversing(pair, step, prod_day, prev_step_end,
                                                                          preferred_worker=preferred_worker)
    # choosen_spaces = {machine: [((s, e, d), shift)]}

    spaces_for_cal = None
    min_wp = None
    min_end = None
    if enough_space:
        # выбираем рабочее место с самым ранним временем окончания
        for wp_id in choosen_spaces:
            if min_end and choosen_spaces[wp_id] and choosen_spaces[wp_id][-1]["end"] < min_end:
                min_end = choosen_spaces[wp_id][-1]["end"]
                min_wp = wp_id
            elif not min_end and choosen_spaces[wp_id]:
                min_end = choosen_spaces[wp_id][-1]["end"]
                min_wp = wp_id
        spaces_for_cal = choosen_spaces
    return spaces_for_cal, min_wp, prod_day, min_end


def update_position_dates(positions):
    """
    Устанавливает даты начала и конца для каждой позиции
    :param positions: Список позиций
    :type positions: list[Positions]
    :rtype: None
    """
    for position in positions:
        all_steps = []
        for pair in position.pairs:
            for step in pair.steps:
                if step.start_date and step.end_date:
                    all_steps.append(step)
        if all_steps:
            position.start_date = min(all_steps, key=lambda step: step.start_date).start_date
            position.end_date = max(all_steps, key=lambda step: step.end_date).end_date



def print_stat(positions, cnt_positions):
    """
    Вывод статистики в консоль
    :param positions:
    :return:
    """
    print('Итоги не вставших')
    quar_cnt = 0
    ddl_cnt = 0
    for position in positions:
        if position.quarantine:
            print(f'id:{position.id} - карантин')
            quar_cnt += 1
        elif position.end_date > position.right_border:
            print(f'id:{position.id} - дедлайн')
            ddl_cnt += 1
    print(f'Не встало {quar_cnt} из {cnt_positions}. Встало - {100 - (quar_cnt / cnt_positions * 100):.2f}%')
    print(f'Встало, но за дедлайн - {ddl_cnt}. \n'
          f'За ддл среди вставших - {100 - ddl_cnt / cnt_positions * 100:.2f}%\n'
          f'Встало идеально - {100 - (quar_cnt + ddl_cnt) / cnt_positions * 100:.2f}%')


def calc_pos_duration(positions):
    """
    Рассчитывает длительность каждой позиции, если вся мощьность производства будет направлена на нее
    :param positions:
    :param start_date:
    :return:
    """
    SECS_AT_HOUR = 3600
    print_blue('Расчет длительности позиций')
    tmp = deepcopy(positions)
    tmp = sorted_positions(tmp)


    pos_dates = {}
    for position in tmp:
        pos_dates[position.id] = {'start': None, 'end': None}
        if position.status == Serialize.get_pos_status('data') or not position.pairs or position.freeze or position.duration_h:
            continue
        workplaces = WorkPlaces()
        workplaces.set_calendar_copy()
        for pair in position.pairs:
            main_prod_day = pair.left_border.date()
            days_to_next_monday = (7 - main_prod_day.weekday()) % 7
            main_prod_day += timedelta(days=days_to_next_monday)
            new_steps = []
            placed = False
            prev_step_end = None
            if not pair.steps:
                continue
            for step in position.steps:
                step.duration = step.original_duration
                spaces_for_cal, choosen_wp, prod_day, step_end = find_space_for_step(pair, step, main_prod_day,
                                                                                     prev_step_end)
                if spaces_for_cal:
                    prev_step_end = step_end
                    placed = True
                    workplaces.add_machine_usage(choosen_wp,
                                                 spaces_for_cal[choosen_wp],
                                                 pair.id_boots,
                                                 position.id
                                                 )
                    if not pos_dates[position.id]['start']:
                        pos_dates[position.id]['start'] = spaces_for_cal[choosen_wp][0]['start']
                    pos_dates[position.id]['end'] = spaces_for_cal[choosen_wp][-1]['end']
                else:
                    placed = False
                    break
            if placed:
                pair.steps = new_steps
            else:
                print(f'pos {position.id} не смогли рассчитать')
                break
        workplaces.calendar_rollback()
    for position in positions:
        end = pos_dates[position.id]['end']
        start = pos_dates[position.id]['start']
        if not end:
            if position.duration_h:
                print(f'pos {position.id} уже подсчитан', position.duration_h)
            else:
                print(f'pos {position.id} ерунда с данными')
            continue
        pos_dates[position.id]['dur'] = (end - start).total_seconds() / SECS_AT_HOUR
        print(f'pos {position.id}', pos_dates[position.id]['dur'])
    print_blue('Расчет окончен')
    return pos_dates


def create_plan(positions):
    """
    Создает производственный план с учетом всех ограничений производства
    :param positions: список позиций
    :type positions: list[Positions]
    :param start_date: Начало периода
    :type start_date: datetime
    :return:
    """
    end_of_period = Serialize.start_date + timedelta(days=90)

    sort = sorted_positions
    if Serialize.is_week:
        sort = week_pos_sort
    positions = sort(positions)

    total_hours = 0.0
    cnt_positions = 0
    workplaces = WorkPlaces()
    for position in positions:
        Positions.count_prod_order += 1
        cnt_positions += 1
        print(f'position {cnt_positions}  id:{position.id}')
        if position.freeze:
            workplaces.freeze_position(position)
            if position.status == Serialize.get_pos_status('data'):
                continue
            if position.end_date > position.deadline:
                position.status = Serialize.get_pos_status('deadline')
            else:
                position.status = Serialize.get_pos_status('chosen')
            continue
        if position.status == Serialize.get_pos_status('data'):
            print('\t\t -не встал')
            continue
        if not position.pairs:
            print(f'{position.id} - нет пар')

        position_copy = position.get_copy()
        workplaces.set_calendar_copy()
        for pair in position.pairs:
            # находим датавремя для каждого из шагов в календаре, в которое можем вставить эту пару
            prod_day = pair.left_border.date()
            new_steps = []
            placed = False
            min_start = None
            prev_step_end = None
            for step in pair.steps:
                if getattr(step, "finished", False):
                    continue
                # обход в поиске дней
                spaces_for_cal, choosen_wp, prod_day, step_end = find_space_for_step(pair, step, prod_day,
                                                                                     prev_step_end)
                # переменная для шагов
                if spaces_for_cal:
                    prev_step_end = step_end
                    placed = True
                    if step.step_num == 1:
                        prev_step = step
                        prev_wp = choosen_wp
                        continue
                    if step.step_num == 2:
                        prev_shift = spaces_for_cal[choosen_wp][0]['shift']
                        prev_end = spaces_for_cal[choosen_wp][0]['start']
                        prev_start = prev_end - timedelta(seconds=prev_step.duration)
                        sp = [{'start': prev_start, 'end': prev_end, 'dur': prev_step.duration, 'shift': prev_shift}]
                        workplaces.add_machine_usage(prev_wp, sp, pair.id_boots, position.id)
                        prev_step.id_workplace = prev_wp
                        new_steps.extend(split_step(prev_step, sp))

                    step.id_workplace = choosen_wp
                    separated_step = split_step(step, spaces_for_cal[choosen_wp])
                    new_steps.extend(separated_step)

                    """Ищем минимальную дату начала шага"""
                    if step.step_num > 1 and not min_start:
                            min_start = spaces_for_cal[choosen_wp][0]["start"]

                    """Если минимальная дата шага вышла за наши 3 месяца, 
                    то ставим метку, что мы не поставили эту позицию"""
                    if pair == position.pairs[0] and min_start > end_of_period:
                        placed = False
                        break

                    workplaces.add_machine_usage(choosen_wp,
                                                 spaces_for_cal[choosen_wp],
                                                  pair.id_boots,
                                                  position.id
                                                  )
                else:
                    placed = False
                    break
            if placed:
                pair.steps = new_steps
            else:
                position = position_copy
                workplaces.calendar_rollback()
                position.status = Serialize.get_pos_status("calendar")
                print('\t\t -не встал', prod_day.day, prod_day.month)
                break

        if not position.status and position.pairs[-1].steps[-1].end_date > position.deadline:
            position.status = Serialize.get_pos_status("deadline")

        if not position.status:
            position.status = Serialize.get_pos_status("chosen")
            Positions.count_success += 1
    if Positions.count_prod_order:
        Positions.percent_success = int((Positions.count_success / Positions.count_prod_order) * 100)
    else:
        Positions.percent_success = 0
    update_position_dates(positions)
    check_inters(positions)


def check_inters(positions):
    def check(d):
        for k in d:
            for i in range(len(d[k]) - 1):
                cur_s, cur_e = d[k][i]
                next_s, next_e = d[k][i + 1]
                if cur_s <= next_s < cur_e or next_s <= cur_s < next_e:
                    if cur_s == cur_e == next_s:
                        continue
                    print('пупупу')

    wp_d = {}
    w_d = {}
    m_d = {}
    workplaces = WorkPlaces()
    for p in positions:
        if p.status not in (Serialize.get_pos_status('chosen'), Serialize.get_pos_status('deadline')):
            continue
        for pair in p.pairs:
            for s in pair.steps:
                wp_d[s.id_workplace] = wp_d.get(s.id_workplace, [])
                wp_d[s.id_workplace].append((s.start_date, s.end_date))

                w_id = workplaces.workplaces[s.id_workplace]["worker"]
                m_id = workplaces.workplaces[s.id_workplace]["machine"]

                w_d[w_id] = w_d.get(w_id, [])
                w_d[w_id].append((s.start_date, s.end_date))

                m_d[m_id] = m_d.get(m_id, [])
                m_d[m_id].append((s.start_date, s.end_date))

    print('Запускаем wp_d')
    for k in wp_d:
        wp_d[k] = sorted(wp_d[k], key=lambda x: (x[0], x[1]))
        check(wp_d)

    print('Запускаем w_d')
    for k in w_d:
        w_d[k] = sorted(w_d[k], key=lambda x: (x[0], x[1]))
        check(w_d)

    print('Запускаем m_d')
    for k in m_d:
        m_d[k] = sorted(m_d[k], key=lambda x: (x[0], x[1]))
        check(m_d)

