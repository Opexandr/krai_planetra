from datetime import datetime
from sqlalchemy import update, case
from sqlalchemy.orm import Session

from docs.database import sync_engine as engine, PairsSteps, PositionsOutput, ProdOrder, PairsStepsWeek, \
    PositionsOutputWeek, PlansWeek, DailyShiftQuota
from docs.database import Plans, Serialize
from docs.utils import copy_all_same_attrs


def get_table_data(cls, conditions=None):
    """ Принимает класс в качестве аргумента и возвращает список объектов по условию
     или список всех объектов, которые хранятся в соответствующей таблице базы данных
    :param cls: класс
    :param conditions: условие для выгрузки
    :type conditions: bool
    :return: список объектов
    """
    with Session(engine) as session:
        if conditions is not None:
            return session.query(cls).filter(conditions).all()
        return session.query(cls).all()


def get_table_first(cls, conditions=None):
    """ Принимает класс в качестве аргумента и возвращает первый объект по условию
     или первый объект, который хранится в соответствующей таблице базы данных
    :param cls: класс
    :param conditions: условие для выгрузки
    :type conditions: bool
    :return: объект класса ``cls``
    """
    with Session(engine) as session:
        if conditions is not None:
            return session.query(cls).filter(conditions).first()
        return session.query(cls).first()


def send_duration_to_prod_orders(positions):
    with Session(engine) as session:
        position_map = {}
        for pos in positions:
            if pos.id and pos.duration_h:
                position_map[pos.id] = pos.duration_h

        if not position_map:
            return
        stmt = (
            update(ProdOrder)
            .where(ProdOrder.prod_order_id.in_(position_map.keys()))
            .values(duration_h=case(position_map, value=ProdOrder.prod_order_id))
        )
        session.execute(stmt)
        session.commit()

def clear_and_insert_table(cls, new_data=None, conditions=None):
    """ Принимает класс в качестве аргумента и очищает таблицу базы данных, затем вставляет в нее новые данные
    :param cls: класс
    :param new_data: новые данные
    :type new_data: list [object]
    :param conditions: условие для очистки
    :type conditions: bool
    :return: выгружает данные в БД
    """
    with Session(engine) as session:
        if conditions is not None:
            # Удаляем объекты из таблицы по условию
            session.query(cls).filter(conditions).delete()
            session.commit()
        else:
            # Очищаем таблицу
            session.query(cls).delete()
            session.commit()

        # Заполняем таблицу новыми данными
        try:
            if new_data:
                session.add_all(new_data)
                session.commit()
        except Exception as e:
            print(e)
            session.rollback()


def convert_pair_steps_to_db(step, plan_id, id_pair):
    """Преобразовывает объекты пар в формат, совместимый с БД, в экземпляр класса PairsSteps.
    :param step: шаг
    :type step: Steps
    :param plan_id: номер плана
    :type plan_id: int
    :param id_pair: идентификатор пары
    :type id_pair: int
    :return: список шагов
    """
    cls = PairsSteps
    if Serialize.is_week:
        cls = PairsStepsWeek
    db_pair = cls()
    copy_all_same_attrs(db_pair, step)
    db_pair.id_pair = id_pair
    db_pair.plan_id = plan_id

    return db_pair


def convert_positions_to_db(position, plan_id):
    """Преобразовывает объекты позиции в формат, совместимый с БД, в экземпляр класса PositionsOutput.
    :param position: список позиций
    :type position: Positions
    :param plan_id: номер цифрового двойника
    :type plan_id: int
    :return: список позиций
    """
    cls = PositionsOutput
    if Serialize.is_week:
        cls = PositionsOutputWeek
    db_positions = cls(

        prod_position_id=position.id,
        freeze=position.freeze,
        start_date=position.start_date,
        end_date=position.end_date,
        plan_id=plan_id,
        status=position.status
    )
    return db_positions


def save_steps_to_db(positions, plan_id):
    """Сохранение данных в таблицу 'pairs_steps' в БД.
    :param positions: список позиций
    :type positions: list [Positions]
    :param plan_id: номер цифрового двойника
    :type plan_id: int
    :return: выгружает список шагов в БД
    """
    db_pairs = []
    for position in positions:
        for pair in position.pairs:
            for step in pair.steps:
                db_pairs.append(convert_pair_steps_to_db(step, plan_id, pair.id))
    cls = PairsSteps
    if Serialize.is_week:
        cls = PairsStepsWeek
    condition = cls.plan_id == plan_id # задаем условие для очистки таблицы
    clear_and_insert_table(cls, db_pairs, condition) # передаем класс, список пар, условие для очистки таблицы


def save_positions_to_db(positions, plan_id):
    """Сохранение данных в таблицу 'PositionsOutput' в БД.
    :param positions: список позиций
    :type positions: list [Positions]
    :param plan_id: номер цифрового двойника
    :type plan_id: int
    :return: выгружает обновленный список позиций в БД
    """
    db_positions = []
    for position in positions:
        db_positions.append(convert_positions_to_db(position, plan_id))
    cls = PositionsOutput
    if Serialize.is_week:
        cls = PositionsOutputWeek
    condition = cls.plan_id == plan_id # задаем условие для очистки таблицы
    clear_and_insert_table(cls, db_positions, condition) # передаем класс, список заказов, условие для очистки таблицы


def save_daily_shift_quota_to_db(daily_shift_quota:list[tuple]):
    obj_list = []
    for quota_details in daily_shift_quota:
        quota = DailyShiftQuota()
        quota.responsible = quota_details.worker_name
        quota.workplace_id = quota_details.id_workplace
        quota.operation = quota_details.operation_name
        quota.quota = quota_details.quota
        quota.start_date = quota_details.start
        quota.end_date = quota_details.end
        quota.id_position = quota_details.id_position
        obj_list.append(quota)
    clear_and_insert_table(DailyShiftQuota, obj_list)


def save_plan_to_db(plan_id, cnt_suc, perc_suc, cnt_pr_or):
    if Serialize.is_week:
        cls = PlansWeek
    else:
        cls = Plans
    with Session(engine) as session:
        stmt = update(cls).where(cls.id == plan_id).values(optim_date=datetime.now(),
                                                               count_success=cnt_suc,
                                                               percent_success=perc_suc,
                                                               count_prod_order=cnt_pr_or
                                                               )
        session.execute(stmt)
        session.commit()


def save_positions_pairs(positions, pos_cls):
    if Serialize.is_week:
        cls = PlansWeek
    else:
        cls = Plans
    plans = get_table_data(cls)
    if not plans:
        plan_id = 1
    else:
        plan_id = max([plan.id for plan in plans])
    print(f"plan_id {plan_id}")
    save_steps_to_db(positions, plan_id)
    save_positions_to_db(positions, plan_id)
    if not Serialize.is_week:
        send_duration_to_prod_orders(positions)
        save_plan_to_db(plan_id, pos_cls.count_success, pos_cls.percent_success, pos_cls.count_prod_order)
