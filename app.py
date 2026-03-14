import streamlit as st
import requests
import google.generativeai as genai

# --- 1. CONFIGURATION ---
# Ensure these keys are exactly named in your Streamlit Cloud Secrets
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
GEMINI_KEY = st.secrets["GEMINI_KEY"]

# Setup Gemini with the current Gemini 3 Model ID
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
st.set_page_config(page_title="Amazon Quality Finder", layout="wide")
st.title("🛒 Amazon Quality Finder")
st.markdown("---")

product_name = st.text_input("What product are you looking for?", placeholder="e.g. noise cancelling headphones")

if st.button("Search & Analyze"):
    if not product_name:
        st.warning("Please enter a product name.")
    else:
        with st.spinner("Searching Amazon..."):
            results, error = search_amazon(product_name)
            
            if error:
                st.error(f"Search Error: {error}")
            elif results:
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
                    with st.spinner("AI Analyst generating opinion..."):
                        try:
                            # Refined prompt for better AI grounding
                            prompt = (f"Act as a professional shopping consultant. Analyze this {product_name} "
                                     f"listing which has {best_item['rating']} stars and {best_item['reviews']} reviews. "
                                     f"Explain in 3 bullet points why this is a high-value purchase.")
                            
                            opinion = model.generate_content(prompt)
                            
                            if opinion and opinion.text:
                                st.info(f"**AI Analyst Opinion:**\n\n{opinion.text}")
                            else:
                                st.warning("AI generated an empty response. Please try again.")
                                
                        except Exception as e:
                            st.error(f"AI Opinion Error: {str(e)}")
                            st.info("The product data is verified above, but the AI consultant is currently busy.")
                else:
                    st.error("No items found with 4.5+ stars and 1,000+ reviews.")
            else:
                st.info("No results returned from Amazon. Try a different search term.")
