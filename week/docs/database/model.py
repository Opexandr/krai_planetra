from datetime import datetime

from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from typing import Annotated

from docs.database import sync_engine
from docs.utils import setup_logger

logging = setup_logger(__name__)

intpk = Annotated[int, mapped_column(primary_key=True)]


class Base(DeclarativeBase):
    id: Mapped[intpk]
    table_args = {"schema": "public"}


class WorkerCalendarDB(Base):
    __tablename__ = "worker_calendar"

    calendar_id: Mapped[int]
    date_start: Mapped[datetime]
    date_end: Mapped[datetime]
    duration: Mapped[float]
    shift: Mapped[int]
    type: Mapped[str]
    version: Mapped[int]


class WorkerDB(Base):
    __tablename__ = "worker"

    post: Mapped[str]
    name: Mapped[str]
    rank: Mapped[str]
    worker_calendar_id: Mapped[int] = mapped_column(Integer, ForeignKey("worker_calendar.calendar_id"))
    coeff: Mapped[float]


class MachineCalendarDB(Base):
    __tablename__ = "machine_calendar"

    calendar_id: Mapped[int]
    date_start: Mapped[datetime]
    date_end: Mapped[datetime]
    duration: Mapped[float]
    shift: Mapped[int]
    type: Mapped[str]
    version: Mapped[int]


class MachineDB(Base):
    __tablename__ = "machine"

    post: Mapped[str]
    name: Mapped[str]
    rank: Mapped[str]
    machine_calendar_id: Mapped[int] = mapped_column(Integer, ForeignKey("machine_calendar.calendar_id"))


class WorkplaceDB(Base):
    __tablename__ = "workplace"

    worker_id: Mapped[int] = mapped_column(Integer, ForeignKey("worker.id"))
    machine_id: Mapped[int] = mapped_column(Integer, ForeignKey("machine.id"))
    operation_name: Mapped[str]
    active_date: Mapped[datetime]
    inactive_date: Mapped[datetime]


class EmergencyDB(Base):
    __tablename__ = "emergency"

    type: Mapped[str]
    start_date: Mapped[datetime]
    end_date: Mapped[datetime]
    machine_id: Mapped[int]
    responsible: Mapped[str]
    worker_id: Mapped[int]


class StepMaterials(Base):
    __tablename__ = "step_materials"


    id_step: Mapped[int]
    id_material: Mapped[int]
    amount: Mapped[float]


class Calendar(Base):
    __tablename__ = "calendar"


    id_machine: Mapped[int]
    date: Mapped[datetime]
    shift: Mapped[int]
    work_start: Mapped[datetime]
    work_end: Mapped[datetime]


class MachineEfficiency(Base):
    __tablename__ = "machine_efficiency"

    id_machine: Mapped[int]
    id_boots: Mapped[int]
    type_of_step: Mapped[str]
    coefficient: Mapped[float]


class MachineGroups(Base):
    __tablename__ = "machine_groups"

    id_group_machine: Mapped[int]
    id_machine: Mapped[int]


class Demand(Base):
    __tablename__ = "demand"

    material_id: Mapped[int]
    date: Mapped[datetime] # Start of the week
    brutto: Mapped[float] # Number of needed material
    netto: Mapped[float] # Number of needed material minus materials in storage
    plan_fact: Mapped[str]
    quantity: Mapped[float]


class ProdOrder(Base):
    __tablename__ = "prod_order"

    client_order_id: Mapped[int]
    plan_id: Mapped[int]
    quantity: Mapped[int]
    sole: Mapped[str]
    tie: Mapped[str]
    priority: Mapped[int]
    model_name: Mapped[str]
    freeze: Mapped[bool]
    prod_order_id: Mapped[int]
    duration_h: Mapped[float]


class ClientOrder(Base):
    __tablename__ = "client_order"

    deadline: Mapped[datetime]


class TechCard(Base):
    __tablename__ = "tech_card"

    type_of_step: Mapped[int]
    step_name: Mapped[str]
    duration: Mapped[float]  # seconds
    id_group_machine: Mapped[int]
    sequence_num: Mapped[int]
    model_article: Mapped[str]
    type_tight: Mapped[str]
    type_sole: Mapped[str]
    string_mat_cat: Mapped[str]


class PairsSteps(Base):
    __tablename__ = "pairs_steps"
    def __init__(self):
        self.id_position = None
        self.sequence_num = None
        self.id_workplace = None
        self.id_pair = None
        self.start_date = None
        self.end_date = None
        self.plan_id = None
        self.step_num = None
        self.shift = None

    id_position: Mapped[int]
    sequence_num: Mapped[int]
    id_workplace: Mapped[int]
    id_pair: Mapped[int]
    start_date: Mapped[datetime | None]
    end_date: Mapped[datetime | None]
    plan_id: Mapped[int]
    step_num: Mapped[int]
    shift: Mapped[int]


class PairsStepsWeek(Base):
    __tablename__ = "pairs_steps_week"
    def __init__(self):
        self.id_position = None
        self.sequence_num = None
        self.id_workplace = None
        self.id_pair = None
        self.start_date = None
        self.end_date = None
        self.plan_id = None
        self.step_num = None
        self.shift = None

    id_position: Mapped[int]
    sequence_num: Mapped[int]
    id_workplace: Mapped[int]
    id_pair: Mapped[int]
    start_date: Mapped[datetime | None]
    end_date: Mapped[datetime | None]
    plan_id: Mapped[int]
    step_num: Mapped[int]
    shift: Mapped[int]


