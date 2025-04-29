# AI-Powered News & Video Recommender

![News & Video Recommender](https://img.shields.io/badge/AI-Powered-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=Streamlit&logoColor=white) ![Gemini AI](https://img.shields.io/badge/Google-Gemini_AI-4285F4?style=flat&logo=google&logoColor=white) ![YouTube API](https://img.shields.io/badge/YouTube-API-FF0000?style=flat&logo=youtube&logoColor=white)

An AI powered web application built with Streamlit that leverages Google's Gemini AI to provide intelligent news article recommendations and related video content based on semantic similarity.

## 🌟 Features

- **Category-Based News Aggregation**: Collects and organizes news from multiple reliable sources across various categories.
- **AI-Powered Article Recommendations**: Uses semantic similarity via Gemini AI to suggest related news articles.
- **Intelligent Video Discovery**: Automatically extracts key topics and finds relevant videos.
- **Responsive UI**: Clean, modern interface with article previews and video thumbnails.
- **Multi-source Content**: Aggregates content from various news outlets for diverse perspectives.

## 🧠 Technical Implementation

### Semantic Similarity Engine

The recommendation system uses advanced NLP techniques through Google's Gemini AI to understand the context and meaning of articles:

- **Content Analysis**: Extracts and interprets the semantic meaning of article content rather than just matching keywords.
- **Topic Correlation**: Identifies relationships between topics and subtopics across different articles.
- **Entity Recognition**: Recognizes people, organizations, events, and other entities mentioned in articles to establish connections.

### Advanced Prompt Engineering

The application employs sophisticated prompt engineering techniques to optimize AI responses:

- **Structured Instructions**: Well-defined system and task instructions guide the AI model.
- **Context Enrichment**: Provides necessary context about articles to improve recommendation quality.
- **Output Formatting**: Strict output structure requirements ensure consistent, parseable responses.
- **Constraints & Examples**: Clear constraints and examples help the model generate properly formatted outputs.

  ## Demo:
  ![Demo Video](assets/Demo3.gif)

Example prompt structure:
```python
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
...
"""
```

### Multi-Layer Fallback Mechanisms

The application implements robust fallback systems to ensure reliability:

- **RSS Feed Redundancy**: Multiple sources per category ensure content availability even if some feeds fail.
- **Google News Fallback**: If primary RSS feeds fail, falls back to Google News search API.
- **Response Parsing Resilience**: Multiple parsing strategies for handling various AI response formats.
- **Video Recommendation Fallbacks**: Alternative keyword generation and search link provision when APIs fail.
- **Error Handling**: Comprehensive error catching with user-friendly messages.

### Video Content Discovery

The application intelligently connects news articles with relevant video content:

- **AI-Generated Search Queries**: Uses Gemini AI to extract optimal search keywords from article content.
- **YouTube API Integration**: Fetches relevant videos using the YouTube Data API.
- **Multi-Keyword Strategy**: Tries alternative keywords if initial searches don't yield enough results.
- **Visual Presentation**: Attractive thumbnail-based video cards for engaging user experience.

## 🛠️ Technology Stack

- **Frontend**: Streamlit for interactive web interface
- **AI**: Google Gemini 1.5 Flash for fast, efficient content analysis
- **Data Processing**: Pandas for data manipulation and analysis
- **Content Fetching**: Feedparser for RSS feed consumption
- **HTML Parsing**: BeautifulSoup for content cleaning
- **External APIs**: YouTube Data API v3 for video recommendations

## 📋 Installation & Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/sandhyabhatt07/Prompt_Based_News_Recommender.git
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys:
   ```
   GOOGLE_API_KEY=your_gemini_api_key
   YOUTUBE_API_KEY=your_youtube_api_key
   ```

4. Run the application:
   ```bash
   streamlit run app.py
   ```

## 🔄 How It Works

1. **News Aggregation**: The application fetches news from multiple RSS feeds based on selected category.
2. **User Selection**: User selects an interesting news article.
3. **AI Analysis**: Gemini AI analyzes the article content and available news corpus.
4. **Recommendation Generation**: The system identifies semantically similar articles.
5. **Video Discovery**: AI extracts key search terms and finds related videos.
6. **Content Presentation**: Articles and videos are presented in an intuitive interface.


*Developed with ❤️ using AI-powered semantic analysis and recommendation algorithms*
