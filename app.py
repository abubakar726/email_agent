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

        emails = set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,4}", visible_text))

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

# --- Streamlit UI Config ---
st.set_page_config(page_title="Email Scraper", layout="centered")
st.markdown("""
    <style>
        .fixed-top {
            position: fixed;
            top: 0;
            width: 100%;
            z-index: 999;
            background-color: #ffffff;
            padding: 10px 20px;
            border-bottom: 1px solid #e6e6e6;
        }
        .spacer {
            margin-top: 75px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="fixed-top">', unsafe_allow_html=True)
st.title("📬 Website Email Scraper")
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

# --- Session State ---
if 'results' not in st.session_state:
    st.session_state.results = []
if 'scraped' not in st.session_state:
    st.session_state.scraped = False

# --- Upload or Manual Input ---
st.markdown("## Upload CSV or Paste URLs")
uploaded_file = st.file_uploader("📁 Upload CSV file with 'URL' column", type=["csv"])
manual_urls = st.text_area("Or paste website URLs (one per line)", height=140)

urls = []
if uploaded_file:
    try:
        df_file = pd.read_csv(uploaded_file)
        if 'URL' in df_file.columns:
            urls = df_file['URL'].dropna().tolist()
        else:
            st.warning("⚠️ Uploaded CSV must contain a 'URL' column")
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
elif manual_urls.strip():
    urls = [u.strip() for u in manual_urls.strip().splitlines() if u.strip()]

# --- Buttons ---
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🔍 Scrape Emails") and urls:
        st.session_state.results.clear()
        progress_bar = st.progress(0)

        for i, url in enumerate(urls):
            if not url.startswith('http'):
                url = 'https://' + url
            with st.spinner(f"Scraping: {url}"):
                email_result = extract_emails_from_main_page(url)
                st.success(f"{url} → {email_result}")
                st.session_state.results.append({"Website": url, "Email": email_result})
                progress_bar.progress((i + 1) / len(urls))

        st.session_state.scraped = True
        progress_bar.empty()

with col2:
    if st.button("🔄 Reset"):
        st.session_state.results.clear()
        st.session_state.scraped = False
        st.experimental_set_query_params()

# --- Results and Download ---
if st.session_state.results:
    df = pd.DataFrame(st.session_state.results)

    # Download CSV top fixed
    st.markdown('<div class="fixed-top download-button">', unsafe_allow_html=True)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv,
        file_name="emails.csv",
        mime="text/csv",
        key="download-top"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### 📋 Scraped Email Results")
    st.dataframe(df, use_container_width=True)
