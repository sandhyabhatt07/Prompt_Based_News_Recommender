# 📰 AI-Powered News Recommender

An intelligent, category-based news recommendation web app that uses **Google's Gemini AI** and advanced **prompt engineering** to suggest similar articles based on semantic relevance.

---

## 📌 Features

- 🔍 **Category-based News Fetching** (World, Technology, Sports, etc.)
- 🤖 **AI-Powered Recommendations** using Google Gemini 1.5
- 🎯 **Semantic Matching**: Finds articles similar in topic, entities, and perspective
- 🧠 **Prompt Engineering**: Crafted prompts guide the model for accurate, formatted outputs
- ⚡ **Fast & Clean UI** with Streamlit
- 🧼 HTML content cleaning via BeautifulSoup
- 🗃️ RSS feed aggregation from top global sources

---

---

## 🚀 How It Works

### 1. **User Flow via Streamlit (`app.py`)**

1. Choose a **news category** (e.g. World, Tech).
2. Select an article from the fetched feed.
3. Click **“Get Similar Articles”**.
4. The app sends a **prompt-engineered request** to Gemini to analyze the article and find 5 semantically similar articles from the same feed.

### 2. **Recommendation Logic (`recommender.py`)**

- Uses **structured prompts** to:
  - Emphasize semantic relevance (topic, entities, angles).
  - Request exact JSON output.
  - Exclude the reference article from results.
- Validates Gemini response and returns clean, structured recommendations.

---

## ✨ Example Gemini Prompt Snippet

```txt
# TASK: Find 5 news articles most similar to the reference article.

# REFERENCE ARTICLE:
TITLE: {article_title}
CONTENT: {article_content}

# AVAILABLE ARTICLES:
ID: 1
TITLE: AI breaks new ground...
...

# CRITERIA FOR SIMILARITY:
- Topic relevance
- Similar entities/events
- Diverse but relevant perspectives

# OUTPUT FORMAT:
[
  {"title": "Article A", "link": "https://..."},
  ...
]

## 🗞️ Supported News Sources
Categorized and high-quality RSS feeds from:

NYTimes, BBC, The Guardian, Al Jazeera

Wired, Verge, ESPN, Politico, Billboard, and more.

## 📚 Prompt Engineering Highlights
Structured instruction block (SYSTEM, TASK, FORMAT)

Explicit constraints:

No markdown

Pure JSON array

Exclude reference article

Encourages diverse sources, and balances semantic similarity with content diversity.

