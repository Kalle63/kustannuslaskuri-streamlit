from datetime import date

from pydantic import ValidationError

from models import (
    AdditionalServiceLine,
    LaborCostLine,
    OtherCostLine,
    ProjectQuoteInput,
    TranslationRevenueLine,
)
from pricing import calculate_project_quote


def test_project_calculation_full_case() -> None:
    quote = ProjectQuoteInput(
        project_name="Delonghi",
        customer_name="Oy KahviKas! Ab",
        language_pairs_text="EN, ES, FR -> FI",
        text_type="Kayttoohje",
        start_date=date(2026, 1, 27),
        end_date=date(2026, 2, 6),
        translation_revenues=[
            TranslationRevenueLine(language_pair="EN -> FI", word_count=1354, price_per_word=0.18, vat_pct=25.5),
            TranslationRevenueLine(language_pair="ES -> FI", word_count=1438, price_per_word=0.18, vat_pct=25.5),
            TranslationRevenueLine(language_pair="FR -> FI", word_count=1383, price_per_word=0.18, vat_pct=25.5),
        ],
        additional_services=[
            AdditionalServiceLine(service_name="Sanasto EN->FI", quantity=1, unit="kpl", unit_price=50, vat_pct=25.5),
            AdditionalServiceLine(service_name="Sanasto ES->FI", quantity=1, unit="kpl", unit_price=50, vat_pct=25.5),
        ],
        labor_costs=[
            LaborCostLine(role_name="Kaantaja", hours=20, gross_hourly_cost=30, side_cost_multiplier=1.3),
            LaborCostLine(role_name="Projektipaallikko", hours=8, gross_hourly_cost=35, side_cost_multiplier=1.3),
        ],
        other_costs=[
            OtherCostLine(cost_name="CAT-tyokalu", amount=25),
            OtherCostLine(cost_name="QA-tyokalu", amount=15),
        ],
    )

    result = calculate_project_quote(quote)

    assert result.words_total == 4175
    assert result.translation_revenue_net == 751.50
    assert result.additional_revenue_net == 100.00
    assert result.total_revenue_net == 851.50
    assert result.total_revenue_vat == 217.13
    assert result.total_revenue_gross == 1068.63

    assert result.labor_cost_total == 1144.00
    assert result.other_cost_total == 40.00
    assert result.variable_cost_total == 1184.00

    assert result.contribution_margin == -332.50
    assert result.contribution_margin_pct == -39.05
    assert result.revenue_per_word == 0.204
    assert result.cost_per_word == 0.2836
    assert result.margin_per_word == -0.0796


def test_project_calculation_without_words() -> None:
    quote = ProjectQuoteInput(
        project_name="Vain lisapalvelu",
        customer_name="Asiakas Oy",
        additional_services=[
            AdditionalServiceLine(service_name="Projektinhallinta", quantity=3, unit="h", unit_price=60, vat_pct=25.5)
        ],
        labor_costs=[LaborCostLine(role_name="PM", hours=2, gross_hourly_cost=40, side_cost_multiplier=1.3)],
    )

    result = calculate_project_quote(quote)

    assert result.words_total == 0
    assert result.total_revenue_net == 180.00
    assert result.variable_cost_total == 104.00
    assert result.contribution_margin == 76.00
    assert result.revenue_per_word == 0.0
    assert result.cost_per_word == 0.0
    assert result.margin_per_word == 0.0


def test_invalid_date_range() -> None:
    try:
        ProjectQuoteInput(
            project_name="Virhe",
            customer_name="Asiakas",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 1, 31),
            translation_revenues=[
                TranslationRevenueLine(language_pair="EN -> FI", word_count=100, price_per_word=0.2, vat_pct=25.5)
            ],
        )
    except ValidationError:
        pass
    else:
        raise AssertionError("Date validation should fail when end_date is before start_date.")


def test_requires_revenue_rows() -> None:
    try:
        ProjectQuoteInput(
            project_name="Virhe",
            customer_name="Asiakas",
            labor_costs=[LaborCostLine(role_name="PM", hours=1, gross_hourly_cost=50, side_cost_multiplier=1.3)],
        )
    except ValidationError:
        pass
    else:
        raise AssertionError("Model should fail without translation or additional service revenue rows.")
