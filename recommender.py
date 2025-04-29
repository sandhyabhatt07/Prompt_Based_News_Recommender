"""
recommender.py - Improved News Recommendation Module with Video Recommendations using Google's Gemini API
"""

import os
import json
import google.generativeai as genai
import pandas as pd
import feedparser
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import re
import requests
from urllib.parse import urlencode

# Load API Key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # Add YouTube API key to your .env file

# Function to fetch and clean RSS feed articles
def fetch_rss_articles(feed_url):
    """Fetch articles from RSS feed with proper HTML cleaning"""
    try:
        feed = feedparser.parse(feed_url)
        articles = []
        
        for entry in feed.entries:
            # Clean HTML content
            content = entry.get('summary', '')
            clean_content = BeautifulSoup(content, "html.parser").get_text(separator=' ', strip=True)
            
            articles.append({
                "title": entry.title,
                "content": clean_content,
                "link": entry.link,
                "source": feed.feed.get('title', 'Unknown Source')
            })
                
        return articles
    except Exception as e:
        print(f"Error fetching {feed_url}: {e}")
        return []

# Function to fetch related videos from YouTube
def fetch_youtube_videos(query, max_results=5):
    """Fetch related videos from YouTube API"""
    if not YOUTUBE_API_KEY:
        print("YouTube API Key not found in environment variables")
        return []
        
    try:
        base_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': max_results,
            'key': YOUTUBE_API_KEY,
            'relevanceLanguage': 'en'
        }
        
        response = requests.get(f"{base_url}?{urlencode(params)}")
        if response.status_code != 200:
            print(f"YouTube API error: {response.status_code}")
            print(response.text)
            return []
            
        results = response.json()
        videos = []
        
        for item in results.get('items', []):
            video_id = item['id']['videoId']
            videos.append({
                "title": item['snippet']['title'],
                "description": item['snippet']['description'],
                "thumbnail": item['snippet']['thumbnails']['medium']['url'],
                "video_id": video_id,
                "link": f"https://www.youtube.com/watch?v={video_id}"
            })
            
        return videos
    except Exception as e:
        print(f"Error fetching videos: {e}")
        return []

