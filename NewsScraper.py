import requests
from bs4 import BeautifulSoup
import io
import sys
from google.colab.auth import authenticate_user
from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SOURCES = [
    ("Financial Express", "https://www.financialexpress.com/market/"),
    ("Economic Times", "https://economictimes.indiatimes.com/markets"),
    ("LiveMint", "https://www.livemint.com/market")
]

NEGATIVE_KEYWORDS = ["fall", "weak", "drop", "decline", "slump", "loss", "bear", "selloff",'HCLTECH','INFY']

def fetch_headlines(url):
    resp = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")
    return [h.get_text(strip=True) for h in soup.find_all(['h2','h3','a'])]

def is_negative(headline):
    text = headline.lower()
    return any(k in text for k in NEGATIVE_KEYWORDS)

def scrape_negative():
    output = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = output
    try:
        for name, url in SOURCES:
            print(f"\n## {name}")
            for hl in fetch_headlines(url):
                if is_negative(hl):
                    print(f"- {hl}")
    finally:
        sys.stdout = old_stdout
    return output.getvalue()

if __name__ == "__main__":
    # Authenticate the user
    authenticate_user()

    # Get credentials and build the service clients
    credentials, _ = default()
    drive_service = build('drive', 'v3', credentials=credentials)
    docs_service = build('docs', 'v1', credentials=credentials)

    negative_headlines_output = scrape_negative()
    print("Output captured successfully.")

    # Create a new Google Document
    try:
        title = 'Negative Stock Market Headlines'
        body = {
            'title': title
        }
        doc = docs_service.documents().create(body=body).execute()
        document_id = doc.get('documentId')
        print(f'Created document with ID: {document_id}')

        # Insert the captured output into the document
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': 1,
                    },
                    'text': negative_headlines_output
                }
            }
        ]

        result = docs_service.documents().batchUpdate(
            documentId=document_id, body={'requests': requests}).execute()
        print(f"Output saved to Google Document: https://docs.google.com/document/d/{document_id}/edit")

    except HttpError as error:
        print(f'An error occurred: {error}')
        document_id = None
