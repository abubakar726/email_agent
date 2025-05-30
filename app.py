import streamlit as st
import pandas as pd
import re
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- Email Extraction Function ---
def extract_emails_from_main_page(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--log-level=3")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        for tag in soup(['script', 'style', 'meta', 'noscript']):
            tag.extract()

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
        return f"❌ Error loading {url}: {e}"

    finally:
        driver.quit()

# --- Streamlit Interface ---
st.set_page_config(page_title="Email Scraper", layout="centered")
st.title("📬 Website Email Scraper (No Google Sheets)")

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

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # --- CSV Download ---
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv,
        file_name="emails.csv",
        mime='text/csv'
    )
