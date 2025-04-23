from docs.database import MachineEfficiency, get_table_data


class MEfficiency:
    def __init__(self):
        self.efficiency = {}
        downloaded_efficiency: list[MachineEfficiency] = get_table_data(MachineEfficiency)
        for object in downloaded_efficiency:
            self.efficiency[object.id_machine, object.id_boots, object.type_of_step] = object.coefficient

    def get_coeff(self, id_machine, id_boots, type_of_step) -> float:
        """
        :param id_machine: Индекс машины
        :param id_boots: Индекс ботинок
        :param type_of_step: Тип шага
        :return: Возвращает коэффициент эффективности
        """
        return self.efficiency[id_machine, id_boots, type_of_step]


machine_eff = MEfficiency()
