from collections import defaultdict
from sqlalchemy import and_

from docs.database import get_table_data, TechCard
from docs.utils import copy_all_same_attrs


class Steps:

    steps = defaultdict(list)

    def __init__(self):
        self.id = None
        self.start_date = None
        self.end_date = None
        self.type_of_step = None
        self.step_name = None
        self.duration = None
        self.original_duration = None
        self.id_group_machine = None
        self.step_num = None
        self.sequence_num = None
        self.model_article = None
        self.type_tight = None
        self.type_sole = None
        self.id_position = None
        self.id_workplace = None
        self.id_pair = None
        self.shift = None
        self.finished = False
        self.string_mat_cat = None
        self.color = None
        self.splited = False

    def __repr__(self):
        return f"seq-{self.sequence_num}"

    @classmethod
    def setup_steps(cls):
        cls.steps = defaultdict(list)
        tech_cards: list[TechCard] = get_table_data(TechCard, and_(TechCard.id > 0, TechCard.id_group_machine > 0))
        for tech_card in tech_cards:
            step = Steps()
            copy_all_same_attrs(step, tech_card)
            step.original_duration = step.duration
            if tech_card.type_tight == tech_card.type_sole is None:
                cls.steps[None].append(step)
            if tech_card.type_sole is not None:
                cls.steps[tech_card.type_sole].append(step)
            if tech_card.type_tight is not None:
                cls.steps[tech_card.type_tight].append(step)

    @classmethod
    def get_steps(cls, key) -> list:
        result = []
        for step in cls.steps[key]:
            copied_step = Steps()
            copy_all_same_attrs(copied_step, step)
            result.append(copied_step)
        return result

    def get_deepcopy(self):
        deepcopy_step = Steps()
        copy_all_same_attrs(deepcopy_step, self)
        return deepcopy_step

    @staticmethod
    def convert_pairs_steps(steps):
        """Выгружает шаги из БД и преобразовывает их в объекты экземпляра класса Steps.
        :param steps: список шагов
        :type steps: list[PairsSteps]
        :return: обновленный список шагов
        """
        new_steps = []
        for step in steps:
            new_step = Steps()
            copy_all_same_attrs(new_step, step)
            new_steps.append(new_step)

        return new_steps
