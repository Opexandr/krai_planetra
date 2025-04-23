from docs.database import MachineGroups, get_table_data


class MGroups:
    def __init__(self):
        self.machine_groups = {}
        self.machines = {}
        self.__set_machine_groups()

    def __set_machine_groups(self) -> None:
        """
        Загружает группы машин из БД и формирует их в словарь следующего формата:\n
        {``группа_машин``: [``машина1``, ``машина2``, и т.д.]}

        """
        downloaded_machine_groups: list[MachineGroups] = get_table_data(MachineGroups)
        for m_group_obj in downloaded_machine_groups:
            self.machine_groups[m_group_obj.id_group_machine] = self.machine_groups.get(m_group_obj.id_group_machine, [])
            self.machine_groups[m_group_obj.id_group_machine].append(m_group_obj.id_machine)

            self.machines[m_group_obj.id_machine] = self.machines.get(m_group_obj.id_machine, [])
            self.machines[m_group_obj.id_machine].append(m_group_obj.id_group_machine)

    def get_machines(self, machine_group) -> list:
        """Возвращает список машин для заданной группы машин"""
        return self.machine_groups[machine_group]

    def get_machine_groups(self, id_machine) -> list:
        """Возвращает список групп оборудования для данной машины"""
        return self.machines.get(id_machine, [])


machine_groups = MGroups()
