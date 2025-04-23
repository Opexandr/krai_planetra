from datetime import datetime, timedelta

from docs.database import get_table_data, ThreeMonthPositions, Serialize


#TODO не запутаться в шагах из Steps и шагах из Techcard

#TODO сортировать пары надо по цветам этим, потом вставлять начинать все пары подряд
# сортируем дл/пост по цветам, вставляем все подряд текущим алгоритмом? по идее должно работать, нужно добавить учет на переналадку

# а мы учитываем индивидуальных швей? может помечать позиции индивидуальными и швей индивидуальными как-то, и только им давать позиции эти? можно оставить на будущее наработку

# для подсчета переналадок надо запоминать машину и шаг который делалася в какое время, чтобы обойти их все

# А что если создать пары как в месячном, а потом поверх пройтись и скорректировать уже выполненные

# а в недельном мы шаги не дробим

def get_period_positions_ids(plan_id, period=7):
    positions = get_table_data(ThreeMonthPositions, conditions=ThreeMonthPositions.plan_id == plan_id and
                                                               ThreeMonthPositions.start_date >= Serialize.start_date and
                                                               ThreeMonthPositions.start_date <= Serialize.start_date + timedelta(days=period))

    return [pos.id for pos in positions]


# что есть верх, низ и подошва
def week_pos_sort(positions):
    positions = sorted(positions, key=lambda x: (x.right_border, x.top, x.bot, x.sole))
    return positions


if __name__ == '__main__':
    ids = get_period_positions(datetime(2025, 2, 24), 65)
    print(ids)
