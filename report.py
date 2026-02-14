from __future__ import annotations

from datetime import datetime

import pandas as pd

from models import ProjectCalculation, ProjectQuoteInput


def _eur(value: float) -> str:
    return f"{value:,.2f} EUR".replace(",", " ")


def build_export_frames(quote: ProjectQuoteInput, result: ProjectCalculation) -> dict[str, pd.DataFrame]:
    perustiedot = pd.DataFrame(
        [
            {"Kenttä": "Projektin nimi", "Arvo": quote.project_name},
            {"Kenttä": "Asiakas", "Arvo": quote.customer_name},
            {"Kenttä": "Kieliparit", "Arvo": quote.language_pairs_text or ""},
            {"Kenttä": "Tekstityyppi", "Arvo": quote.text_type or ""},
            {"Kenttä": "Aloituspäivä", "Arvo": quote.start_date.isoformat() if quote.start_date else ""},
            {"Kenttä": "Päättymispäivä", "Arvo": quote.end_date.isoformat() if quote.end_date else ""},
        ]
    )

    kaannostyo = pd.DataFrame(
        [
            {
                "Kielipari": line.name,
                "Sanamäärä": int(line.quantity),
                "EUR/sana": line.unit_price,
                "Veroton EUR": line.net_amount,
                "ALV %": line.vat_pct,
                "ALV EUR": line.vat_amount,
                "Brutto EUR": line.gross_amount,
            }
            for line in result.translation_lines
        ]
    )

    lisapalvelut = pd.DataFrame(
        [
            {
                "Palvelu": line.name,
                "Määrä": line.quantity,
                "EUR/yksikkö": line.unit_price,
                "Veroton EUR": line.net_amount,
                "ALV %": line.vat_pct,
                "ALV EUR": line.vat_amount,
                "Brutto EUR": line.gross_amount,
            }
            for line in result.additional_service_lines
        ]
    )

    tyokustannukset = pd.DataFrame(
        [
            {
                "Rooli": line.role_name,
                "Tunnit": line.hours,
                "Bruttopalkka EUR/h": line.gross_hourly_cost,
                "Sivukulukerroin": line.side_cost_multiplier,
                "Yhteensä EUR": line.total_cost,
            }
            for line in result.labor_lines
        ]
    )

    muut_kulut = pd.DataFrame(
        [{"Kulu": line.cost_name, "Summa EUR": line.amount} for line in result.other_cost_lines]
    )

    yhteenveto = pd.DataFrame(
        [
            {"Tunnusluku": "Kokonaistuotto veroton", "Arvo": result.total_revenue_net},
            {"Tunnusluku": "Kokonaistuotto ALV", "Arvo": result.total_revenue_vat},
            {"Tunnusluku": "Kokonaistuotto brutto", "Arvo": result.total_revenue_gross},
            {"Tunnusluku": "Muuttuvat kustannukset", "Arvo": result.variable_cost_total},
            {"Tunnusluku": "Kate", "Arvo": result.contribution_margin},
            {"Tunnusluku": "Kate-%", "Arvo": result.contribution_margin_pct},
            {"Tunnusluku": "Tuotto/sana", "Arvo": result.revenue_per_word},
            {"Tunnusluku": "Kustannus/sana", "Arvo": result.cost_per_word},
            {"Tunnusluku": "Kate/sana", "Arvo": result.margin_per_word},
        ]
    )

    return {
        "Perustiedot": perustiedot,
        "Käännöstyö": kaannostyo,
        "Lisäpalvelut": lisapalvelut,
        "Työkustannukset": tyokustannukset,
        "Muut kulut": muut_kulut,
        "Yhteenveto": yhteenveto,
    }


