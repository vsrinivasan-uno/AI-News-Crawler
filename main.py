#!/usr/bin/env python3
"""
AI News Crawler - Python Version
A comprehensive AI news scraping and email digest system
"""

import os
import sys
import json
import sqlite3
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl
from urllib.parse import urljoin, urlparse
import feedparser
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import time
import schedule
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_news_crawler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class NewsItem:
    """Data class for news items"""
    title: str
    content: str
    link: str
    source: str
    date: str
    score: int = 0
    comments: int = 0
    author: str = ""
    category: str = ""
    type: str = ""
    engagement: int = 0
    is_trending: bool = False
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        # Handle environment variables with proper fallback for empty strings
        self.resend_api_key = os.getenv('RESEND_API_KEY') or None
        self.smtp_server = os.getenv('SMTP_SERVER') or 'smtp.gmail.com'
        
        # Handle SMTP_PORT with proper fallback for empty strings
        smtp_port_str = os.getenv('SMTP_PORT', '587')
        self.smtp_port = int(smtp_port_str) if smtp_port_str and smtp_port_str.strip() else 587
        
        self.email_user = os.getenv('EMAIL_USER') or None
        self.email_password = os.getenv('EMAIL_PASSWORD') or None
        
    def send_email_via_resend(self, to_emails: List[str], subject: str, html_content: str) -> bool:
        """Send email using Resend API"""
        if not self.resend_api_key:
            logger.error("RESEND_API_KEY not found in environment variables")
            logger.error("Please add RESEND_API_KEY to your GitHub repository secrets")
            logger.error("Get a free API key from: https://resend.com")
            return False
            
        try:
            import requests
            
            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {self.resend_api_key}",
                "Content-Type": "application/json"
            }
            
            # Batch emails in groups of 50 (Resend free tier limit)
            batch_size = 50
            for i in range(0, len(to_emails), batch_size):
                batch = to_emails[i:i + batch_size]
                
                payload = {
                    "from": "Vishva's AI Digest <Vishva@Luke.ai>",
                    "to": batch,
                    "subject": subject,
                    "html": html_content
                }
                
                response = requests.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    logger.info(f"Email sent successfully to {len(batch)} recipients via Resend")
                else:
                    logger.error(f"Resend API error: {response.status_code} - {response.text}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error sending email via Resend: {e}")
            return False
    
    def send_email_via_smtp(self, to_emails: List[str], subject: str, html_content: str) -> bool:
        """Send email using SMTP"""
        if not self.email_user or not self.email_password:
            logger.error("SMTP credentials not configured")
            logger.error("Either set RESEND_API_KEY (recommended) or configure SMTP:")
            logger.error("- EMAIL_USER: Your email address")  
            logger.error("- EMAIL_PASSWORD: Your email password/app password")
            return False
            
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_user
            msg['To'] = ', '.join(to_emails)
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
                
            logger.info(f"Email sent successfully to {len(to_emails)} recipients via SMTP")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email via SMTP: {e}")
            return False
    
    def send_email(self, to_emails: List[str], subject: str, html_content: str) -> bool:
        """Send email using available method"""
        logger.info(f"🔍 Email configuration check:")
        logger.info(f"   - RESEND_API_KEY: {'✅ Found' if self.resend_api_key else '❌ Not found'}")
        logger.info(f"   - EMAIL_USER: {'✅ Found' if self.email_user else '❌ Not found'}")
        logger.info(f"   - EMAIL_PASSWORD: {'✅ Found' if self.email_password else '❌ Not found'}")
        
        if self.resend_api_key:
            logger.info("📧 Attempting to send via Resend API...")
            return self.send_email_via_resend(to_emails, subject, html_content)
        else:
            logger.info("📧 Attempting to send via SMTP (fallback)...")
            return self.send_email_via_smtp(to_emails, subject, html_content)
    
    def format_digest_email(self, content: Dict[str, List[NewsItem]]) -> str:
        """Format the news content into HTML email"""
        reddit_items = content.get('reddit', [])
        research_items = content.get('research', [])
        news_items = content.get('news', [])
        
        def truncate_content(text: str, max_length: int = 150) -> str:
            if not text or text.strip() == '':
                return 'Click to read the full article for more details.'
            
            # Clean HTML and extra spaces
            clean_text = re.sub(r'<[^>]*>', '', text)
            clean_text = re.sub(r'&[^;]+;', ' ', clean_text)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            if len(clean_text) == 0:
                return 'Click to read the full article for more details.'
            
            return clean_text[:max_length] + '...' if len(clean_text) > max_length else clean_text
        
        today = datetime.now(timezone.utc).strftime('%A, %B %d, %Y')
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI Intelligence Brief</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background-color: #f5f5f5; line-height: 1.6;">
            
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px 0;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden;">
                            
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 40px 30px; text-align: center;">
                                    <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">AI Intelligence Brief</h1>
                                    <p style="margin: 8px 0 0 0; color: rgba(255,255,255,0.9); font-size: 16px; font-weight: 400;">Your daily digest of AI breakthroughs</p>
                                    <p style="margin: 12px 0 0 0; color: rgba(255,255,255,0.8); font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">{today}</p>
                                </td>
                            </tr>
                            
                            <!-- Research Papers Section -->
                            <tr>
                                <td style="padding: 30px;">
                                    <h2 style="margin: 0 0 25px 0; color: #1f2937; font-size: 22px; font-weight: 700; border-bottom: 2px solid #e5e7eb; padding-bottom: 12px;">
                                        🔬 Research Papers <span style="background: #3b82f6; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-left: 10px;">{len(research_items)}</span>
                                    </h2>
        """
        
        if research_items:
            for paper in research_items:
                authors = getattr(paper, 'authors', [])
                author_text = ', '.join(authors[:2])
                if len(authors) > 2:
                    author_text += ' et al.'
                
                html += f"""
                <div style="margin-bottom: 20px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; background-color: #fafafa;">
                    <div style="padding: 24px;">
                        <h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 18px; font-weight: 600; line-height: 1.4;">
                            <a href="{paper.link}" style="color: #1f2937; text-decoration: none;" target="_blank">{paper.title}</a>
                        </h3>
                        <p style="margin: 0 0 15px 0; color: #6b7280; font-size: 14px; line-height: 1.5;">
                            📄 arXiv • 👥 {author_text} • 📅 {datetime.fromisoformat(paper.date.replace('Z', '+00:00')).strftime('%B %d, %Y') if paper.date else 'Today'}
                        </p>
                        <p style="margin: 0 0 18px 0; color: #4b5563; font-size: 15px; line-height: 1.6;">{truncate_content(paper.content, 180)}</p>
                        <a href="{paper.link}" style="display: inline-block; background: #3b82f6; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: 500;" target="_blank">Read Paper →</a>
                    </div>
                </div>
                """
        else:
            html += """
            <p style="text-align: center; color: #6b7280; font-style: italic; padding: 40px 20px; background-color: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">No new research papers today. Check back tomorrow for the latest AI research!</p>
            """
        
        # Industry News Section
        html += f"""
                                </td>
                            </tr>
                            
                            <!-- Industry News Section -->
                            <tr>
                                <td style="padding: 0 30px 30px 30px;">
                                    <h2 style="margin: 0 0 25px 0; color: #1f2937; font-size: 22px; font-weight: 700; border-bottom: 2px solid #e5e7eb; padding-bottom: 12px;">
                                        📰 Industry News <span style="background: #3b82f6; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-left: 10px;">{len(news_items)}</span>
                                    </h2>
        """
        
        if news_items:
            for article in news_items:
                html += f"""
                <div style="margin-bottom: 20px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; background-color: #fafafa;">
                    <div style="padding: 24px;">
                        <h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 18px; font-weight: 600; line-height: 1.4;">
                            <a href="{article.link}" style="color: #1f2937; text-decoration: none;" target="_blank">{article.title}</a>
                        </h3>
                        <p style="margin: 0 0 15px 0; color: #6b7280; font-size: 14px; line-height: 1.5;">
                            🏢 {article.source} • 📅 {datetime.fromisoformat(article.date.replace('Z', '+00:00')).strftime('%B %d, %Y') if article.date else 'Today'}
                        </p>
                        <p style="margin: 0 0 18px 0; color: #4b5563; font-size: 15px; line-height: 1.6;">{truncate_content(article.content, 180)}</p>
                        <a href="{article.link}" style="display: inline-block; background: #3b82f6; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: 500;" target="_blank">Read Article →</a>
                    </div>
                </div>
                """
        else:
            html += """
            <p style="text-align: center; color: #6b7280; font-style: italic; padding: 40px 20px; background-color: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">No industry news today. Check back tomorrow for the latest updates!</p>
            """
        
        # Reddit Discussion Section
        html += f"""
                                </td>
                            </tr>
                            
                            <!-- Reddit Discussions Section -->
                            <tr>
                                <td style="padding: 0 30px 30px 30px;">
                                    <h2 style="margin: 0 0 25px 0; color: #1f2937; font-size: 22px; font-weight: 700; border-bottom: 2px solid #e5e7eb; padding-bottom: 12px;">
                                        💬 Community Discussions <span style="background: #3b82f6; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-left: 10px;">{len(reddit_items)}</span>
                                    </h2>
        """
        
        if reddit_items:
            for post in reddit_items:
                html += f"""
                <div style="margin-bottom: 20px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; background-color: #fafafa;">
                    <div style="padding: 24px;">
                        <h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 18px; font-weight: 600; line-height: 1.4;">
                            <a href="{post.link}" style="color: #1f2937; text-decoration: none;" target="_blank">{post.title}</a>
                        </h3>
                        <p style="margin: 0 0 15px 0; color: #6b7280; font-size: 14px; line-height: 1.5;">
                            🏛️ {post.source} • 👤 {post.author} • ⬆️ {post.score} • 💬 {post.comments}
                        </p>
                        <p style="margin: 0 0 18px 0; color: #4b5563; font-size: 15px; line-height: 1.6;">{truncate_content(post.content, 180)}</p>
                        <a href="{post.link}" style="display: inline-block; background: #3b82f6; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: 500;" target="_blank">Join Discussion →</a>
                    </div>
                </div>
                """
        else:
            html += """
            <p style="text-align: center; color: #6b7280; font-style: italic; padding: 40px 20px; background-color: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">No trending discussions today. Check back tomorrow for community insights!</p>
            """
        
        # Footer
        html += """
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                                    <p style="margin: 0 0 10px 0; color: #6b7280; font-size: 14px;">
                                        🤖 Powered by AI News Crawler built by Vishva
                                    </p>
                                    <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                                        This digest was automatically generated and curated for you.
                                    </p>
                                </td>
                            </tr>
                            
                        </table>
                    </td>
                </tr>
            </table>
            
        </body>
        </html>
        """
        
        return html

class ScraperService:
    """Service for scraping AI news from various sources"""
    
    def __init__(self):
        self.session = requests.Session()
        # Improved headers to avoid Reddit blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.driver = None
        
    def setup_selenium(self):
        """Setup Selenium WebDriver"""
        if not self.driver:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("Selenium WebDriver initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Selenium WebDriver: {e}")
                self.driver = None
    
    def close_selenium(self):
        """Close Selenium WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Selenium WebDriver closed")
    
    def is_from_today(self, date_string: str) -> bool:
        """Check if content is from the last 24 hours"""
        try:
            if isinstance(date_string, str):
                content_date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            else:
                content_date = date_string
                
            now = datetime.now(timezone.utc)
            yesterday = now - timedelta(days=1)
            return yesterday <= content_date <= now
        except Exception as e:
            logger.error(f"Error parsing date: {date_string} - {e}")
            return False
    
    def is_from_today_unix(self, unix_timestamp: int) -> bool:
        """Check if content is from the last 24 hours using Unix timestamp"""
        try:
            content_date = datetime.fromtimestamp(unix_timestamp, timezone.utc)
            now = datetime.now(timezone.utc)
            yesterday = now - timedelta(days=1)
            return yesterday <= content_date <= now
        except Exception as e:
            logger.error(f"Error parsing unix timestamp: {unix_timestamp} - {e}")
            return False
    
    def is_significant_content(self, title: str, content: str) -> bool:
        """Check if content contains significant AI-related keywords"""
        significant_keywords = [
            'breakthrough', 'advancement', 'new model', 'state of the art', 'sota',
            'significant', 'revolutionary', 'groundbreaking', 'major', 'important',
            'release', 'announcement', 'launch', 'update', 'improvement',
            'outperforms', 'better than', 'surpasses', 'achieves', 'milestone',
            'gpt', 'llm', 'transformer', 'neural network', 'deep learning',
            'machine learning', 'artificial intelligence', 'ai model'
        ]
        
        text = (title + ' ' + content).lower()
        return any(keyword.lower() in text for keyword in significant_keywords)
    
    def extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text"""
        ai_keywords = [
            'GPT', 'LLM', 'Transformer', 'Neural Network', 'Deep Learning',
            'Machine Learning', 'Computer Vision', 'NLP', 'Robotics',
            'OpenAI', 'Google', 'Meta', 'Anthropic', 'DeepMind'
        ]
        
        found_tags = []
        text_lower = text.lower()
        
        for keyword in ai_keywords:
            if keyword.lower() in text_lower:
                found_tags.append(keyword)
                
        return list(set(found_tags))
    
    def scrape_reddit(self) -> List[NewsItem]:
        """Scrape AI-related posts from Reddit"""
        logger.info("Starting Reddit scraping...")
        results = []
        
        subreddits = [
            {'name': 'artificial', 'category': 'general', 'min_score': 100},
            {'name': 'MachineLearning', 'category': 'research', 'min_score': 50},
            {'name': 'AIdev', 'category': 'development', 'min_score': 30},
            {'name': 'OpenAI', 'category': 'companies', 'min_score': 50},
            {'name': 'deeplearning', 'category': 'research', 'min_score': 50},
            {'name': 'artificial_intelligence', 'category': 'general', 'min_score': 100},
            {'name': 'AIethics', 'category': 'ethics', 'min_score': 50},
            {'name': 'AGI', 'category': 'research', 'min_score': 30},
            {'name': 'ChatGPT', 'category': 'applications', 'min_score': 100},
            {'name': 'StableDiffusion', 'category': 'applications', 'min_score': 50},
            {'name': 'LocalLLaMA', 'category': 'development', 'min_score': 30}
        ]
        
        for subreddit in subreddits:
            try:
                logger.info(f"Scraping r/{subreddit['name']}...")
                url = f"https://www.reddit.com/r/{subreddit['name']}/hot.json"
                
                # Add rate limiting to avoid being blocked
                time.sleep(1)  # Wait 1 second between requests
                
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'data' in data and 'children' in data['data']:
                    posts = []
                    for post in data['data']['children']:
                        post_data = post['data']
                        
                        created_utc = post_data.get('created_utc', 0)
                        score = post_data.get('score', 0)
                        comments = post_data.get('num_comments', 0)
                        
                        if (self.is_from_today_unix(created_utc) and 
                            score > subreddit['min_score'] and
                            self.is_significant_content(post_data.get('title', ''), post_data.get('selftext', ''))):
                            
                            news_item = NewsItem(
                                title=post_data.get('title', ''),
                                content=post_data.get('selftext', ''),
                                link=f"https://reddit.com{post_data.get('permalink', '')}",
                                source=f"Reddit - r/{subreddit['name']}",
                                date=datetime.fromtimestamp(created_utc, timezone.utc).isoformat(),
                                score=score,
                                comments=comments,
                                author=post_data.get('author', ''),
                                category=subreddit['category'],
                                type='reddit_post',
                                engagement=score + (comments * 2),
                                is_trending=True,
                                tags=self.extract_tags(post_data.get('title', '') + ' ' + post_data.get('selftext', ''))
                            )
                            posts.append(news_item)
                    
                    results.extend(posts)
                    logger.info(f"Found {len(posts)} significant posts from today in r/{subreddit['name']}")
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    logger.warning(f"Reddit blocked access to r/{subreddit['name']} (403). This is common and not critical.")
                else:
                    logger.error(f"HTTP error scraping r/{subreddit['name']}: {e}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error scraping r/{subreddit['name']}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error scraping r/{subreddit['name']}: {e}")
        
        # Sort by engagement and return top 15
        results.sort(key=lambda x: x.engagement, reverse=True)
        return results[:15]
    
    def scrape_research_papers(self) -> List[NewsItem]:
        """Scrape recent AI research papers from arXiv"""
        logger.info("Starting research paper scraping...")
        results = []
        
        categories = [
            'cs.AI',    # Artificial Intelligence
            'cs.LG',    # Machine Learning
            'cs.CL',    # Computation and Language
            'cs.CV',    # Computer Vision
            'cs.RO',    # Robotics
            'cs.NE',    # Neural and Evolutionary Computing
            'stat.ML'   # Machine Learning (Statistics)
        ]
        
        paper_ids = set()  # Track unique papers
        three_days_ago = datetime.now(timezone.utc) - timedelta(days=3)
        
        for category in categories:
            try:
                logger.info(f"Searching arXiv category: {category}")
                url = "http://export.arxiv.org/api/query"
                params = {
                    'search_query': f'cat:{category}',
                    'sortBy': 'submittedDate',
                    'sortOrder': 'descending',
                    'max_results': 30
                }
                
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                # Parse XML response
                soup = BeautifulSoup(response.content, 'xml')
                entries = soup.find_all('entry')
                
                for entry in entries:
                    try:
                        title = entry.find('title').text.strip()
                        abstract = entry.find('summary').text.strip()
                        published = entry.find('published').text
                        link = entry.find('link')['href']
                        
                        # Parse date
                        paper_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                        
                        # Check if paper is from last 3 days
                        if paper_date >= three_days_ago:
                            # Extract paper ID for deduplication
                            paper_id = link.split('/')[-1]
                            
                            if paper_id not in paper_ids:
                                paper_ids.add(paper_id)
                                
                                # Extract authors
                                authors = [author.find('name').text for author in entry.find_all('author')]
                                
                                # Extract categories
                                paper_categories = [cat['term'] for cat in entry.find_all('category')]
                                
                                news_item = NewsItem(
                                    title=title,
                                    content=abstract,
                                    link=link,
                                    source='arXiv',
                                    date=paper_date.isoformat(),
                                    author=', '.join(authors[:3]),  # First 3 authors
                                    category=category,
                                    type='research_paper',
                                    tags=self.extract_tags(title + ' ' + abstract)
                                )
                                
                                # Add authors as attribute for email formatting
                                news_item.authors = authors
                                
                                results.append(news_item)
                                
                    except Exception as e:
                        logger.error(f"Error parsing arXiv entry: {e}")
                        
            except Exception as e:
                logger.error(f"Error scraping arXiv category {category}: {e}")
        
        logger.info(f"Found {len(results)} recent research papers")
        return results[:10]  # Return top 10 most recent
    
    def scrape_ai_news(self) -> List[NewsItem]:
        """Scrape AI news from various news sources"""
        logger.info("Starting AI news scraping...")
        results = []
        
        news_sources = [
            {
                'name': 'VentureBeat AI',
                'url': 'https://venturebeat.com/ai/feed/',
                'type': 'rss'
            },
            {
                'name': 'TechCrunch AI',
                'url': 'https://techcrunch.com/category/artificial-intelligence/feed/',
                'type': 'rss'
            },
            {
                'name': 'MIT Technology Review AI',
                'url': 'https://www.technologyreview.com/topic/artificial-intelligence/feed/',
                'type': 'rss'
            }
        ]
        
        for source in news_sources:
            try:
                logger.info(f"Scraping {source['name']}...")
                
                if source['type'] == 'rss':
                    feed = feedparser.parse(source['url'])
                    
                    for entry in feed.entries:
                        try:
                            # Parse publication date
                            published = getattr(entry, 'published_parsed', None)
                            if published:
                                pub_date = datetime(*published[:6], tzinfo=timezone.utc)
                                
                                # Check if article is from last 24 hours
                                if self.is_from_today(pub_date.isoformat()):
                                    content = getattr(entry, 'description', '') or getattr(entry, 'summary', '')
                                    
                                    if self.is_significant_content(entry.title, content):
                                        news_item = NewsItem(
                                            title=entry.title,
                                            content=content,
                                            link=entry.link,
                                            source=source['name'],
                                            date=pub_date.isoformat(),
                                            author=getattr(entry, 'author', ''),
                                            category='news',
                                            type='news_article',
                                            tags=self.extract_tags(entry.title + ' ' + content)
                                        )
                                        results.append(news_item)
                                        
                        except Exception as e:
                            logger.error(f"Error parsing news entry from {source['name']}: {e}")
                            
            except Exception as e:
                logger.error(f"Error scraping {source['name']}: {e}")
        
        logger.info(f"Found {len(results)} recent news articles")
        return results[:10]  # Return top 10 most recent
    
    def scrape_all_sources(self) -> Dict[str, List[NewsItem]]:
        """Scrape all sources and return organized results"""
        logger.info("Starting comprehensive AI news scraping...")
        
        try:
            # Scrape all sources
            reddit_results = self.scrape_reddit()
            research_results = self.scrape_research_papers()
            news_results = self.scrape_ai_news()
            
            results = {
                'reddit': reddit_results,
                'research': research_results,
                'news': news_results
            }
            
            total_items = len(reddit_results) + len(research_results) + len(news_results)
            logger.info(f"Scraping completed. Total items: {total_items}")
            logger.info(f"  - Reddit posts: {len(reddit_results)}")
            logger.info(f"  - Research papers: {len(research_results)}")
            logger.info(f"  - News articles: {len(news_results)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error during comprehensive scraping: {e}")
            return {'reddit': [], 'research': [], 'news': []}
        finally:
            self.close_selenium()

class EmailListManager:
    """Manage email lists configuration"""
    
    def __init__(self):
        self.email_lists = {
            'main': [
                'vishvaluke@gmail.com',
                'vsrinivasan@unomaha.edu',
                'vishvaluke@proton.me'
            ],
            'team': [
                # Add team emails here
            ],
            'vip': [
                # Add VIP emails here
            ],
            'test': [
                'delivered@resend.dev',  # Resend test email
                'vishvaluke@gmail.com'
            ]
        }
        
        self.config = {
            'active_list': 'main',  # Options: 'main', 'team', 'vip', 'test', 'all'
            'include_registered_users': True,
            'custom_subject': None
        }
    
    def get_active_email_list(self) -> List[str]:
        """Get the active email list"""
        if self.config['active_list'] == 'all':
            # Combine all lists (remove duplicates)
            all_emails = []
            for email_list in self.email_lists.values():
                all_emails.extend(email_list)
            return list(set(all_emails))  # Remove duplicates
        
        return self.email_lists.get(self.config['active_list'], [])

class DatabaseManager:
    """Simple SQLite database manager for logging"""
    
    def __init__(self, db_path: str = 'ai_news_crawler.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create runs table to track scraping runs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraping_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    reddit_count INTEGER DEFAULT 0,
                    research_count INTEGER DEFAULT 0,
                    news_count INTEGER DEFAULT 0,
                    total_count INTEGER DEFAULT 0,
                    email_sent BOOLEAN DEFAULT FALSE,
                    recipients_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'completed',
                    error_message TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def log_scraping_run(self, results: Dict[str, List[NewsItem]], email_sent: bool, 
                        recipients_count: int, status: str = 'completed', error_message: str = None):
        """Log a scraping run to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            reddit_count = len(results.get('reddit', []))
            research_count = len(results.get('research', []))
            news_count = len(results.get('news', []))
            total_count = reddit_count + research_count + news_count
            
            cursor.execute('''
                INSERT INTO scraping_runs 
                (timestamp, reddit_count, research_count, news_count, total_count, 
                 email_sent, recipients_count, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(timezone.utc).isoformat(),
                reddit_count,
                research_count,
                news_count,
                total_count,
                email_sent,
                recipients_count,
                status,
                error_message
            ))
            
            conn.commit()
            conn.close()
            logger.info("Scraping run logged to database")
            
        except Exception as e:
            logger.error(f"Error logging scraping run: {e}")

def send_daily_digest():
    """Main function to scrape content and send daily digest"""
    logger.info("🚀 Starting AI News Daily Digest Process")
    
    # Initialize services
    scraper = ScraperService()
    email_service = EmailService()
    email_manager = EmailListManager()
    db_manager = DatabaseManager()
    
    email_sent = False
    recipients_count = 0
    error_message = None
    
    try:
        # Scrape all sources
        logger.info("📡 Scraping AI content from all sources...")
        results = scraper.scrape_all_sources()
        
        # Get email list
        email_list = email_manager.get_active_email_list()
        
        if not email_list:
            logger.warning("⚠️ No email addresses found in active email list")
            error_message = "No email addresses configured"
        else:
            # Send email digest
            logger.info(f"📧 Sending digest to {len(email_list)} recipients...")
            
            subject = email_manager.config.get('custom_subject') or 'AI Intelligence Brief'
            html_content = email_service.format_digest_email(results)
            
            email_sent = email_service.send_email(email_list, subject, html_content)
            recipients_count = len(email_list) if email_sent else 0
            
            if email_sent:
                logger.info("✅ Daily digest sent successfully!")
            else:
                logger.error("❌ Failed to send daily digest")
                error_message = "Failed to send email"
        
        # Log to database
        status = 'completed' if email_sent or not email_list else 'failed'
        db_manager.log_scraping_run(results, email_sent, recipients_count, status, error_message)
        
        # Print summary
        total_items = sum(len(items) for items in results.values())
        logger.info(f"""
📊 Daily Digest Summary:
   - Reddit Posts: {len(results.get('reddit', []))}
   - Research Papers: {len(results.get('research', []))}
   - News Articles: {len(results.get('news', []))}
   - Total Items: {total_items}
   - Email Sent: {'✅' if email_sent else '❌'}
   - Recipients: {recipients_count}
        """)
        
    except Exception as e:
        logger.error(f"❌ Error in daily digest process: {e}")
        error_message = str(e)
        db_manager.log_scraping_run({}, False, 0, 'failed', error_message)
        raise

def main():
    """Main function - entry point for the application"""
    logger.info("🤖 AI News Crawler - Python Version")
    logger.info("===================================")
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test':
            logger.info("🧪 Running in test mode...")
            send_daily_digest()
            
        elif command == 'schedule':
            logger.info("⏰ Running in scheduled mode...")
            # Schedule daily digest at 6 PM
            schedule.every().day.at("18:00").do(send_daily_digest)
            
            logger.info("📅 Scheduled daily digest at 6:00 PM")
            logger.info("⏳ Waiting for scheduled time... (Press Ctrl+C to stop)")
            
            try:
                while True:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("⏹️ Scheduler stopped by user")
                
        elif command == 'daemon':
            logger.info("🔄 Running in daemon mode...")
            # Schedule daily digest at 6 PM and run immediately once
            send_daily_digest()  # Run immediately
            
            schedule.every().day.at("18:00").do(send_daily_digest)
            logger.info("📅 Scheduled daily digest at 6:00 PM")
            logger.info("🔄 Running in continuous mode... (Press Ctrl+C to stop)")
            
            try:
                while True:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("⏹️ Daemon stopped by user")
                
        else:
            logger.error(f"❌ Unknown command: {command}")
            print_usage()
            
    else:
        # Default: run once
        logger.info("▶️ Running single digest...")
        send_daily_digest()

def print_usage():
    """Print usage information"""
    print("""
Usage: python main.py [command]

Commands:
  (no command)  - Run once and send digest immediately
  test         - Run in test mode (same as no command)
  schedule     - Run scheduler that sends digest daily at 6 PM
  daemon       - Run once immediately, then schedule daily at 6 PM

Environment Variables:
  RESEND_API_KEY    - API key for Resend email service (recommended)
  EMAIL_USER        - SMTP email username (fallback)
  EMAIL_PASSWORD    - SMTP email password (fallback)
  SMTP_SERVER       - SMTP server (default: smtp.gmail.com)
  SMTP_PORT         - SMTP port (default: 587)

Examples:
  python main.py                # Run once
  python main.py test          # Test run
  python main.py schedule      # Schedule daily digest
  python main.py daemon        # Run once + schedule daily
    """)

if __name__ == "__main__":
    main() 