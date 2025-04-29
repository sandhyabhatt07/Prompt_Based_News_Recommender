"""
app.py - Streamlit Web Application for AI-Powered News Recommendations
"""

import os
import json
import streamlit as st
import google.generativeai as genai
import pandas as pd
import feedparser
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import re
import time

# Load API Key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# App title and configuration
st.set_page_config(
    page_title="AI News Recommender",
    page_icon="📰",
    layout="wide"
)

# Categorized RSS Feed URLs
RSS_FEEDS = {
    "World": [
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.theguardian.com/world/rss",
        "https://www.aljazeera.com/xml/rss/all.xml"
    ],
    "Technology": [
        "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "https://www.theverge.com/rss/index.xml",
        "https://www.wired.com/feed/rss"
    ],
    "Sports": [
        "https://www.espn.com/espn/rss/news",
        "https://www.skysports.com/rss/12040",
        "https://www.bbc.co.uk/sport/rss.xml"
    ],
    "Entertainment": [
        "https://www.billboard.com/feed/",
        "https://www.etonline.com/rss",
        "https://www.rollingstone.com/feed/"
    ],
    "Lifestyle": [
        "https://www.refinery29.com/en-us/feed.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/FashionandStyle.xml"
    ],
    "Health": [
        "https://www.medicalnewstoday.com/rss",
        "https://www.nhs.uk/news/feed.rss"
    ],
    "Politics": [
        "https://www.politico.com/rss/politics.xml",
        "https://www.theguardian.com/politics/rss"
    ]
}

# Fetch news articles from RSS feeds based on category
@st.cache_data(ttl=3600)  # Cache for one hour
def fetch_news(category):
    """Fetch and process news from a specific category"""
    articles = []
    
    with st.spinner(f"Fetching {category} news..."):
        for feed_url in RSS_FEEDS.get(category, []):
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:10]:  # Limit to 10 per source
                    # Clean the HTML content
                    content = entry.get('summary', '')
                    clean_content = BeautifulSoup(content, "html.parser").get_text(separator=' ', strip=True)
                    
                    # Add article to our dataset
                    articles.append({
                        "title": entry.get('title', '').strip(),
                        "content": clean_content,
                        "link": entry.get('link', ''),
                        "source": feed.feed.get('title', 'Unknown Source')
                    })
            except Exception as e:
                st.error(f"Error fetching {feed_url}: {str(e)}")
                
    # Convert to DataFrame
    df = pd.DataFrame(articles)
    
    # Drop duplicates by title
    if not df.empty:
        df = df.drop_duplicates(subset=['title'])
        
    return df

def clean_gemini_response(response_text):
    """Removes markdown formatting and extracts pure JSON."""
    # Remove code block markers
    cleaned = re.sub(r'```json\s*|```\s*', '', response_text.strip())
    return cleaned.strip()

