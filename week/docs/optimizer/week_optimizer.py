from datetime import datetime

from docs.optimizer import create_plan
from docs.database import OptimizeParamsWeek, save_positions_pairs, get_table_first, save_daily_shift_quota_to_db
from docs.optimizer.preparation_phase import set_frozen_data
from docs.optimizer.data_verification import check_impossible_position
from docs.optimizer.week_funcs import get_period_positions_ids
from docs.classes import WorkPlaces, Positions


def week_start(plan_id: int = 0):
    t1 = datetime.now()
    workplaces = WorkPlaces()
    workplaces.reset_calendar()
    optimize_params = get_table_first(OptimizeParamsWeek, conditions=OptimizeParamsWeek.id == 1)
    week_ids = get_period_positions_ids(plan_id)
    positions = Positions.get_positions(optimize_params, plan_id, week_ids)
    set_frozen_data(positions, plan_id)
    check_impossible_position(positions)
    create_plan(positions)
    daily_list = Positions.get_daily_shift_quota()
    save_daily_shift_quota_to_db(daily_list)
    #workplaces.print_changeovers()
    #workplaces.print_colors_with_date()
    #save_positions_pairs(positions, Positions)
    t2 = datetime.now()
    print(f'{(t2-t1).total_seconds():.2f} секунд')

    # должны учитываться другие календари (но они потом) нужно проверить обеспеченность позиций
    # надо смотреть на склад для материала позиций там будет приход(поставки) и расход


if __name__ == '__main__':
    week_start()
