from docs.database import Demand, get_table_data


def get_netto_materials():
    """
    Функция берет все данные по необходимости материала на неделю и заполняет словарь следующим образом:\n
    ``{id_material:{date:netto}}``\n
    где:\n
    ``id_material`` - индекс материала\n
    ``date`` - дата начала недели\n
    ``netto`` - количество материала, которое необходимо закупить
    :return: Словарь нетто по каждому материалу
    :rtype: dict
    """
    demand_dict = {}
    demand_list: list[Demand] = get_table_data(Demand)
    for obj in demand_list:
        if obj.netto == 0:
            continue
        demand_dict[obj.material_id] = demand_dict.get(obj.material_id, {})
        demand_dict[obj.material_id][obj.date] = obj.netto
    for material_id in demand_dict:
        demand_dict[material_id] = dict(sorted(demand_dict[material_id].items()))

    return demand_dict


if __name__ == '__main__':
    print(get_netto_materials())
    for key, value in get_netto_materials().items():
        print(f"MATERIAL_ID = {key}")
        for k, v in value.items():
            print(f"{k} - {v}")
