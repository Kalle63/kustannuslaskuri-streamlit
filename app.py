from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from models import (
    AdditionalServiceLine,
    LaborCostLine,
    OtherCostLine,
    ProjectQuoteInput,
    TranslationRevenueLine,
)
from pricing import calculate_project_quote
from report import generate_report_html
from storage import get_quote_history, init_db, save_quote

st.set_page_config(page_title="Käännösprojektin kannattavuuslaskuri", layout="wide")
init_db()

st.title("Käännösprojektin kannattavuuslaskuri")

tab_laskuri, tab_historia = st.tabs(["Laskuri", "Historia"])


with tab_laskuri:
    st.subheader("1. Projektin perustiedot")

    with st.form("project_form"):
        project_name = st.text_input("Projektin nimi", placeholder="Esim. Käyttöohjeen käännös")
        customer_name = st.text_input("Asiakas", placeholder="Esim. Oy Käännöstoimisto Ab")
        c1, c2 = st.columns(2)
        with c1:
            language_pairs_text = st.text_input("Kielipari(t)", placeholder="Esim. EN, ES, FR -> FI")
            text_type = st.text_input("Tekstityyppi", placeholder="Esim. tekninen käyttöohje")
        with c2:
            start_date = st.date_input("Aloituspäivä", value=None)
            end_date = st.date_input("Päättymispäivä", value=None)

        st.subheader("2. Tuotot: käännöstyö")
        translation_df = st.data_editor(
            pd.DataFrame(
                [
                    {"Kielipari": "EN -> FI", "Sanamäärä": 0, "EUR/sana": 0.18, "ALV %": 25.5},
                    {"Kielipari": "", "Sanamäärä": 0, "EUR/sana": 0.18, "ALV %": 25.5},
                    {"Kielipari": "", "Sanamäärä": 0, "EUR/sana": 0.18, "ALV %": 25.5},
                    {"Kielipari": "", "Sanamäärä": 0, "EUR/sana": 0.18, "ALV %": 25.5},
                    {"Kielipari": "", "Sanamäärä": 0, "EUR/sana": 0.18, "ALV %": 25.5},
                ]
            ),
            num_rows="dynamic",
            width='stretch',
            key="translation_editor",
        )

        st.subheader("3. Tuotot: lisäpalvelut")
        service_df = st.data_editor(
            pd.DataFrame(
                [
                    {"Palvelu": "Sanasto", "Määrä": 0.0, "Yksikkö": "kpl", "EUR/yksikkö": 50.0, "ALV %": 25.5},
                    {"Palvelu": "Käännösmuisti", "Määrä": 0.0, "Yksikkö": "kpl", "EUR/yksikkö": 50.0, "ALV %": 25.5},
                ]
            ),
            num_rows="dynamic",
            width='stretch',
            key="service_editor",
        )

        st.subheader("4. Työkustannukset")
        labor_df = st.data_editor(
            pd.DataFrame(
                [
                    {
                        "Rooli": "Kääntäjä",
                        "Tunnit": 0.0,
                        "Bruttopalkka EUR/h": 30.0,
                        "Sivukulukerroin": 1.3,
                    },
                    {
                        "Rooli": "Projektipäällikkö",
                        "Tunnit": 0.0,
                        "Bruttopalkka EUR/h": 35.0,
                        "Sivukulukerroin": 1.3,
                    },
                ]
            ),
            num_rows="dynamic",
            width='stretch',
            key="labor_editor",
        )

        st.subheader("5. Muut muuttuvat kustannukset")
        other_df = st.data_editor(
            pd.DataFrame(
                [
                    {"Kulu": "CAT-työkalu", "Summa EUR": 0.0},
                    {"Kulu": "Alihankinta", "Summa EUR": 0.0},
                ]
            ),
            num_rows="dynamic",
            width='stretch',
            key="other_editor",
        )

        submitted = st.form_submit_button("Laske ja tallenna")

    if submitted:
        try:
            translation_lines = [
                TranslationRevenueLine(
                    language_pair=str(row["Kielipari"]).strip(),
                    word_count=int(row["Sanamäärä"]),
                    price_per_word=float(row["EUR/sana"]),
                    vat_pct=float(row["ALV %"]),
                )
                for _, row in translation_df.iterrows()
                if str(row.get("Kielipari", "")).strip()
                and float(row.get("Sanamäärä", 0)) > 0
                and float(row.get("EUR/sana", 0)) > 0
            ]

            service_lines = [
                AdditionalServiceLine(
                    service_name=str(row["Palvelu"]).strip(),
                    quantity=float(row["Määrä"]),
                    unit=str(row["Yksikkö"]).strip() or "kpl",
                    unit_price=float(row["EUR/yksikkö"]),
                    vat_pct=float(row["ALV %"]),
                )
                for _, row in service_df.iterrows()
                if str(row.get("Palvelu", "")).strip() and float(row.get("Määrä", 0)) > 0
            ]

            labor_lines = [
                LaborCostLine(
                    role_name=str(row["Rooli"]).strip(),
                    hours=float(row["Tunnit"]),
                    gross_hourly_cost=float(row["Bruttopalkka EUR/h"]),
                    side_cost_multiplier=float(row["Sivukulukerroin"]),
                )
                for _, row in labor_df.iterrows()
                if str(row.get("Rooli", "")).strip() and float(row.get("Tunnit", 0)) > 0
            ]

            other_lines = [
                OtherCostLine(cost_name=str(row["Kulu"]).strip(), amount=float(row["Summa EUR"]))
                for _, row in other_df.iterrows()
                if str(row.get("Kulu", "")).strip() and float(row.get("Summa EUR", 0)) != 0
            ]

            quote_input = ProjectQuoteInput(
                project_name=project_name,
                customer_name=customer_name,
                language_pairs_text=language_pairs_text or None,
                text_type=text_type or None,
                start_date=start_date,
                end_date=end_date,
                translation_revenues=translation_lines,
                additional_services=service_lines,
                labor_costs=labor_lines,
                other_costs=other_lines,
            )

            result = calculate_project_quote(quote_input)
            html_report = generate_report_html(quote_input, result)
            quote_id = save_quote(quote_input, result, html_report)

            stamped_report = generate_report_html(
                quote_input,
                result,
                quote_id=quote_id,
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

            st.success(f"Projekti tallennettu (ID: {quote_id}).")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Kokonaistuotto (veroton)", f"{result.total_revenue_net:.2f} EUR")
            m2.metric("Muuttuvat kustannukset", f"{result.variable_cost_total:.2f} EUR")
            m3.metric("Kate", f"{result.contribution_margin:.2f} EUR")
            m4.metric("Kate-%", f"{result.contribution_margin_pct:.2f} %")

            m5, m6, m7 = st.columns(3)
            m5.metric("Tuotto/sana", f"{result.revenue_per_word:.4f} EUR")
            m6.metric("Kustannus/sana", f"{result.cost_per_word:.4f} EUR")
            m7.metric("Kate/sana", f"{result.margin_per_word:.4f} EUR")

            st.download_button(
                label="Lataa HTML-raportti",
                data=stamped_report.encode("utf-8"),
                file_name=f"projekti_{quote_id}.html",
                mime="text/html",
            )

            if result.translation_lines:
                st.markdown("**Käännöstyön rivit**")
                st.dataframe([line.model_dump() for line in result.translation_lines], width='stretch')
            if result.additional_service_lines:
                st.markdown("**Lisapalvelurivit**")
                st.dataframe([line.model_dump() for line in result.additional_service_lines], width='stretch')
            if result.labor_lines:
                st.markdown("**Työkustannusrivit**")
                st.dataframe([line.model_dump() for line in result.labor_lines], width='stretch')
            if result.other_cost_lines:
                st.markdown("**Muut kustannusrivit**")
                st.dataframe([line.model_dump() for line in result.other_cost_lines], width='stretch')

        except ValidationError as exc:
            for err in exc.errors():
                location = ".".join(str(item) for item in err["loc"])
                st.error(f"Virhe kentässä '{location}': {err['msg']}")

with tab_historia:
    st.subheader("Projektihistoria")
    history = get_quote_history()

    if not history:
        st.info("Historiassa ei ole tallennettuja projekteja.")
    else:
        table_rows = [
            {
                "ID": row.id,
                "Luotu": row.created_at,
                "Projekti": row.project_name or "-",
                "Asiakas": row.customer_name,
                "Kokonaistuotto": f"{(row.total_revenue_net if row.total_revenue_net is not None else (row.price_excl_vat or 0.0)):.2f} EUR",
                "Kustannukset": f"{(row.variable_cost_total or 0.0):.2f} EUR",
                "Kate": f"{(row.contribution_margin if row.contribution_margin is not None else (row.profit_amount or 0.0)):.2f} EUR",
                "Kate-%": f"{(row.contribution_margin_pct if row.contribution_margin_pct is not None else (row.profitability_pct or 0.0)):.2f} %",
            }
            for row in history
        ]
        st.dataframe(table_rows, width='stretch')

        selected_id = st.selectbox(
            "Valitse projekti raportin lataukseen",
            options=[row.id for row in history],
            format_func=lambda item: f"Projekti #{item}",
        )
        selected = next(row for row in history if row.id == selected_id)

        st.download_button(
            label="Lataa valittu raportti (HTML)",
            data=selected.report_html.encode("utf-8"),
            file_name=f"projekti_{selected.id}.html",
            mime="text/html",
        )
