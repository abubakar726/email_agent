import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# --- Email Extraction Function (No Selenium) ---
def extract_emails_from_main_page(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        for tag in soup(['script', 'style', 'meta', 'noscript']):
            tag.decompose()

        visible_text = soup.get_text(separator=' ', strip=True)

        emails = set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}", visible_text))

        excluded_domains = ['sentry.io', 'wixpress.com', 'sentry.wixpress.com']
        image_extensions = ('.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp')

        valid_emails = {
            e for e in emails
            if all(domain not in e.lower() for domain in excluded_domains)
            and not e.lower().endswith(image_extensions)
        }

        return ', '.join(valid_emails) if valid_emails else "❌ No valid email found"

    except Exception as e:
        return f"❌ Error: {str(e)}"


# --- Streamlit Interface ---
st.set_page_config(page_title="Email Scraper", layout="centered")
st.title("📬 Website Email Scraper (Streamlit Cloud Friendly)")

urls_input = st.text_area("Paste website URLs (one per line)", height=200)

if st.button("🔍 Scrape Emails"):
    urls = urls_input.strip().splitlines()
    results = []

    for url in urls:
        url = url.strip()
        if not url.startswith('http'):
            url = 'https://' + url
        with st.spinner(f"Scraping: {url}"):
            email_result = extract_emails_from_main_page(url)
            st.success(f"{url} → {email_result}")
            results.append({"Website": url, "Email": email_result})

    df = pd.DataFrame(results)

    # --- CSV Download ---
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📅 Download Results as CSV",
        data=csv,
        file_name="emails.csv",
        mime='text/csv'
    )
