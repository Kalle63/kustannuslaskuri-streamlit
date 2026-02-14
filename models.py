from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TranslationRevenueLine(BaseModel):
    language_pair: str = Field(min_length=1)
    word_count: int = Field(gt=0)
    price_per_word: float = Field(gt=0)
    vat_pct: float = Field(ge=0, le=100, default=25.5)


class AdditionalServiceLine(BaseModel):
    service_name: str = Field(min_length=1)
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, default="kpl")
    unit_price: float
    vat_pct: float = Field(ge=0, le=100, default=25.5)


class LaborCostLine(BaseModel):
    role_name: str = Field(min_length=1)
    hours: float = Field(gt=0)
    gross_hourly_cost: float = Field(gt=0)
    side_cost_multiplier: float = Field(ge=1)


class OtherCostLine(BaseModel):
    cost_name: str = Field(min_length=1)
    amount: float


class ProjectQuoteInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    project_name: str = Field(min_length=1)
    customer_name: str = Field(min_length=1)
    language_pairs_text: Optional[str] = None
    text_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    translation_revenues: list[TranslationRevenueLine] = Field(default_factory=list)
    additional_services: list[AdditionalServiceLine] = Field(default_factory=list)
    labor_costs: list[LaborCostLine] = Field(default_factory=list)
    other_costs: list[OtherCostLine] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_dates(self) -> ProjectQuoteInput:
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("Päättymispäivä ei voi olla ennen aloituspäivää.")
        if not self.translation_revenues and not self.additional_services:
            raise ValueError("Syötä vähintään yksi tuottorivi (käännöstyö tai lisäpalvelu).")
        return self


class RevenueLineResult(BaseModel):
    name: str
    quantity: float
    unit_price: float
    vat_pct: float
    net_amount: float
    vat_amount: float
    gross_amount: float


class LaborLineResult(BaseModel):
    role_name: str
    hours: float
    gross_hourly_cost: float
    side_cost_multiplier: float
    total_cost: float


class OtherCostLineResult(BaseModel):
    cost_name: str
    amount: float


class ProjectCalculation(BaseModel):
    translation_lines: list[RevenueLineResult]
    additional_service_lines: list[RevenueLineResult]
    labor_lines: list[LaborLineResult]
    other_cost_lines: list[OtherCostLineResult]

    words_total: int

    translation_revenue_net: float
    translation_revenue_vat: float
    translation_revenue_gross: float

    additional_revenue_net: float
    additional_revenue_vat: float
    additional_revenue_gross: float

    total_revenue_net: float
    total_revenue_vat: float
    total_revenue_gross: float

    labor_cost_total: float
    other_cost_total: float
    variable_cost_total: float

    contribution_margin: float
    contribution_margin_pct: float

    revenue_per_word: float
    cost_per_word: float
    margin_per_word: float


class QuoteHistoryRecord(BaseModel):
    id: int
    created_at: str
    customer_name: str
    project_name: Optional[str] = None

    total_revenue_net: Optional[float] = None
    total_revenue_gross: Optional[float] = None
    variable_cost_total: Optional[float] = None
    contribution_margin: Optional[float] = None
    contribution_margin_pct: Optional[float] = None

    input_json: Optional[str] = None
    result_json: Optional[str] = None
    report_html: str

    # Legacy fields for backwards compatibility with old rows.
    price_excl_vat: Optional[float] = None
    price_incl_vat: Optional[float] = None
    profit_amount: Optional[float] = None
    profitability_pct: Optional[float] = None

    @field_validator("project_name", mode="before")
    @classmethod
    def fallback_project_name(cls, value: Optional[str]) -> Optional[str]:
        return value
