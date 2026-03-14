import streamlit as st
import requests
import google.generativeai as genai

# --- 1. CONFIGURATION ---
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
GEMINI_KEY = st.secrets["GEMINI_KEY"]

genai.configure(api_key=GEMINI_KEY)
# Using Gemini 3 Flash Preview as requested
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
                    st.success(f"Successfully found {len(matches)} elite products!")
                    
                    # --- 3. BULK LINK GENERATION ---
                    # We create a link using the ASINs (p_78 filter)
                    asins = [item.get("asin") for item in matches if item.get("asin")]
                    asin_query = "|".join(asins)
                    bulk_link = f"https://www.amazon.com/s?k={product_name.replace(' ', '+')}&rh=p_78%3A{asin_query}"
                    
                    st.markdown("### 🔗 Your Curated Amazon Page")
                    st.info("The button below takes you to an Amazon page showing ONLY the high-rated items we found.")
                    st.link_button("🔥 Open All Elite Results on Amazon", bulk_link, type="primary")

                    # --- 4. TOP 3 COMPARISON ---
                    st.markdown("---")
                    st.markdown("### 🏆 Top 3 Highlights")
                    top_matches = matches[:3]
                    cols = st.columns(len(top_matches))
                    
                    for idx, item in enumerate(top_matches):
                        with cols[idx]:
                            if item.get("thumbnail"):
                                st.image(item["thumbnail"], width=150)
                            st.write(f"**{item.get('title', 'Product')[:60]}...**")
                            st.write(f"⭐ {item.get('rating')} | 💬 {item.get('reviews')}")

                    # --- 5. AI ANALYST ---
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
                else:
                    st.error("No items found meeting the 4.5+ star and 1,000+ review criteria.")
            else:
                st.info("Amazon returned no results. Try a more general search term.")
