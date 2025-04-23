from docs.utils import copy_all_same_attrs


class Pairs:
    def __init__(self):
        self.id_boots = None
        self.left_border = None
        self.right_border = None
        self.id = None
        self.id_position = None
        self.current_step = None
        self.steps = None

    def __repr__(self):
        return f"{self.id}"

    def set_steps(self, steps):
        """Функция присваивания шагов паре ботинок"""
        self.steps = [step.get_deepcopy() for step in steps]
        if hasattr(self, "current_step"):
            min_step_num = None
            for step in self.steps:
                if step.sequence_num == self.current_step:
                    if min_step_num is None:
                        min_step_num = step.step_num
                    else:
                        min_step_num = min(min_step_num, step.sequence_num)
            if min_step_num is not None:
                for step in self.steps:
                    if step.sequence_num < min_step_num:
                        step.finished = True
        self.set_pair_id()

    def set_pair_attrs(self, position, pair_id):
        """Функция установки некоторых параметров пар ботинок"""
        self.id_boots = position.model_name
        self.left_border = position.left_border
        self.right_border = position.right_border
        self.id = pair_id
        self.id_position = position.id

    def set_pair_id(self):
        """Функция устанавливает индекс шагам пары"""
        for step in self.steps:
            step.id_pair = self.id

    def get_copy(self):
        """Функция возвращает копию пары ботинок"""
        pair_copy = Pairs()
        copy_all_same_attrs(pair_copy, self)
        pair_copy.steps = [step.get_deepcopy() for step in self.steps]
        return pair_copy
