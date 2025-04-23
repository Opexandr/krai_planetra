from copy import deepcopy
from sqlalchemy import update
from sqlalchemy.orm import Session

from docs.database import Supplies, sync_engine as engine, get_table_data, SupsParams, Suppliers
from demand import get_netto_materials


def preparation_of_supplies(supplies):
    """Функция подготавливает поставки к работе, добавляя и проставляя атрибут reliability
    :param supplies: Список поставок
    :type supplies: list[Supplies]
    :return: None"""
    suppliers = get_table_data(Suppliers)
    suppliers_dict = {}
    rm = []
    for supplier in suppliers:
        suppliers_dict[supplier.id] = supplier.reliability
    for i, supply in enumerate(supplies):
        if supply.id_supplier in suppliers_dict and supply.plan_date:
            supply.reliability = suppliers_dict[supply.id_supplier]
        elif supply.id_supplier not in suppliers_dict or supply.plan_date is None:
            rm.append(i)

    for i in reversed(rm):
        supplies.pop(i)
        print(f'Для поставки {supply.id} нет поставщика или даты, пропущена')


            # supply.first = False


def sorted_supplies(supplies, priority_obj):
    """Cортирует поставки по указанным критериям и приоритету.
    :param supplies: Список поставок.
    :type supplies: list[Supplies]
    :param priority_obj: Список критериев сортировки
    :type priority_obj: SupsParams
    :return: Отсортированный список поставок."""
    sort_criteria = [('price', priority_obj.price),
                     ('plan_date', priority_obj.plan_date),
                     ('reliability', priority_obj.reliability),
                     ('plan_defect', priority_obj.plan_defect)]
    filtered_criteria = []
    for crt in sort_criteria:
        if crt[1] != 0 and crt[1] is not None:
            filtered_criteria.append(crt)
    # Сортируем по убыванию значений в этих колонках
    sorted_criteria = sorted(filtered_criteria, key=lambda x: x[1], reverse=True)
    sorted_criteria_names = [crt[0] for crt in sorted_criteria]
    # Сортируем поставки по указанным критериям и приоритету в порядке возрастания
    supplies = sorted(supplies, key=lambda x: [getattr(x, crt) for crt in sorted_criteria_names], reverse=False)
    return supplies


def break_up_supplies(supplies):
    """Функция разбивает отсортированный список поставок ``supplies`` и группирует их по
    значению атрибута ``id_material``, возвращая словарь, где каждый ключ — это уникальный ``id_material``, а значение —
    список объектов ``supply``, которые имеют этот ``id_material.``
    :param supplies: список поставок
    :type supplies: list[Supplies]
    :return: словарь поставок по кадому материалу
    :rtype: dict"""
    supps_dict = {}
    for supply in supplies:
        if supply.id_material not in supps_dict:
            supps_dict[supply.id_material] = []
        supps_dict[supply.id_material].append(supply)
    return supps_dict


def search_for_supplies(supplies, supplies_dict, demand):
    """Рассчитывает общую стоимость выбранных поставок для удовлетворения текущей потребности. Функция выбирает
    подходящие поставки на основе даты и количества, помечая выбранные поставки и обновляя остатки потребности.
    :param supplies: Список поставок
    :type supplies: list[Supplies]
    :param supplies_dict: Словарь, содержащий поставки по каждому материалу
    :type supplies_dict: dict
    :param demand: Словарь, содержащий потребность на материалы по дате и количеству
    :type demand: dict
    :return: общую стоимость выбранных поставок"""
    for supply in supplies:
        supply.chosen = False
        supply.selected = False

    total_price = 0
    for id_material in demand:
        remainder = 0
        for date, quantity in demand[id_material].items():
            if remainder >= quantity:
                remainder -= quantity
                continue
            for supply in supplies_dict[id_material]:
                if supply.plan_date.date() < date.date() and not supply.selected:
                    supply.selected = True
                    supply.chosen = True
                    total_price += supply.price
                    if supply.quantity + remainder >= quantity:
                        remainder += supply.quantity - quantity
                        demand[id_material][date] = 0
                        break
                    else:
                        quantity -= supply.quantity
                        demand[id_material][date] = quantity
    return total_price


def supplies_planning(supplies, parameters, demand_dict):
    """Оптимизирует список поставок, чтобы общая стоимость не превышала заданный бюджет, с учетом
     таких критериев, как дата, цена, надежность и уровень дефектов. Функция итеративно корректирует
    критерии и переоценивает выбор до тех пор, пока общая стоимость не будет в пределах бюджета или
    пока цена не станет самым приоритетным критерием сортировки
    :param supplies: список поставок
    :type supplies: list[Supplies]
    :param parameters: Критерии сортировки
    :type parameters: SupsParams
    :param demand_dict: Словарь, содержащий потребность на материалы по дате и количеству
    :type demand_dict: dict"""
    criteria_was_changed = True
    total_price = parameters.budget + 1
    # iteration = 0
    # supplies_first = []
    while total_price > parameters.budget and criteria_was_changed == True:
        # iteration += 1
        supplies = sorted_supplies(supplies, parameters)
        supplies_dict = break_up_supplies(supplies)
        demand = deepcopy(demand_dict)
        total_price = search_for_supplies(supplies, supplies_dict, demand)
        # if iteration == 1:
        #     supplies_first = deepcopy(supplies)
        attr_obj = [('plan_date', parameters.plan_date), ('reliability', parameters.reliability),
                    ('plan_defect', parameters.plan_defect)]
        sort_criteria = sorted(attr_obj, key=lambda x: x[1], reverse=False)
        criteria = []
        criteria_was_changed = False
        for crt in sort_criteria:
            criteria.append(crt[0])
        for i in criteria:
            # Цену сравниваем с атрибутами объекта класса parameters, ищем следующий по величине критерий
            if parameters.price - getattr(parameters, i) < 0:
                criteria_was_changed = True
                price = parameters.price
                parameters.price = getattr(parameters, i)
                setattr(parameters, i, price)
                break
    # if total_price > parameters.budget:
    #     return supplies_first
    return supplies


def update_supplies(supplies):
    """Функция обновляет столбец chosen в таблице supplies в БД
    :param supplies: список поставок
    :type supplies: list [Supplies]"""
    with Session(engine) as session:
        for supply in supplies:
            stmt = update(Supplies).where(Supplies.id == supply.id).values(chosen=supply.chosen)
            session.execute(stmt)
        session.commit()


def optimize_supplies():
    """Функция вызывает загрузку, выборку и выгрузку поставок"""
    parameters = get_table_data(SupsParams)[0]
    data_filter = (Supplies.id > 0) & (Supplies.status == "Предложение")
    supplies = get_table_data(Supplies, data_filter)
    preparation_of_supplies(supplies)
    demand_dict = get_netto_materials()
    supplies = supplies_planning(supplies, parameters, demand_dict)
    #update_supplies(supplies)


if __name__ == "__main__":
    optimize_supplies()