# Generate recommendations using Gemini with improved prompt engineering
def get_gemini_recommendations(article_title, article_content, news_df):
    """Generate article recommendations using Gemini AI"""
    # Use the faster model for better user experience
    model = genai.GenerativeModel("gemini-1.5-flash")  

    # Sample the dataset to avoid token limits
    sample_size = min(30, len(news_df))
    news_sample = news_df.sample(n=sample_size) if len(news_df) > sample_size else news_df
    
    # Create a structured dataset representation
    news_items = []
    for idx, row in news_sample.iterrows():
        news_items.append(f"ID: {idx}\nTITLE: {row['title']}\nLINK: {row['link']}\nSOURCE: {row.get('source', 'Unknown')}")
    
    news_list = "\n\n".join(news_items)

    prompt = f"""
    # SYSTEM: You are an expert news recommendation system that identifies relevant articles based on semantic similarity.

    # TASK: Find 5 news articles most similar to the reference article below.

    # REFERENCE ARTICLE:
    TITLE: {article_title}
    CONTENT: {article_content}

    # AVAILABLE ARTICLES:
    {news_list}

    # CRITERIA FOR SIMILARITY:
    - Topic relevance (most important)
    - Similar events or entities mentioned
    - Similar perspectives or angles
    - Content diversity (include different sources when possible)

    # OUTPUT FORMAT:
    Return a JSON array containing exactly 5 article recommendations.
    Each recommendation must have only these fields:
    - "title": The exact title of the article as shown in AVAILABLE ARTICLES
    - "link": The exact link of the article as shown in AVAILABLE ARTICLES

    # OUTPUT CONSTRAINTS:
    - Return ONLY raw JSON with no markdown formatting, explanation, or commentary
    - The output must be a parseable JSON array of 5 objects
    - Do not include the reference article in recommendations
    - Ensure all links are complete URLs

    # EXAMPLE OUTPUT:
    [
      {{"title": "Example Article 1", "link": "https://example.com/1"}},
      {{"title": "Example Article 2", "link": "https://example.com/2"}},
      {{"title": "Example Article 3", "link": "https://example.com/3"}},
      {{"title": "Example Article 4", "link": "https://example.com/4"}},
      {{"title": "Example Article 5", "link": "https://example.com/5"}}
    ]
    """

    try:
        # Generate recommendations
        response = model.generate_content(prompt)
        
        # Clean and parse response
        cleaned_response = clean_gemini_response(response.text)
        
        # Try to parse JSON
        recommendations = json.loads(cleaned_response)
        
        # Validate recommendations structure
        if not isinstance(recommendations, list):
            st.error("AI returned invalid response format.")
            return []
            
        # Filter valid recommendations
        valid_recommendations = [
            {"title": rec["title"], "link": rec["link"]}
            for rec in recommendations
            if isinstance(rec, dict) and rec.get("title") and rec.get("link", "").startswith("http") 
            and rec["title"] != article_title  # Avoid recommending same article
        ]
        
        return valid_recommendations

    except json.JSONDecodeError as e:
        st.error(f"Error parsing AI response: {e}")
        # Try fallback extraction
        try:
            # Look for JSON-like patterns
            pattern = r'\[\s*\{.*?\}\s*\]'
            match = re.search(pattern, cleaned_response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except:
            pass
        return []
    except Exception as e:
        st.error(f"Error generating recommendations: {e}")
        return []

# Main Streamlit UI
def main():
    st.title("📰 AI-Powered News Recommender")
    st.write("Discover similar news articles with the help of AI")
    
    # Step 1: Select category
    category = st.selectbox("Choose a News Category", list(RSS_FEEDS.keys()))
    
    # Fetch news based on selected category
    with st.spinner("Loading news..."):
        news_df = fetch_news(category)
    
    if news_df.empty:
        st.warning(f"No articles found for {category}. Try another category.")
    else:
        st.success(f"Found {len(news_df)} articles in the {category} category")
        
        # Step 2: Select an article
        article_titles = news_df["title"].tolist()
        selected_article = st.selectbox("Select a News Article", article_titles)
        
        # Get selected article details
        article_row = news_df[news_df["title"] == selected_article].iloc[0]
        
        # Display article details
        with st.expander("Selected Article Details", expanded=True):
            st.markdown(f"### {article_row['title']}")
            st.markdown(f"**Source:** {article_row.get('source', 'Unknown')}")
            st.markdown(f"**Content Preview:**")
            st.write(article_row['content'][:500] + "..." if len(article_row['content']) > 500 else article_row['content'])
            st.markdown(f"[Read Full Article]({article_row['link']})")
        
        # Step 3: Fetch recommendations
        if st.button("Get Similar Articles", type="primary"):
            with st.spinner("AI is finding similar articles..."):
                # Add slight delay for better UX
                start_time = time.time()
                
                # Get recommendations
                recommendations = get_gemini_recommendations(
                    article_row["title"], 
                    article_row["content"], 
                    news_df
                )
                
                # Ensure minimum perception of AI "thinking"
                elapsed = time.time() - start_time
                if elapsed < 1.5:
                    time.sleep(1.5 - elapsed)
            
            # Display recommendations
            if recommendations:
                st.subheader("🔍 Recommended Articles")
                
                # Create columns for recommendations
                cols = st.columns(min(len(recommendations), 3))
                
                for i, rec in enumerate(recommendations):
                    col_idx = i % len(cols)
                    with cols[col_idx]:
                        st.markdown(f"**{i+1}. {rec['title']}**")
                        st.markdown(f"[Read Article]({rec['link']})")
                        st.markdown("---")
            else:
                st.warning("Could not find similar articles. Try selecting a different article.")

if __name__ == "__main__":
    main()
