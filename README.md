# Duct Factory Dashboard

Minimal Streamlit mock dashboard for duct manufacturing.

## What it shows

- KPI cards
- Factory floor layout map
- Machine utilization circles
- WIP hour circles
- Started / last-updated timestamps
- WIP and completed job tables
- Mock operator update form

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy

1. Push these files to GitHub.
2. Open Streamlit Community Cloud.
3. Connect the GitHub repo.
4. Set the main file as `app.py`.
5. Deploy.

## Future version

Replace CSV files with a database. Operators can update jobs from a phone, tablet, or shop-floor computer.
