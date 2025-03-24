# Prompt-Based News Recommender

This is a Python-based news recommender system that uses generative AI from Google (Gemini) to recommend similar news articles based on a given article's title and content. The system fetches news articles from popular RSS feeds, processes them, and generates relevant recommendations using **prompt engineering** with the Gemini model.

## Features

- Fetches news articles from RSS feeds (NYTimes, BBC, AlJazeera).
- Uses **prompting techniques** with **Google Gemini** to recommend similar news articles.
- Can be deployed as a web app using **Streamlit** for an interactive user interface.
- Integrates with **BeautifulSoup** and **Feedparser** for data processing and RSS feed handling.

## Installation

Follow the steps below to set up the project locally:

### Prerequisites

- Python 3.x
- Git
- Google Cloud API Key (for accessing Gemini)

### Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/sandhyabhatt07/Prompt_Based_News_Recommender.git
   cd Prompt_Based_News_Recommender
