import os
import json
import streamlit as st
import google.generativeai as genai
import pandas as pd
import feedparser
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import re

# Load API Key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

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
def fetch_news(category):
    articles = []
    for feed_url in RSS_FEEDS.get(category, []):
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:10]:  # Limit to 10 per source
            clean_content = BeautifulSoup(entry.summary, "html.parser").get_text()
            articles.append({"title": entry.title, "content": clean_content, "link": entry.link})
    return pd.DataFrame(articles)

# Generate recommendations using Gemini with Few-Shot Learning
def get_gemini_recommendations(article_title, article_content, news_df):
    model = genai.GenerativeModel("gemini-1.5-flash")  # Faster, lower cost  

    # Reduce dataset size for better responses
    sample_news = news_df.sample(n=min(10, len(news_df)))
    news_list = "\n".join([f"{{'title': '{row['title']}', 'link': '{row['link']}'}}" for _, row in sample_news.iterrows()])

    prompt = f"""
    You are an AI assistant that provides news article recommendations based on content similarity. Given the following news article:
    
    TITLE: {article_title}
    CONTENT: {article_content}
    
    Find 5 most relevant news articles from the dataset below:
    [{news_list}]
    
    Respond **ONLY** in valid JSON format like this:
    ```json
    [
      {{"title": "Article Title 1", "link": "https://example.com/article1"}},
      {{"title": "Article Title 2", "link": "https://example.com/article2"}}
    ]
    ```
    
    Ensure all links are valid and start with 'http'. Do NOT return empty links. Avoid repeating the input article.
    """

    response = model.generate_content(prompt)
    
    # Debugging: Print raw response
    print("🔹 RAW RESPONSE:", response.text)
    
    try:
        json_text = response.text.strip()
        match = re.search(r'```json\n(.*?)\n```', json_text, re.DOTALL)
        
        if match:
            json_str = match.group(1)
        else:
            json_str = json_text  # Fallback to using raw text

        recommendations = json.loads(json_str)

        # Ensure recommendations is a list
        if not isinstance(recommendations, list):
            raise ValueError("Parsed JSON is not a list.")

        # Debugging: Print extracted recommendations
        print("🔹 Extracted Recommendations:", recommendations)

        # Filter out None values, ensure valid links, and avoid duplicate input article
        valid_recommendations = [
            {"title": rec["title"], "link": rec["link"]}
            for rec in recommendations
            if isinstance(rec, dict) and rec.get("title") and rec.get("link", "").startswith("http") and rec["title"] != article_title
        ]

        return valid_recommendations

    except (json.JSONDecodeError, ValueError, AttributeError) as e:
        st.error(f"❌ Error parsing response: {e}")
        print("❌ Parsing Error:", e)
        return []

# Streamlit UI
st.title("📰 AI-Powered News Recommender")

# Step 1: Select category
category = st.selectbox("Choose a News Category", list(RSS_FEEDS.keys()))

# Fetch news based on selected category
news_df = fetch_news(category)

if news_df.empty:
    st.warning(f"No articles found for {category}. Try another category.")
else:
    # Step 2: Select an article
    selected_article = st.selectbox("Select a News Article", news_df["title"])

    # Get selected article content
    article_row = news_df[news_df["title"] == selected_article].iloc[0]
    st.write(f"**Title:** {article_row['title']}")
    st.write(f"**Content:** {article_row['content']}")
    st.markdown(f"[Read Full Article]({article_row['link']})")

    # Step 3: Fetch recommendations
    if st.button("Get Similar Articles"):
        st.info("Fetching recommendations...")
        
        recommendations = get_gemini_recommendations(article_row["title"], article_row["content"], news_df)
        
        if recommendations:
            st.subheader("🔗 Recommended Articles")
            for rec in recommendations:
                st.markdown(f"- [{rec['title']}]({rec['link']})", unsafe_allow_html=True)
        else:
            st.warning("No valid recommendations found.")
