from sqlalchemy import and_

from docs.classes import Positions
from docs.classes.steps_class import Steps
from docs.database import get_table_data, PairsSteps, PairsStepsWeek, Serialize


def set_frozen_data(positions, plan_id):
    """
    Для замороженных позиций среди позиций проставляет пары и шаги пар
    :param positions: список позиций
    :type positions: list[Positions]
    :param plan_id: цифровой двойник
    :type plan_id: int
    :return:
    """
    frozen_positions = {}
    frozen_positions_ids = []
    pairs_d = {}
    pairs_index = {}
    for position in positions:
        if position.freeze:
            for i, pair in enumerate(position.pairs):
                pairs_d[pair.id] = pair
                pair.steps = []
                pairs_index[pair.id] = i

            frozen_positions[position.id] = position
            frozen_positions_ids.append(position.id)
    if not frozen_positions:
        return
    cls = PairsSteps
    if Serialize.is_week:
        cls = PairsStepsWeek
    filter_by = and_(cls.id_position.in_(frozen_positions_ids), cls.plan_id == plan_id)
    pairst_steps = get_table_data(cls, filter_by)
    steps = Steps.convert_pairs_steps(pairst_steps)
    # разбить шаги по парам и позициям
    steps_pairs = {}
    for step in steps:
        steps_pairs[step.id_position] = steps_pairs.get(step.id_position, {})
        steps_pairs[step.id_position][step.id_pair] = steps_pairs[step.id_position].get(step.id_pair, [])
        steps_pairs[step.id_position][step.id_pair].append(step)

    for id_position in steps_pairs:
        for id_pair in steps_pairs[id_position]:
            for step in steps_pairs[id_position][id_pair]:
                frozen_positions[step.id_position].pairs[pairs_index[id_pair]].steps = steps_pairs[id_position][id_pair]

    for position_id in frozen_positions:
        for pair in frozen_positions[position_id].pairs:
            pair.steps = sorted(pair.steps, key=lambda x: x.step_num)
        frozen_positions[position_id].calc_start_end()