def generate_report_html(
    quote: ProjectQuoteInput,
    result: ProjectCalculation,
    quote_id: int | None = None,
    created_at: str | None = None,
) -> str:
    timestamp = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header_id = f"Projekti #{quote_id}" if quote_id is not None else "Projekti"

    translation_rows = "".join(
        f"<tr><td>{line.name}</td><td>{line.quantity:.0f}</td><td>{line.unit_price:.4f}</td>"
        f"<td>{_eur(line.net_amount)}</td><td>{line.vat_pct:.2f} %</td><td>{_eur(line.vat_amount)}</td><td>{_eur(line.gross_amount)}</td></tr>"
        for line in result.translation_lines
    ) or "<tr><td colspan='7'>Ei rivejä</td></tr>"

    service_rows = "".join(
        f"<tr><td>{line.name}</td><td>{line.quantity:.2f}</td><td>{line.unit_price:.2f}</td>"
        f"<td>{_eur(line.net_amount)}</td><td>{line.vat_pct:.2f} %</td><td>{_eur(line.vat_amount)}</td><td>{_eur(line.gross_amount)}</td></tr>"
        for line in result.additional_service_lines
    ) or "<tr><td colspan='7'>Ei rivejä</td></tr>"

    labor_rows = "".join(
        f"<tr><td>{line.role_name}</td><td>{line.hours:.2f}</td><td>{_eur(line.gross_hourly_cost)}</td>"
        f"<td>{line.side_cost_multiplier:.2f}</td><td>{_eur(line.total_cost)}</td></tr>"
        for line in result.labor_lines
    ) or "<tr><td colspan='5'>Ei rivejä</td></tr>"

    other_rows = "".join(
        f"<tr><td>{line.cost_name}</td><td>{_eur(line.amount)}</td></tr>" for line in result.other_cost_lines
    ) or "<tr><td colspan='2'>Ei rivejä</td></tr>"

    return f"""
<!doctype html>
<html lang="fi">
<head>
  <meta charset="utf-8" />
  <title>{header_id}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #1c1c1c; }}
    h1, h2 {{ margin-bottom: 8px; }}
    .meta {{ margin-bottom: 20px; color: #555; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; margin-bottom: 20px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background: #f2f2f2; }}
    .summary td:first-child {{ font-weight: bold; width: 320px; }}
  </style>
</head>
<body>
  <h1>{header_id}: {quote.project_name}</h1>
  <div class="meta">Luotu: {timestamp}</div>

  <h2>Projektin perustiedot</h2>
  <table>
    <tr><th>Asiakas</th><td>{quote.customer_name}</td></tr>
    <tr><th>Kieliparit</th><td>{quote.language_pairs_text or '-'}</td></tr>
    <tr><th>Tekstityyppi</th><td>{quote.text_type or '-'}</td></tr>
    <tr><th>Aloituspäivä</th><td>{quote.start_date or '-'}</td></tr>
    <tr><th>Päättymispäivä</th><td>{quote.end_date or '-'}</td></tr>
  </table>

  <h2>Tuotot: käännöstyö</h2>
  <table>
    <tr><th>Kielipari</th><th>Sanamäärä</th><th>EUR/sana</th><th>Veroton</th><th>ALV</th><th>ALV EUR</th><th>Brutto</th></tr>
    {translation_rows}
  </table>

  <h2>Tuotot: lisäpalvelut</h2>
  <table>
    <tr><th>Palvelu</th><th>Määrä</th><th>EUR/yksikkö</th><th>Veroton</th><th>ALV</th><th>ALV EUR</th><th>Brutto</th></tr>
    {service_rows}
  </table>

  <h2>Työkustannukset</h2>
  <table>
    <tr><th>Rooli</th><th>Tunnit</th><th>Bruttopalkka/h</th><th>Sivukulukerroin</th><th>Yhteensä</th></tr>
    {labor_rows}
  </table>

  <h2>Muut muuttuvat kustannukset</h2>
  <table>
    <tr><th>Kulu</th><th>Summa</th></tr>
    {other_rows}
  </table>

  <h2>Yhteenveto</h2>
  <table class="summary">
    <tr><td>Kokonaistuotto veroton</td><td>{_eur(result.total_revenue_net)}</td></tr>
    <tr><td>Kokonaistuotto ALV</td><td>{_eur(result.total_revenue_vat)}</td></tr>
    <tr><td>Kokonaistuotto brutto</td><td>{_eur(result.total_revenue_gross)}</td></tr>
    <tr><td>Muuttuvat kustannukset yhteensä</td><td>{_eur(result.variable_cost_total)}</td></tr>
    <tr><td>Kate</td><td>{_eur(result.contribution_margin)}</td></tr>
    <tr><td>Kate-%</td><td>{result.contribution_margin_pct:.2f} %</td></tr>
    <tr><td>Tuotto/sana</td><td>{result.revenue_per_word:.4f} EUR</td></tr>
    <tr><td>Kustannus/sana</td><td>{result.cost_per_word:.4f} EUR</td></tr>
    <tr><td>Kate/sana</td><td>{result.margin_per_word:.4f} EUR</td></tr>
  </table>
</body>
</html>
""".strip()
