import streamlit as st
import requests
import google.generativeai as genai

# --- 1. CONFIGURATION ---
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
GEMINI_KEY = st.secrets["GEMINI_KEY"]

# Setup Gemini - Using the 2026 stable alias
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.0-flash') 

def search_amazon(query):
    params = {
        "engine": "amazon",
        "k": query,
        "amazon_domain": "amazon.com",
        "api_key": SERPAPI_KEY
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params)
        data = response.json()
        if "error" in data:
            return None, data['error']
        return data.get("organic_results", []), None
    except Exception as e:
        return None, str(e)

# --- 2. UI LAYOUT ---
st.set_page_config(page_title="Amazon Elite Finder", layout="wide")
st.title("🛒 Amazon Quality Finder & Comparator")

product_name = st.text_input("What product are you looking for?", placeholder="e.g. Mechanical Keyboard")

st.markdown("### Price Filters (Optional)")
p_col1, p_col2 = st.columns(2)
with p_col1:
    min_p = st.number_input("Min Price ($)", min_value=0.0, step=1.0, value=0.0)
with p_col2:
    max_p = st.number_input("Max Price ($)", min_value=0.0, step=1.0, value=0.0)

if st.button("Search & Compare Top Products"):
    if not product_name:
        st.warning("Please enter a product name.")
    else:
        with st.spinner("Analyzing Amazon Listings..."):
            results, error = search_amazon(product_name)
            
            if error:
                st.error(f"Search Error: {error}")
            elif results:
                matches = []
                for item in results:
                    rating = item.get("rating", 0)
                    reviews = item.get("reviews", 0)
                    
                    # Safe Price Extraction
                    price_data = item.get("price")
                    price_val = 0
                    if isinstance(price_data, dict):
                        price_val = price_data.get("value", 0)
                    elif isinstance(price_data, (int, float)):
                        price_val = price_data
                    elif isinstance(price_data, str):
                        try:
                            price_val = float(price_data.replace('$', '').replace(',', ''))
                        except: price_val = 0
                    
                    price_pass = True
                    if min_p > 0 and price_val < min_p: price_pass = False
                    if max_p > 0 and price_val > max_p: price_pass = False
                        
                    if rating >= 4.5 and reviews >= 1000 and price_pass:
                        matches.append(item)

                if matches:
                    st.success(f"Found {len(matches)} elite products!")
                    top_matches = matches[:3]
                    
                    # --- 3. COMPANION MODE ---
                    cols = st.columns(len(top_matches))
                    for idx, item in enumerate(top_matches):
                        with cols[idx]:
                            st.markdown(f"#### Match #{idx+1}")
                            if item.get("thumbnail"):
                                st.image(item["thumbnail"], use_container_width=True)
                            st.write(f"**{item.get('title', 'Product')[:60]}...**")
                            st.write(f"⭐ {item.get('rating')} | 💬 {item.get('reviews')} reviews")
                            
                            price_info = item.get("price")
                            display_price = price_info.get("raw", "N/A") if isinstance(price_info, dict) else str(price_info)
                            st.write(f"💰 **{display_price}**")
                            st.link_button(f"Buy Product {idx+1}", item.get('link', '#'))

                    # --- 4. AI ANALYST (FIXED) ---
                    st.markdown("---")
                    with st.spinner("AI Analyst generating verdict..."):
                        try:
                            best = top_matches[0]
                            # Simplified prompt for better reliability
                            prompt = f"Explain in 2 sentences why a {product_name} with {best['rating']} stars and {best['reviews']} reviews is a reliable choice."
                            
                            response = model.generate_content(prompt)
                            
                            # Check for text attribute safely
                            if hasattr(response, 'text') and response.text:
                                st.info(f"**AI Expert Verdict:**\n\n{response.text}")
                            else:
                                st.warning("AI opinion is being processed. Please refresh in a moment.")
                        except Exception as e:
                            st.error(f"AI Connectivity Note: {str(e)}")
                            st.info("The top products are verified above, but the AI service is currently throttled.")
                else:
                    st.error("No items found meeting all criteria (4.5+ stars, 1,000+ reviews).")
            else:
                st.info("No results returned. Try a different search term.")