class PositionsOutput(Base):
    __tablename__ = "positions_output"

    prod_position_id: Mapped[int]
    freeze: Mapped[bool | None] = mapped_column(default=False)
    start_date: Mapped[datetime | None]
    end_date: Mapped[datetime | None]
    plan_id: Mapped[int]
    status: Mapped[str]


class PositionsOutputWeek(Base):
    __tablename__ = "positions_output_week"

    prod_position_id: Mapped[int]
    freeze: Mapped[bool | None] = mapped_column(default=False)
    start_date: Mapped[datetime | None]
    end_date: Mapped[datetime | None]
    plan_id: Mapped[int]
    status: Mapped[str]


class OptimizeParamsBase(Base):
    __abstract__ = True

    defect: Mapped[float]
    is_supply: Mapped[bool]
    is_deadline: Mapped[bool]
    is_positions_coeffs: Mapped[bool]
    workload_calendar: Mapped[float]
    digital_twin: Mapped[int]


class OptimizeParams(OptimizeParamsBase):
    __tablename__ = "optimize_params"


class OptimizeParamsWeek(OptimizeParamsBase):
    __tablename__ = "optimize_params_week"


class OrderRations(Base):
    __tablename__ = "position_rations"

    customer_type: Mapped[str]
    coefficient: Mapped[float]
    plan_id: Mapped[int]


class SortCriteria(Base):
    __tablename__ = "sort_criteria"

    name: Mapped[str]
    priority: Mapped[int | None]
    reverse: Mapped[bool | None]


class ThreeMonthPositions(Base):
    __tablename__ = "three_month_positions_approved"

    type_of_position: Mapped[str]
    id_boots: Mapped[int]
    quantity: Mapped[int]
    price: Mapped[float]
    deadline: Mapped[datetime | None]
    number_of_stars: Mapped[int | None] = mapped_column(default=0)
    customer_coefficient: Mapped[float | None]
    freeze: Mapped[bool | None] = mapped_column(default=False)
    quarantine: Mapped[bool | None] = mapped_column(default=False)

    start_date: Mapped[datetime | None]
    end_date: Mapped[datetime | None]
    plan_id: Mapped[int]


class WeeklyPositions(Base):
    __tablename__ = "weekly_positions_approved"

    type_of_position: Mapped[str]
    id_boots: Mapped[int]
    duration: Mapped[float]
    quantity: Mapped[int]
    price: Mapped[float]
    want_date: Mapped[datetime | None]
    deadline: Mapped[datetime | None]
    number_of_stars: Mapped[int | None] = mapped_column(default=0)
    customer_coefficient: Mapped[float | None]
    freeze: Mapped[bool | None] = mapped_column(default=False)
    quarantine: Mapped[bool | None] = mapped_column(default=False)

    start_date: Mapped[datetime | None]
    end_date: Mapped[datetime | None]
    plan_id: Mapped[int]


class PairsKS(Base):
    __tablename__ = "pair_ks"

    id_position: Mapped[int]
    status: Mapped[str]
    current_step: Mapped[int]


class Suppliers(Base):
    __tablename__ = "suppliers"

    name: Mapped[str]
    reliability:Mapped[int]
    inn: Mapped[int]
    contact: Mapped[str]
    email: Mapped[str]
    deal_count: Mapped[int]
    transport_type: Mapped[str]
    conditions: Mapped[str]
    city: Mapped[str]
    code: Mapped[str]


class Supplies(Base):
    __tablename__ = "supplies"

    id_supplier: Mapped[int]
    id_material: Mapped[int]
    quantity: Mapped[int]
    plan_date: Mapped[datetime | None]
    fact_date: Mapped[datetime | None]
    plan_defect: Mapped[int]
    fact_defect: Mapped[int]
    chosen: Mapped[bool]
    status: Mapped[str]
    price: Mapped[int]


class SupsParams(Base):
    __tablename__ = "sups_params"

    price: Mapped[int]
    plan_date: Mapped[datetime | None]
    reliability: Mapped[int]
    plan_defect: Mapped[int]
    budget: Mapped[int]


class Plans(Base):
    __tablename__ = "plans"

    optim_date: Mapped[datetime]
    count_success: Mapped[int]
    percent_success: Mapped[int]
    count_prod_order: Mapped[int]


class PlansWeek(Base):
    __tablename__ = "plans_weekly"

    optim_date: Mapped[datetime]
    count_success: Mapped[int]
    percent_success: Mapped[int]
    count_prod_order: Mapped[int]


class PosStrings(Base):
    __tablename__ = "position_strings"

    prod_order_id: Mapped[int]
    category: Mapped[str]
    color: Mapped[str]


class DailyShiftQuota(Base):
    __tablename__ = "daily_shift_quota"

    responsible: Mapped[str]
    workplace_id: Mapped[int]
    operation: Mapped[str]
    quota: Mapped[int]
    start_date: Mapped[datetime]
    end_date: Mapped[datetime]
    id_position: Mapped[int]


try:
    """Создание таблицы, если какая-то отсутствует"""
    Base.metadata.create_all(bind=sync_engine)
    logging.info(list(Base.metadata.tables.keys()))
except Exception as e:
    logging.error("ошибка создания таблицы", exc_info=e)
