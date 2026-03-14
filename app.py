import streamlit as st
import requests
import google.generativeai as genai

# --- 1. CONFIGURATION ---
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
GEMINI_KEY = st.secrets["GEMINI_KEY"]

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def search_amazon(query):
    # SerpApi's Amazon engine can be sensitive to parameters.
    # We use 'q' for the search term and 'amazon_domain' to be specific.
    params = {
        "engine": "amazon",
        "q": query,
        "amazon_domain": "amazon.com",
        "api_key": SERPAPI_KEY
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params)
        data = response.json()
        
        # DEBUG: Check if SerpApi returned an error (like 'out of credits')
        if "error" in data:
            st.error(f"SerpApi Error: {data['error']}")
            return []
            
        return data.get("organic_results", [])
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return []

# --- 2. UI LAYOUT ---
st.title("🛒 High-Rating Amazon Finder")
st.markdown("---")

product_name = st.text_input("Enter product name (e.g., 'wireless earbuds'):")

if st.button("Find Best Listing"):
    if not product_name:
        st.warning("Please enter a product name.")
    else:
        with st.spinner("Searching Amazon..."):
            results = search_amazon(product_name)
            
            # DEBUG: Show total results found before filtering
            st.write(f"Total Amazon results analyzed: {len(results)}")
            
            # Filtering logic: Rating > 4.5 and Reviews >= 1000
            matches = [
                item for item in results 
                if item.get("rating", 0) > 4.5 and item.get("reviews", 0) >= 1000
            ]

            if matches:
                best_item = matches[0]
                st.success(f"Found a Match: {best_item.get('title')}")
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    if best_item.get("thumbnail"):
                        st.image(best_item["thumbnail"])
                with col2:
                    st.write(f"⭐ **Rating:** {best_item.get('rating')}")
                    st.write(f"💬 **Reviews:** {best_item.get('reviews')}")
                    st.link_button("View on Amazon", best_item.get('link', '#'))
                
                # AI Analysis
                try:
                    prompt = f"Explain why this {product_name} is a high-quality choice."
                    opinion = model.generate_content(prompt)
                    st.info(f"**AI Analyst:** {opinion.text}")
                except Exception as ai_err:
                    st.warning("AI opinion unavailable, but product data is shown above.")
            else:
                st.error("No items matched the 4.5+ star and 1,000+ review criteria.")
                if len(results) > 0:
                    st.info("Found results, but none were high enough quality. Try a more popular product name.")
