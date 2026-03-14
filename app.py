import streamlit as st
import requests
import google.generativeai as genai

# --- 1. CONFIGURATION ---
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
GEMINI_KEY = st.secrets["GEMINI_KEY"]

# Setup Gemini with the specific model requested
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview') 

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
st.title("🛒 Amazon Elite Product Finder")
st.markdown("Strict Criteria: **4.5+ Stars** and **1,000+ Reviews**.")

product_name = st.text_input("Product Name:", placeholder="e.g. Ergonomic Office Chair")

# Optional Price Filters
st.markdown("### Price Range (Optional)")
p_col1, p_col2 = st.columns(2)
with p_col1:
    min_p = st.number_input("Min Price ($)", min_value=0.0, step=1.0, value=0.0)
with p_col2:
    max_p = st.number_input("Max Price ($)", min_value=0.0, step=1.0, value=0.0)

if st.button("Search & Analyze"):
    if not product_name:
        st.warning("Please enter a product name.")
    else:
        with st.spinner("Scanning Amazon..."):
            results, error = search_amazon(product_name)
            
            if error:
                st.error(f"Search Error: {error}")
            elif results:
                # --- FILTERING LOGIC ---
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
                    
                    # Apply criteria + optional price
                    price_pass = True
                    if min_p > 0 and price_val < min_p: price_pass = False
                    if max_p > 0 and price_val > max_p: price_pass = False
                        
                    if rating >= 4.5 and reviews >= 1000 and price_pass:
                        matches.append(item)

                if matches:
                    st.success(f"Successfully found {len(matches)} elite products!")
                    
                    # --- 3. TOP 3 COMPARISON (SIDE-BY-SIDE) ---
                    st.markdown("### 🏆 Top 3 Comparisons")
                    top_matches = matches[:3]
                    cols = st.columns(len(top_matches))
                    
                    for idx, item in enumerate(top_matches):
                        with cols[idx]:
                            st.markdown(f"**Match #{idx+1}**")
                            if item.get("thumbnail"):
                                st.image(item["thumbnail"], width=150)
                            st.write(f"**{item.get('title', 'Product')[:60]}...**")
                            st.write(f"⭐ {item.get('rating')} | 💬 {item.get('reviews')}")
                            st.link_button(f"Listing #{idx+1}", item.get('link', '#'))

                    # --- 4. THE FULL LISTING CATALOG ---
                    st.markdown("---")
                    st.markdown(f"### 📋 Full Catalog ({len(matches)} items)")
                    st.write("Browse all listings that met your quality requirements:")
                    
                    # Displaying all links in a list for the user
                    for i, item in enumerate(matches):
                        with st.expander(f"Item {i+1}: {item.get('title', 'Product')[:80]}..."):
                            st.write(f"**Rating:** {item.get('rating')} Stars")
                            st.write(f"**Reviews:** {item.get('reviews')}")
                            st.link_button("Go to Amazon Listing", item.get('link', '#'))

                    # --- 5. AI ANALYST (USING GEMINI-3-FLASH-PREVIEW) ---
                    st.markdown("---")
                    with st.spinner("AI Analyst generating verdict..."):
                        try:
                            best = matches[0]
                            prompt = f"Analyze why a {product_name} with {best['rating']} stars and {best['reviews']} reviews is considered elite quality. Limit to two sentences."
                            
                            response = model.generate_content(prompt)
                            if response.text:
                                st.info(f"**AI Analyst Verdict (Gemini 3):**\n\n{response.text}")
                        except Exception as e:
                            st.error(f"AI Service Note: {str(e)}")
                            st.info("The links above are verified. The AI model ID might be restricted in your region.")
                else:
                    st.error("No items found meeting the 4.5+ star and 1,000+ review criteria.")
            else:
                st.info("Amazon returned no results. Try a more general search term.")
