import streamlit as st
import requests
import google.generativeai as genai

# --- 1. CONFIGURATION ---
# Access keys from Streamlit Cloud Secrets
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
GEMINI_KEY = st.secrets["GEMINI_KEY"]

# Setup Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def search_amazon(query):
    # FIXED: Amazon engine requires 'k' for the keyword, not 'q'
    params = {
        "engine": "amazon",
        "k": query, # Correct parameter for Amazon engine
        "amazon_domain": "amazon.com",
        "api_key": SERPAPI_KEY
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params)
        data = response.json()
        
        if "error" in data:
            st.error(f"SerpApi Error: {data['error']}")
            return []
            
        return data.get("organic_results", [])
    except Exception as e:
        st.error(f"Network Error: {e}")
        return []

# --- 2. UI LAYOUT ---
st.set_page_config(page_title="Amazon High-Rating Finder", layout="wide")
st.title("🛒 Amazon Quality Finder")
st.markdown("---")

# Sidebar for Debugging
with st.sidebar:
    show_raw = st.checkbox("Show Raw Search Data (Debug)")

product_name = st.text_input("What product are you looking for?", placeholder="e.g. noise cancelling headphones")

if st.button("Search & Analyze"):
    if not product_name:
        st.warning("Please enter a product name.")
    else:
        with st.spinner("Talking to Amazon..."):
            results = search_amazon(product_name)
            
            if show_raw:
                st.write("### Raw Data from API", results)

            # Filtering: Rating > 4.5 and Reviews >= 1000
            matches = [
                item for item in results 
                if item.get("rating", 0) > 4.5 and item.get("reviews", 0) >= 1000
            ]

            if matches:
                best_item = matches[0]
                st.success(f"Top Match Found!")
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    if best_item.get("thumbnail"):
                        st.image(best_item["thumbnail"])
                with col2:
                    st.subheader(best_item.get("title"))
                    st.write(f"⭐ **Rating:** {best_item.get('rating')}")
                    st.write(f"💬 **Reviews:** {best_item.get('reviews')}")
                    st.link_button("View Listing on Amazon", best_item.get('link', '#'))
                
                # --- 3. AI AGENT ---
                st.markdown("---")
                try:
                    prompt = f"As a shopping expert, explain why this {product_name} is a smart buy based on {best_item['rating']} stars and {best_item['reviews']} reviews."
                    opinion = model.generate_content(prompt)
                    st.info(f"**AI Analyst Opinion:**\n\n{opinion.text}")
                except Exception as e:
                    st.warning("AI opinion unavailable, but data is shown above.")
            else:
                st.error("No items found with 4.5+ stars and 1,000+ reviews.")
                if results:
                    st.info(f"Found {len(results)} items, but none met your high-quality filters.")
