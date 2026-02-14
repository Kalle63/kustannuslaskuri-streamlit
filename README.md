# quote_calc

Streamlit-pohjainen käännösprojektin kannattavuuslaskuri suomenkielisellä käyttöliittymällä.

## Ominaisuudet
- Projektin perustiedot (nimi, asiakas, kieliparit, päivämäärät)
- Tuotot käännöstyöstä kielipareittain (sanamäärä, EUR/sana, ALV)
- Tuotot lisäpalveluista (määrä, yksikkö, EUR/yksikkö, ALV)
- Työkustannukset rooleittain (tunnit * bruttopalkka * sivukulukerroin)
- Muut muuttuvat kustannukset
- Kate ja tunnusluvut (tuotto/sana, kustannus/sana, kate/sana)
- SQLite-historia
- HTML-raportin lataus
- Yksikkötestit hinnoittelulogiikalle

## Keskeiset kaavat
- `translation_net = sum(word_count * price_per_word)`
- `additional_net = sum(quantity * unit_price)`
- `total_revenue_net = translation_net + additional_net`
- `vat_amount = net_amount * vat_pct / 100`
- `labor_cost_total = sum(hours * gross_hourly_cost * side_cost_multiplier)`
- `variable_cost_total = labor_cost_total + other_cost_total`
- `contribution_margin = total_revenue_net - variable_cost_total`
- `contribution_margin_pct = contribution_margin / total_revenue_net * 100`
- `revenue_per_word = total_revenue_net / words_total` (jos sanoja > 0)

## Asennus
```bash
cd quote_calc
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Käynnistys
```bash
streamlit run app.py
```

## Testit
```bash
pytest -q
```
