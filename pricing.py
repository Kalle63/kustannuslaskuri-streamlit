from __future__ import annotations

from models import (
    LaborLineResult,
    OtherCostLineResult,
    ProjectCalculation,
    ProjectQuoteInput,
    RevenueLineResult,
)


def _round2(value: float) -> float:
    return round(value + 1e-9, 2)


def _round4(value: float) -> float:
    return round(value + 1e-12, 4)


def _build_revenue_line(name: str, quantity: float, unit_price: float, vat_pct: float) -> RevenueLineResult:
    net_amount = quantity * unit_price
    vat_amount = net_amount * (vat_pct / 100)
    gross_amount = net_amount + vat_amount
    return RevenueLineResult(
        name=name,
        quantity=quantity,
        unit_price=unit_price,
        vat_pct=vat_pct,
        net_amount=_round2(net_amount),
        vat_amount=_round2(vat_amount),
        gross_amount=_round2(gross_amount),
    )


def calculate_project_quote(data: ProjectQuoteInput) -> ProjectCalculation:
    translation_lines = [
        _build_revenue_line(
            name=row.language_pair,
            quantity=float(row.word_count),
            unit_price=row.price_per_word,
            vat_pct=row.vat_pct,
        )
        for row in data.translation_revenues
    ]

    additional_service_lines = [
        _build_revenue_line(
            name=row.service_name,
            quantity=row.quantity,
            unit_price=row.unit_price,
            vat_pct=row.vat_pct,
        )
        for row in data.additional_services
    ]

    labor_lines = [
        LaborLineResult(
            role_name=row.role_name,
            hours=row.hours,
            gross_hourly_cost=row.gross_hourly_cost,
            side_cost_multiplier=row.side_cost_multiplier,
            total_cost=_round2(row.hours * row.gross_hourly_cost * row.side_cost_multiplier),
        )
        for row in data.labor_costs
    ]

    other_cost_lines = [
        OtherCostLineResult(cost_name=row.cost_name, amount=_round2(row.amount)) for row in data.other_costs
    ]

    words_total = sum(row.word_count for row in data.translation_revenues)

    translation_revenue_net = _round2(sum(line.net_amount for line in translation_lines))
    translation_revenue_vat = _round2(sum(line.vat_amount for line in translation_lines))
    translation_revenue_gross = _round2(sum(line.gross_amount for line in translation_lines))

    additional_revenue_net = _round2(sum(line.net_amount for line in additional_service_lines))
    additional_revenue_vat = _round2(sum(line.vat_amount for line in additional_service_lines))
    additional_revenue_gross = _round2(sum(line.gross_amount for line in additional_service_lines))

    total_revenue_net = _round2(translation_revenue_net + additional_revenue_net)
    total_revenue_vat = _round2(translation_revenue_vat + additional_revenue_vat)
    total_revenue_gross = _round2(total_revenue_net + total_revenue_vat)

    labor_cost_total = _round2(sum(line.total_cost for line in labor_lines))
    other_cost_total = _round2(sum(line.amount for line in other_cost_lines))
    variable_cost_total = _round2(labor_cost_total + other_cost_total)

    contribution_margin = _round2(total_revenue_net - variable_cost_total)
    contribution_margin_pct = _round2((contribution_margin / total_revenue_net * 100) if total_revenue_net > 0 else 0.0)

    revenue_per_word = _round4(total_revenue_net / words_total) if words_total > 0 else 0.0
    cost_per_word = _round4(variable_cost_total / words_total) if words_total > 0 else 0.0
    margin_per_word = _round4(contribution_margin / words_total) if words_total > 0 else 0.0

    return ProjectCalculation(
        translation_lines=translation_lines,
        additional_service_lines=additional_service_lines,
        labor_lines=labor_lines,
        other_cost_lines=other_cost_lines,
        words_total=words_total,
        translation_revenue_net=translation_revenue_net,
        translation_revenue_vat=translation_revenue_vat,
        translation_revenue_gross=translation_revenue_gross,
        additional_revenue_net=additional_revenue_net,
        additional_revenue_vat=additional_revenue_vat,
        additional_revenue_gross=additional_revenue_gross,
        total_revenue_net=total_revenue_net,
        total_revenue_vat=total_revenue_vat,
        total_revenue_gross=total_revenue_gross,
        labor_cost_total=labor_cost_total,
        other_cost_total=other_cost_total,
        variable_cost_total=variable_cost_total,
        contribution_margin=contribution_margin,
        contribution_margin_pct=contribution_margin_pct,
        revenue_per_word=revenue_per_word,
        cost_per_word=cost_per_word,
        margin_per_word=margin_per_word,
    )
