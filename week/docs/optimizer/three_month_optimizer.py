from datetime import datetime

from docs.optimizer import create_plan, calc_pos_duration
from docs.database import OptimizeParams, save_positions_pairs, get_table_first, send_duration_to_prod_orders
from docs.optimizer.preparation_phase import set_frozen_data
from docs.optimizer.data_verification import check_impossible_position
from docs.classes import WorkPlaces, Positions


# def extend_pos_n_time(positions, n):
#     new = []
#     for i in range(n):
#         for p in positions:
#             if p.freeze:
#                 continue
#             new.append(deepcopy(p))
#     positions.extend(new)


def three_month_start(plan_id: int = 0):
    t1 = datetime.now()
    workplaces = WorkPlaces()
    workplaces.reset_calendar()
    optimize_params = get_table_first(OptimizeParams, conditions=OptimizeParams.id == 1)
    positions = Positions.get_positions(optimize_params, plan_id)
    set_frozen_data(positions, plan_id)
    check_impossible_position(positions)
    #extend_pos_n_time(positions, 10)
    pos_dates = calc_pos_duration(positions)
    Positions.set_duration(pos_dates)
    send_duration_to_prod_orders(positions)
    create_plan(positions)
    save_positions_pairs(positions, Positions)
    t2 = datetime.now()
    print(f'{(t2-t1).total_seconds():.2f} секунд')


if __name__ == '__main__':
    three_month_start()
    #check_impossible_position(start_date=start_date, plan_id=0)
