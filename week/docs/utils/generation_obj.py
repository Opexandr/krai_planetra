from random import randint
from datetime import datetime, timedelta, date

from docs.database import Positions, Steps, get_table_data, clear_and_insert_table, MachineGroups, MachineEfficiency, \
    Calendar, Supplies


def generation_steps()-> None:
    """Функция создает шаги для позиций"""
    steps = []
    positions = get_table_data(Positions)
    for position in positions:
        prev_step = 1
        for i in range(1, 6):
            step = Steps()
            step.id_position = position.id
            step.id_group_machine = randint(1, 5)
            step.duration = randint(5, 30)
            step.type_of_step = 1
            if i > prev_step:
                step.step_num = randint(prev_step, prev_step + 1)
                if step.step_num == prev_step:
                    pass
                else:
                    prev_step += 1
            else:
                step.step_num = prev_step
            steps.append(step)

    clear_and_insert_table(Steps, steps)


def generation_machines()-> None:
    """Функция создает группы машин и машины"""
    machines = []
    for i in range(1, 6):
        for j in range(1,4):
            uniq_id=[]
            machine = MachineGroups()
            machine.id_group_machine = i
            while True:
                id_machine = randint(1, 10)
                if id_machine not in uniq_id:
                    uniq_id.append(id_machine)
                    machine.id_machine = id_machine
                    break
            machines.append(machine)
    clear_and_insert_table(MachineGroups, machines)


def generation_machines_efficiency()-> None:
    """Функция создает машины"""
    machinescf=[]
    for i in range(1,11):
        machine = MachineEfficiency()
        machine.id_machine = i
        machine.coefficient = 1
        machine.type_of_step = 1
        machine.id_boots = 1
        machinescf.append(machine)
    clear_and_insert_table(MachineEfficiency, machinescf)


def generation_shift_calendar(start_date=datetime(2024, 10, 1), rng=90)-> None:
    """Функция создает рабочие промежутки для машин"""
    calendar = []
    for machine in range(1, 11):
        if machine == 3:
            continue
        for day in range(rng):
            equipment = Calendar()
            equipment.id_machine = machine
            equipment.date = start_date +timedelta(days=day)
            equipment.shift = 1
            equipment.work_start = start_date +timedelta(days=day, hours=9)
            equipment.work_end = start_date +timedelta(days=day, hours=18)
            calendar.append(equipment)
    clear_and_insert_table(Calendar,calendar)


def generation_supplies():
    """Функция создает поставки в таблице поставок"""
    start_date = date(2025, 1, 1)
    end_date = date(2025, 1, 10)
    random_days = randint(0, (end_date - start_date).days)
    supplies = []
    for _ in range(60):
        supplie = Supplies()
        random_days = randint(0, (end_date - start_date).days)
        supplie.plan_date = start_date + timedelta(days=random_days)
        supplie.id_supplier = randint(1, 4)
        supplie.id_material = randint(1, 2)
        supplie.price = randint(1, 150000)
        supplie.quantity = randint(5, 30)
        supplie.plan_defect = 1
        supplie.status = 'ex'
        supplies.append(supplie)
    clear_and_insert_table(Supplies, supplies)

if __name__ == '__main__':
    generation_shift_calendar()