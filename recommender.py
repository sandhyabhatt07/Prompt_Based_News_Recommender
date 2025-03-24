import os
import json
import google.generativeai as genai
import pandas as pd
import feedparser
from dotenv import load_dotenv
import re

# Load API Key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to fetch RSS feed articles
def fetch_rss_articles(feed_url):
    feed = feedparser.parse(feed_url)
    articles = [
        {"title": entry.title, "content": entry.summary, "link": entry.link}
        for entry in feed.entries
    ]
    return pd.DataFrame(articles)

# RSS Feed URLs
RSS_FEEDS = [
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml"
]

# Fetch news articles from all RSS feeds
news_df = pd.concat([fetch_rss_articles(url) for url in RSS_FEEDS], ignore_index=True)

if news_df.empty:
    print("❌ No news articles fetched from RSS feeds.")
else:
    print(f"✅ Fetched {len(news_df)} articles from RSS feeds.")

def clean_gemini_response(response_text):
    """Removes markdown formatting (```json ... ```) and extracts pure JSON."""
    response_text = response_text.strip()
    response_text = re.sub(r"```json\n|\n```", "", response_text)  # Fixing markdown formatting
    return response_text


def get_gemini_recommendations(article_title, article_content, news_df):
    """Uses Gemini to recommend similar articles."""
    model = genai.GenerativeModel("gemini-1.5-pro-latest")

    # Convert dataset into a formatted string
    news_list = "\n".join([f"{row['title']} ( {row['link']} )" for _, row in news_df.iterrows()])

    prompt = f"""
    You are a news recommendation AI. Based on the following article:
    TITLE: {article_title}
    CONTENT: {article_content}

    Find 5 highly relevant news articles from the dataset below:
    {news_list}

    Return a **valid JSON array**, with each object having:
    - "title" (string): The article title
    - "link" (string): The actual URL of the article.

    Strictly return only a valid JSON response with no explanations, text, or comments.
    """

    print("🔹 Sending Prompt to Gemini...")  # Debugging Step

    response = model.generate_content(prompt)

    if not response.text.strip():  # Handle empty responses
        print("❌ Gemini returned an empty response.")
        return []

    cleaned_response = clean_gemini_response(response.text)

    print("🔹 Gemini Cleaned Response:\n", cleaned_response)  # Debugging Step

    try:
        recommendations = json.loads(cleaned_response)  # Parse JSON safely
        if isinstance(recommendations, list):
            return recommendations
        else:
            print("❌ Gemini returned non-list JSON. Fixing format...")
            return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing Gemini response: {e}")
        return []  # Return empty list if JSON parsing fails

# Example usage
if not news_df.empty:
    first_article = news_df.iloc[0]
    recommendations = get_gemini_recommendations(first_article["title"], first_article["content"], news_df)

    if recommendations:
        print("\n🔹 Recommended Articles:")
        for rec in recommendations:
            print(f"- {rec['title']} (Link: {rec['link']})")
    else:
        print("❌ No recommendations found.")