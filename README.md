# Awwalumart - Vanilla E-Commerce

Simple e-commerce website with Google Sheets as database and WhatsApp ordering.

## Local Development

1. Clone the repository.
2. Install Python dependencies: `pip install -r requirements.txt`
3. Place your `credentials.json` in the `api/` folder.
4. Update the `SHEET_ID` in `api/index.py`.
5. Start the backend: `uvicorn api.index:app --reload --port 8000`
6. Open `index.html` in your browser.

## Deploy to Vercel

1. Push this project to GitHub.
2. On Vercel, import the repository.
3. Add environment variable: `GOOGLE_CREDENTIALS` with the entire JSON of your service account key.
4. Deploy.