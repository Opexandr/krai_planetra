from datetime import datetime, date
import pytest

from docs.classes import MachineCalendar


@pytest.mark.parametrize(
    'machine_usage, res',
    [   #Машина работает с 10-11, возвращаем временной промежуток с 09-10 и с 11 до 18
        ((datetime(2024, 11, 1, 10 ), datetime(2024, 11, 1, 11 ), None, None),
         [(datetime(2024,11,1,9), datetime(2024,11,1, 10), 1.0),
          (datetime(2024,11,1,11), datetime(2024,11,1, 18), 7.0) ]),
        #Машина работает с начала смены и до 11, возвращаем временной промежуток с 11 до конца смены
        ((datetime(2024, 11, 1, 9 ), datetime(2024, 11, 1, 11 ), None, None),
         [(datetime(2024,11,1,11), datetime(2024,11,1, 18), 7.0)]),
        #Машина работает с 11 до конца смены, возвращаем временной промежуток с начал смены до 11
        ((datetime(2024, 11, 1, 12 ), datetime(2024, 11, 1, 18 ), None, None),
         [(datetime(2024,11,1,9), datetime(2024,11,1, 12), 3.0)]),
        #Машина работает всю смену, возвращаем пустой список
        ((datetime(2024, 11, 1, 9), datetime(2024, 11, 1, 18), None, None),[]),
        #Машина работает с начал смены до 11 и с 14 до конца смены, возвращаем временной промежуток между 11 и 14
        ([(datetime(2024, 11, 1, 9 ), datetime(2024, 11, 1, 11 ), None, None),
          (datetime(2024, 11, 1, 14 ), datetime(2024, 11, 1, 18 ), None, None)],
         [(datetime(2024, 11, 1, 11), datetime(2024, 11, 1, 14), 3.0)]),
        #Машина работает с 10-11 и с 15 до 17, возвращаем временной промежуток от начала смены до 10, с 11 до 15 и с 17 до конца смены
        ([(datetime(2024, 11, 1, 10 ), datetime(2024, 11, 1, 11 ), None, None),
          (datetime(2024, 11, 1, 15 ), datetime(2024, 11, 1, 17 ), None, None)],
         [(datetime(2024, 11, 1, 9), datetime(2024, 11, 1, 10), 1.0),
          (datetime(2024, 11, 1, 11), datetime(2024, 11, 1, 15), 4.0),
          (datetime(2024, 11, 1, 17), datetime(2024, 11, 1, 18), 1.0)]),
        #Машина работает с 9-10, с 10 до 11, с 13 до 14, с 14 до 15, с 16 до 17. Возвращаем временной промежуток с 11 до 13, с 15 до 16 и с 17 до конца смены
        ([(datetime(2024, 11, 1, 9 ), datetime(2024, 11, 1, 10 ), None, None),
          (datetime(2024, 11, 1, 10 ), datetime(2024, 11, 1, 11 ), None, None),
          (datetime(2024, 11, 1, 13 ), datetime(2024, 11, 1, 14 ), None, None),
          (datetime(2024, 11, 1, 14 ), datetime(2024, 11, 1, 15 ), None, None),
          (datetime(2024, 11, 1, 16 ), datetime(2024, 11, 1, 17 ), None, None)],
         [(datetime(2024, 11, 1, 11), datetime(2024, 11, 1, 13), 2.0),
          (datetime(2024, 11, 1, 15), datetime(2024, 11, 1, 16), 1.0),
          (datetime(2024, 11, 1, 17), datetime(2024, 11, 1, 18), 1.0)]),
        #Машина не работает в смену, возвращаем полные часы
        ([],[(datetime(2024, 11, 1, 9), datetime(2024, 11, 1, 18), 9.0)])
    ]
)


def test_1(machine_usage, res):
    calendar = MachineCalendar()
    if isinstance(machine_usage,list):
        for usage in machine_usage:
            calendar.add_machine_usage(1, date(2024, 11, 1), 1, usage)
    else:
        calendar.add_machine_usage(1,  date(2024, 11, 1 ), 1, machine_usage)

    assert calendar.free_time_usage(1, date(2024, 11, 1 ), 1) == res