# Function to get video recommendations based on keywords without API (fallback method)
def get_alternative_video_recommendations(article_title, article_content):
    """Generate relevant search queries and structure as video recommendations"""
    # Use Gemini to extract key search terms
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    Extract 3-5 most important search keywords or phrases from this news article that would be good for finding related videos.
    
    ARTICLE TITLE: {article_title}
    ARTICLE CONTENT: {article_content[:500]}
    
    Return only a JSON array of strings with no additional text or explanation.
    Example output: ["keyword1", "keyword2", "keyword phrase 3"]
    """
    
    try:
        response = model.generate_content(prompt)
        cleaned_response = clean_gemini_response(response.text)
        keywords = json.loads(cleaned_response)
        
        if not isinstance(keywords, list) or len(keywords) == 0:
            keywords = [article_title]
        
        # If we have YouTube API key, use it
        if YOUTUBE_API_KEY:
            # Use the first keyword which should be the most relevant
            return fetch_youtube_videos(keywords[0])
        else:
            # Create structured placeholder data that directs to YouTube search
            video_recommendations = []
            for keyword in keywords[:5]:
                search_query = urlencode({'search_query': keyword})
                video_recommendations.append({
                    "title": f"Videos about: {keyword}",
                    "description": f"Search results for {keyword}",
                    "thumbnail": "https://www.youtube.com/img/desktop/yt_1200.png",  # YouTube logo as placeholder
                    "link": f"https://www.youtube.com/results?{search_query}"
                })
            return video_recommendations
            
    except Exception as e:
        print(f"Error generating video recommendations: {e}")
        # Fallback to basic article title search
        search_query = urlencode({'search_query': article_title})
        return [{
            "title": f"Videos about: {article_title}",
            "description": "Related videos on YouTube",
            "thumbnail": "https://www.youtube.com/img/desktop/yt_1200.png",
            "link": f"https://www.youtube.com/results?{search_query}"
        }]

# RSS Feed URLs
RSS_FEEDS = [
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml"
]

def fetch_all_news():
    """Fetch all news from defined RSS feeds"""
    all_articles = []
    
    for feed_url in RSS_FEEDS:
        all_articles.extend(fetch_rss_articles(feed_url))
    
    # Convert to DataFrame and drop duplicates if needed
    df = pd.DataFrame(all_articles)
    if not df.empty:
        df = df.drop_duplicates(subset=['title'])
    
    return df

def clean_gemini_response(response_text):
    """Removes markdown formatting and extracts pure JSON."""
    response_text = response_text.strip()
    # Remove code block markers if present
    response_text = re.sub(r"```json\n|\n```|```", "", response_text)
    return response_text

def get_gemini_recommendations(article_title, article_content, news_df):
    """Uses Gemini to recommend similar articles with improved prompt engineering."""
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    
    # Sample a manageable subset of news to avoid token limits
    sample_size = min(25, len(news_df))
    news_sample = news_df.sample(n=sample_size) if len(news_df) > sample_size else news_df
    
    # Create a more structured dataset representation
    news_items = []
    for idx, row in news_sample.iterrows():
        news_items.append(f"ID: {idx}\nTITLE: {row['title']}\nLINK: {row['link']}")
    
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
    - Complementary information that would interest the same reader

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

    print("🔹 Sending Prompt to Gemini...")
    response = model.generate_content(prompt)
    
    if not response.text.strip():
        print("❌ Gemini returned an empty response.")
        return []
    
    cleaned_response = clean_gemini_response(response.text)
    print("🔹 Gemini Cleaned Response:\n", cleaned_response)
    
    try:
        recommendations = json.loads(cleaned_response)
        
        if isinstance(recommendations, list):
            # Filter out any recommendations that don't match the expected format
            valid_recommendations = [
                rec for rec in recommendations 
                if isinstance(rec, dict) and rec.get("title") and rec.get("link", "").startswith("http")
                and rec["title"] != article_title  # Avoid recommending the same article
            ]
            return valid_recommendations[:5]  # Return at most 5 recommendations
        else:
            print("❌ Gemini returned non-list JSON.")
            return []
            
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing Gemini response: {e}")
        # Try to extract any JSON-like structures as fallback
        pattern = r'\[\s*\{.*?\}\s*\]'
        match = re.search(pattern, cleaned_response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
        return []

# Example usage
if __name__ == "__main__":
    # Fetch the news
    news_df = fetch_all_news()
    
    if news_df.empty:
        print("❌ No news articles fetched from RSS feeds.")
    else:
        print(f"✅ Fetched {len(news_df)} articles from RSS feeds.")
        
        # Example of getting recommendations
        if len(news_df) > 0:
            first_article = news_df.iloc[0]
            print(f"\n🔍 Finding recommendations for: {first_article['title']}")
            
            # Get article recommendations
            article_recommendations = get_gemini_recommendations(
                first_article["title"], 
                first_article["content"], 
                news_df
            )
            
            if article_recommendations:
                print("\n🔹 Recommended Articles:")
                for i, rec in enumerate(article_recommendations, 1):
                    print(f"{i}. {rec['title']}")
                    print(f"   Link: {rec['link']}")
                    print()
            else:
                print("❌ No article recommendations found.")
                
            # Get video recommendations
            print(f"\n🎬 Finding related videos for: {first_article['title']}")
            video_recommendations = get_alternative_video_recommendations(
                first_article["title"],
                first_article["content"]
            )
            
            if video_recommendations:
                print("\n🔹 Related Videos:")
                for i, video in enumerate(video_recommendations, 1):
                    print(f"{i}. {video['title']}")
                    print(f"   Link: {video['link']}")
                    print()
            else:
                print("❌ No video recommendations found.")
