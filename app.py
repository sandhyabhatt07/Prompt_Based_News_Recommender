"""
app.py - Streamlit Web Application for AI-Powered News and Video Recommendations
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
import requests
from urllib.parse import urlencode

# Load API Key from .env file (for development only)
load_dotenv()
DEFAULT_GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DEFAULT_YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Initialize session state variables if they don't exist
if 'usage_count' not in st.session_state:
    st.session_state.usage_count = 0

if 'api_keys_provided' not in st.session_state:
    st.session_state.api_keys_provided = False

# App title and configuration
st.set_page_config(
    page_title="AI News & Video Recommender",
    page_icon="📰",
    layout="wide"
)

# Add custom CSS for video thumbnail display
st.markdown("""
<style>
    .video-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .video-thumbnail {
        width: 100%;
        border-radius: 5px;
    }
    .video-title {
        font-weight: bold;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .api-input {
        margin-bottom: 20px;
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 10px;
        border: 1px solid #eaeaea;
    }
</style>
""", unsafe_allow_html=True)

# Function to check if API keys are required
def check_api_requirement():
    """Check if user needs to provide API keys based on usage count"""
    # If keys already provided in this session, no need to ask again
    if st.session_state.api_keys_provided:
        return False
    
    # If usage count >= 2, require API keys
    return st.session_state.usage_count >= 2

# Function to display API key input form
def show_api_form():
    st.markdown("### 🔑 API Keys Required")
    st.markdown("""
    You've used our demo twice. To continue using this application, please provide your API keys:
    - Get a [Google Gemini API key](https://makersuite.google.com/app/apikey)
    - Get a [YouTube Data API key](https://console.cloud.google.com/apis/credentials)
    """)
    
    with st.form("api_keys_form"):
        col1, col2 = st.columns(2)
        with col1:
            google_api_key = st.text_input("Google Gemini API Key", type="password")
        with col2:
            youtube_api_key = st.text_input("YouTube API Key (optional)", type="password")
        
        submitted = st.form_submit_button("Save Keys")
        
        if submitted:
            if google_api_key:
                # Store API keys in session state
                st.session_state.google_api_key = google_api_key
                st.session_state.youtube_api_key = youtube_api_key if youtube_api_key else ""
                st.session_state.api_keys_provided = True
                st.success("API keys saved successfully!")
                return True
            else:
                st.error("Google Gemini API key is required.")
                return False
    return False

# Get API keys (either from session state, environment, or user input)
def get_api_keys():
    """Get API keys from session state or environment variables"""
    if st.session_state.api_keys_provided:
        return {
            "google": st.session_state.google_api_key,
            "youtube": st.session_state.youtube_api_key
        }
    else:
        return {
            "google": DEFAULT_GOOGLE_API_KEY,
            "youtube": DEFAULT_YOUTUBE_API_KEY
        }

# Configure API clients with keys
def configure_apis():
    """Configure API clients with the appropriate keys"""
    keys = get_api_keys()
    genai.configure(api_key=keys["google"])
    return keys["youtube"]  # Return YouTube API key for later use

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
        "https://www.health.com/feeds/rss",
        "https://www.healthline.com/health/feeds/rss",
        "https://www.everydayhealth.com/rss/",
        "https://www.medicinenet.com/rss/dailyhealth.xml"
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
    fetch_success = False
    failed_feeds_count = 0
    
    with st.spinner(f"Fetching {category} news..."):
        for feed_url in RSS_FEEDS.get(category, []):
            try:
                feed = feedparser.parse(feed_url)
                # Check if feed has entries and no error
                if feed.entries and not feed.get('bozo_exception'):
                    fetch_success = True
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
                else:
                    # Silently count failed feeds instead of showing a warning
                    failed_feeds_count += 1
            except Exception as e:
                # Only show error for critical failures, not individual feeds
                failed_feeds_count += 1
    
    # Convert to DataFrame
    df = pd.DataFrame(articles)
    
    # Drop duplicates by title
    if not df.empty:
        df = df.drop_duplicates(subset=['title'])
    
    # If no successful fetches, try a fallback approach - but don't show individual warnings
    if not fetch_success:
        # Display a single warning about using fallback instead of individual feed failures
        st.warning(f"Unable to fetch {category} news from primary sources. Using fallback method...")
        try:
            # Use Google News RSS as fallback
            fallback_url = f"https://news.google.com/rss/search?q={category}+health&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(fallback_url)
            for entry in feed.entries[:20]:  # Get more from fallback
                content = entry.get('summary', '')
                clean_content = BeautifulSoup(content, "html.parser").get_text(separator=' ', strip=True)
                
                articles.append({
                    "title": entry.get('title', '').strip(),
                    "content": clean_content,
                    "link": entry.get('link', ''),
                    "source": "Google News"
                })
            
            # Update DataFrame
            df = pd.DataFrame(articles)
            if not df.empty:
                df = df.drop_duplicates(subset=['title'])
        except Exception as e:
            st.error(f"Fallback method also failed. Please try a different category.")
        
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

# Function to fetch related videos from YouTube
def fetch_youtube_videos(query, max_results=3, youtube_api_key=None):
    """Fetch related videos from YouTube API"""
    if not youtube_api_key:
        # Provide search links as fallback
        search_query = urlencode({'search_query': query})
        return [{
            "title": f"Videos about: {query}",
            "description": "Search results on YouTube",
            "thumbnail": "https://www.youtube.com/img/desktop/yt_1200.png",  # YouTube logo as placeholder
            "link": f"https://www.youtube.com/results?{search_query}"
        }]
        
    try:
        base_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': max_results,
            'key': youtube_api_key,
            'relevanceLanguage': 'en'
        }
        
        response = requests.get(f"{base_url}?{urlencode(params)}")
        if response.status_code != 200:
            st.error(f"YouTube API error: {response.status_code}")
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
        st.error(f"Error fetching videos: {e}")
        return []

# Function to get video recommendations based on keywords
def get_video_recommendations(article_title, article_content, youtube_api_key=None):
    """Generate relevant search queries and get related videos"""
    # Use Gemini to extract key search terms
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    Extract 3 most important search keywords or phrases from this news article that would be good for finding related videos.
    
    ARTICLE TITLE: {article_title}
    ARTICLE CONTENT: {article_content[:500]}
    
    Return only a JSON array of strings with no additional text or explanation.
    Example output: ["keyword1", "keyword2", "keyword phrase 3"]
    """
    
    try:
        with st.spinner("Generating video keywords..."):
            response = model.generate_content(prompt)
            cleaned_response = clean_gemini_response(response.text)
            keywords = json.loads(cleaned_response)
            
            if not isinstance(keywords, list) or len(keywords) == 0:
                keywords = [article_title]
            
        with st.spinner("Fetching related videos..."):
            # Try to use the first (most relevant) keyword
            primary_keyword = keywords[0]
            videos = fetch_youtube_videos(primary_keyword, youtube_api_key=youtube_api_key)
            
            # If we didn't get enough videos, try other keywords
            if len(videos) < 3 and len(keywords) > 1:
                for keyword in keywords[1:]:
                    if len(videos) >= 3:
                        break
                    more_videos = fetch_youtube_videos(keyword, max_results=1, youtube_api_key=youtube_api_key)
                    videos.extend(more_videos)
                    
            return videos
            
    except Exception as e:
        st.error(f"Error generating video recommendations: {e}")
        # Fallback to basic article title search
        return fetch_youtube_videos(article_title, youtube_api_key=youtube_api_key)

# Increment usage count function
def increment_usage():
    """Increment the usage counter in session state"""
    st.session_state.usage_count += 1

# Main Streamlit UI
def main():
    st.title("📰 AI-Powered News & Video Recommender")
    st.write("Discover similar news articles and related videos with the help of AI")
    
    # Check if we need to ask for API keys
    if check_api_requirement():
        api_provided = show_api_form()
        if not api_provided:
            st.info("You can continue using the demo with default API keys, but providing your own ensures uninterrupted service.")
    
    # Get YouTube API key (will be None if user hasn't provided one)
    youtube_api_key = configure_apis()
    
    # Display usage information
    if st.session_state.usage_count > 0 and not st.session_state.api_keys_provided:
        st.info(f"Demo uses remaining: {max(0, 2 - st.session_state.usage_count)}")
    
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
        if st.button("Get Similar Articles & Videos", type="primary"):
            # Increment usage count when recommendations are requested
            increment_usage()
            
            # Create two tabs for articles and videos
            tab1, tab2 = st.tabs(["📰 Similar Articles", "🎬 Related Videos"])
            
            # Task 1: Get article recommendations
            with st.spinner("AI is finding similar articles..."):
                # Add slight delay for better UX
                start_time = time.time()
                
                # Get recommendations
                article_recommendations = get_gemini_recommendations(
                    article_row["title"], 
                    article_row["content"], 
                    news_df
                )
                
                # Ensure minimum perception of AI "thinking"
                elapsed = time.time() - start_time
                if elapsed < 1.5:
                    time.sleep(1.5 - elapsed)
            
            # Task 2: Get video recommendations (in parallel)
            with st.spinner("Finding related videos..."):
                video_recommendations = get_video_recommendations(
                    article_row["title"],
                    article_row["content"],
                    youtube_api_key
                )
            
            # Display article recommendations in the first tab
            with tab1:
                if article_recommendations:
                    st.subheader("🔍 Recommended Articles")
                    
                    # Create columns for recommendations
                    cols = st.columns(min(len(article_recommendations), 3))
                    
                    for i, rec in enumerate(article_recommendations):
                        col_idx = i % len(cols)
                        with cols[col_idx]:
                            st.markdown(f"**{i+1}. {rec['title']}**")
                            st.markdown(f"[Read Article]({rec['link']})")
                            st.markdown("---")
                else:
                    st.warning("Could not find similar articles. Try selecting a different article.")
            
            # Display video recommendations in the second tab
            with tab2:
                if video_recommendations:
                    st.subheader("🎬 Related Videos")
                    
                    # Create columns for video thumbnails
                    video_cols = st.columns(min(len(video_recommendations), 3))
                    
                    for i, video in enumerate(video_recommendations):
                        col_idx = i % len(video_cols)
                        with video_cols[col_idx]:
                            # Display video card with thumbnail
                            st.markdown(f"""
                            <div class="video-card">
                                <a href="{video['link']}" target="_blank">
                                    <img src="{video.get('thumbnail', 'https://www.youtube.com/img/desktop/yt_1200.png')}" class="video-thumbnail">
                                </a>
                                <p class="video-title">{video['title']}</p>
                                <a href="{video['link']}" target="_blank">Watch on YouTube</a>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.warning("Could not find related videos. Try selecting a different article.")
            
            # Check if we should display API key prompt after this usage
            if st.session_state.usage_count >= 2 and not st.session_state.api_keys_provided:
                st.warning("You've reached the demo limit. Please provide your API keys to continue using all features.")

if __name__ == "__main__":
    main()
