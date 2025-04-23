from collections import defaultdict, Counter, namedtuple
from datetime import timedelta, time, datetime

from docs.classes.workplace_class import WorkPlaces
from docs.database import ProdOrder, ClientOrder, get_table_data, Serialize
from docs.classes.steps_class import Steps
from docs.database.model import PairsKS, PosStrings
from docs.classes.pairs import Pairs
from docs.utils import print_red, copy_all_same_attrs


class Positions:

    positions = []
    count_success = 0
    percent_success = 0
    count_prod_order = 0

    def __init__(self):
        self.id = None
        self.start_date = None
        self.end_date = None
        self.deadline = None
        self.supply_date = None
        self.left_border = None
        self.right_border = None
        self.plan_id = None
        self.quantity = None
        self.sole = None
        self.tie = None
        self.number_of_stars = None
        self.model_name = None
        self.freeze = None
        self.duration = None
        self.free_space = None
        self.steps = None
        self.pairs = None
        self.status = None
        self.duration_h = None
        self.top = None
        self.bot = None
        self.sole = None

    def __repr__(self):
        return f"{self.id}"

    @staticmethod
    def set_duration(pos_dates):
        for position in Positions.positions:
            if position.freeze or position.duration_h:
                continue
            position.duration_h = pos_dates[position.id]['dur']

    def calc_duration(self):
        duration = 0
        for step in self.steps:
            duration += step.duration
        self.duration = duration * self.quantity

    def calc_start_end(self):
        min_start = datetime(year=3000, month=12, day=1)
        max_end = datetime(year=2000, month=1, day=1)
        for pair in self.pairs:
            for step in pair.steps:
                if not step.start_date or not step.end_date:
                    print(f"Какой-то косяк с заморозкой. pos {self.id} pair {pair.id} step_num {step.step_num} start {step.start_date} end {step.end_date}")
                    continue
                min_start = min(min_start, step.start_date)
                max_end = max(max_end, step.end_date)
        self.start_date = min_start
        self.end_date = max_end

    def set_free_space(self):
        """Функция устанавливает время на которое можно сдвигать позицию, не выходя за границы"""
        self.free_space = self.right_border - self.left_border - timedelta(seconds=self.duration)

    def accounting_for_defects(self, defect_rate):
        """Функция увеличивает длительность шагов в зависимости от процента брака"""
        for step in self.steps:
            step.duration *= (1 + defect_rate / 100)

    def fill_missing_position_values(self):
        """Приводит некоторые параметры к значениям для сравнения"""
        if self.freeze is None:
            self.freeze = False
        if self.number_of_stars is None:
            self.number_of_stars = 0

    def set_borders(self, optimize_params):
        """Устанавливает левую и правую границу позиций"""

        if optimize_params.is_supply and self.supply_date:
            self.left_border = max(self.supply_date, Serialize.start_date)
        else:
            self.left_border = Serialize.start_date

        if optimize_params.is_deadline and self.deadline:
            self.right_border = datetime.combine(self.deadline.date(), time(0, 0, 0))
        else:
            # Если мы отключаем учет дедлайнов, то правая граница будет установлена через 50 лет после левой
            self.right_border = self.left_border + timedelta(days=50 * 365)

    def set_borders_week(self, optimize_params):
        """Устанавливает левую или правую границу позиций для недельного оптимизатора"""

        if optimize_params.is_supply and self.supply_date:
            self.left_border = max(self.supply_date, Serialize.start_date)
        else:
            self.left_border = Serialize.start_date

        if optimize_params.is_deadline and self.deadline:
            self.right_border = min(datetime.combine(self.deadline.date(), time(0, 0, 0)),
                                    Serialize.start_date + timedelta(days=7))
        else:
            # Если мы отключаем учет дедлайнов, то правая граница будет установлена через неделю после запуска оптимизатора
            self.right_border = Serialize.start_date + timedelta(days=7)

    @classmethod
    def set_pairs(cls):
        """Устанавливает пары для каждой позиции"""
        pairs_ks: list[PairsKS] = get_table_data(PairsKS)
        positions_pairs_id = defaultdict(list)
        for pair in pairs_ks:
            positions_pairs_id[pair.id_position].append((pair.id, pair.status, pair.current_step))
        for position in cls.positions:
            pairs = []
            # чтобы пары шли по порядку
            positions_pairs_id[position.id] = sorted(positions_pairs_id[position.id], key=lambda x: x[0], reverse=True)
            for _ in range(position.quantity):
                try:
                    id_pair, status, current_step = positions_pairs_id[position.id].pop()
                    if status != Serialize.get_status("Закончен"):
                        pair = Pairs()
                        pair.set_pair_attrs(position, id_pair)
                        pair.current_step = current_step
                        pair.set_steps(position.steps)
                        pairs.append(pair)
                except IndexError:
                    print_red(f"В БД НЕ ХВАТАЕТ ПАР ДЛЯ ПОЗИЦИИ - {position.id}\n"
                              f"КОЛИЧЕСТВО НЕДОСТАЮЩИХ ПАР - {position.quantity - _}")
                    break
            position.pairs = pairs

    @classmethod
    def _set_positions(cls, plan_id, ids=None):
        """Скачивает позиции"""
        cls.positions = []
        cls.count_success = 0
        cls.percent_success = 0
        cls.count_prod_order = 0

        all_positions = get_table_data(ProdOrder)
        db_positions = []
        pos_tie_sole = {}
        for pos in all_positions:
            if not pos.prod_order_id and not pos.plan_id:
                pos_tie_sole[pos.id] = (pos.tie, pos.sole)

        for pos in all_positions:
            if pos.plan_id == plan_id and (not ids or pos.id in ids):
                pos.tie, pos.sole = pos_tie_sole[pos.prod_order_id]
                db_positions.append(pos)

        db_client_order = get_table_data(ClientOrder)

        client_deadline = {}

        for client_order in db_client_order:
            client_deadline[client_order.id] = client_order.deadline

        for position in db_positions:
            position: ProdOrder
            new_position = Positions()

            copy_all_same_attrs(new_position, position)

            new_position.id = position.prod_order_id
            new_position.deadline = client_deadline.get(position.client_order_id)
            new_position.number_of_stars = position.priority

            cls.positions.append(new_position)

    @classmethod
    def get_positions(cls, optimize_params, plan_id, ids=None):
        cls._set_positions(plan_id, ids)
        cls._setup_steps_for_positions()
        for position in cls.positions:
            position: Positions
            position.fill_missing_position_values()
            if Serialize.is_week:
                position.set_borders_week(optimize_params)
            else:
                position.set_borders(optimize_params)
            position.calc_duration()
            position.set_free_space()
            position.accounting_for_defects(optimize_params.defect)
            if Serialize.is_week:
                position._calculate_colors()
        cls.set_pairs()
        return cls.positions

    @classmethod
    def _set_pos_steps(cls):
        pos_ids = {}
        pos_steps_category_colors = get_table_data(PosStrings)
        for row in pos_steps_category_colors:
            pos_ids[row.prod_order_id] = pos_ids.get(row.prod_order_id, {})
            pos_ids[row.prod_order_id][row.category] = row.color
        return pos_ids


    @classmethod
    def _setup_steps_for_positions(cls):
        Steps.setup_steps()
        pos_steps_colors = Positions._set_pos_steps()
        for position in cls.positions:
            position: Positions
            position.steps = []
            position.steps.extend(Steps.get_steps(None))
            if position.tie is not None:
                position.steps.extend(Steps.get_steps(position.tie))
            if position.sole is not None:
                position.steps.extend(Steps.get_steps(position.sole))

            position.steps.sort(key=lambda x: x.sequence_num)
            i = 1
            for step in position.steps:
                if step.string_mat_cat and Serialize.get_command() == "Недельный оптимизатор":
                    try:
                        step.color = pos_steps_colors[position.id][step.string_mat_cat]
                    except Exception as e:
                        step.color = None
                step.id_position = position.id
                step.step_num = i
                i += 1

    def _calculate_colors(self):
        """Метод определяет наиболее часто встречающийся цвет ниток среди всех шагов
         пары и присваивает этот цвет паре в зависимости от её категории"""
        colors_count = namedtuple("color_count", "color count")

        top, bot, sole = [], [], []
        for step in self.steps:
            if step.string_mat_cat == "Верх":
                top.append(step.color)
            elif step.string_mat_cat == "Подошва":
                sole.append(step.color)
            elif step.string_mat_cat == "Низ":
                bot.append(step.color)
        top_color, bot_color, sole_color = (Counter(top).most_common(1), Counter(bot).most_common(1),
                                            Counter(sole).most_common(1))
        if top_color:
            top_color = colors_count(*top_color[0])
            self.top = top_color.color
        if bot_color:
            bot_color = colors_count(*bot_color[0])
            self.bot = bot_color.color
        if sole_color:
            sole_color = colors_count(*sole_color[0])
            self.sole = sole_color.color
        for step in self.steps:
            if step.string_mat_cat == "Верх":
                step.color = top_color.color
            elif step.string_mat_cat == "Низ":
                step.color = bot_color.color
            elif step.string_mat_cat == "Подошва":
                step.color = sole_color.color

    def get_copy(self):
        position_copy = Positions()
        copy_all_same_attrs(position_copy, self)
        position_copy.steps = [step.get_deepcopy() for step in self.steps]
        position_copy.pairs = [pair.get_copy() for pair in self.pairs]
        return position_copy

    @classmethod
    def get_daily_shift_quota(cls):
        workplaces = WorkPlaces()
        shift_for_machines = 1
        daily_shift_quota = defaultdict(dict)
        quota_tuple = namedtuple("quota", "start end quota")
        for position in cls.positions:
            for pair in position.pairs:
                for step in pair.steps:
                    workplace = step.id_workplace
                    start = step.start_date
                    if start is None:
                        continue
                    end = step.end_date
                    cal_date = start.date()
                    machine_calendar = workplaces.machine_calendar

                    shift_start, shift_end = machine_calendar.get_period(workplace, cal_date, shift_for_machines)
                    if start < shift_start:
                        cal_date -= timedelta(days=1)
                        shift_start, shift_end = machine_calendar.get_period(workplace, cal_date, shift_for_machines)
                    shift_period = (shift_start, shift_end)

                    quota_details = (workplace, position.id, step.step_name)
                    if daily_shift_quota[shift_period].get(quota_details) is None:
                        quota = quota_tuple(start, end, 1)
                        daily_shift_quota[shift_period][quota_details] = quota
                    else:
                        quota = daily_shift_quota[shift_period][quota_details]
                        new_start = min(quota.start, start)
                        new_end = max(quota.end, end)
                        new_quota = quota_tuple(new_start, new_end, quota.quota + 1)
                        daily_shift_quota[shift_period][quota_details] = new_quota

        daily_shift_quota_list = []
        daily_shift_quota_tuple = namedtuple("daily_shift_quota",
                                             "start "
                                             "end "
                                             "operation_name "
                                             "quota "
                                             "worker_name "
                                             "id_workplace "
                                             "id_position")
        for quota_dict in daily_shift_quota.values():
            for quota_details, quota in quota_dict.items():
                id_workplace, id_position, step_name = quota_details
                worker_name = workplaces.get_workers_name(id_workplace)
                d_s_q = daily_shift_quota_tuple(quota.start,
                                                quota.end,
                                                step_name,
                                                quota.quota,
                                                worker_name,
                                                id_workplace,
                                                id_position)
                daily_shift_quota_list.append(d_s_q)

        return daily_shift_quota_list
