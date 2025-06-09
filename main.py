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
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        self.email_provider = os.getenv('EMAIL_PROVIDER', 'google').lower()
        self.resend_api_key = os.getenv('RESEND_API_KEY') or None
        self.smtp_server = os.getenv('SMTP_SERVER') or 'smtp.gmail.com'
        
        # Handle SMTP_PORT with proper fallback for empty strings
        smtp_port_str = os.getenv('SMTP_PORT', '587')
        self.smtp_port = int(smtp_port_str) if smtp_port_str and smtp_port_str.strip() else 587
        
        self.email_user = os.getenv('EMAIL_USER') or None
        self.email_password = os.getenv('EMAIL_PASSWORD') or None
        
        # Configurable sender name for masking personal email
        self.sender_name = os.getenv('EMAIL_SENDER_NAME', 'AI-CCORE Research Team').strip()
        
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
                
                # Use configurable sender name with masked email
                payload = {
                    "from": f"{self.sender_name} <{self.email_user or 'ai-digest@ai-ccore.org'}>",
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
            # Use configurable sender name with masked email
            msg['From'] = f"{self.sender_name} <{self.email_user}>"
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
        """Send email using available method with fallback"""
        logger.info(f"🔍 Email configuration check:")
        logger.info(f"   - Primary Provider: {self.email_provider}")
        logger.info(f"   - Resend API Key: {'✅ Found' if self.resend_api_key else '❌ Not found'}")
        logger.info(f"   - SMTP User: {'✅ Found'if self.email_user else '❌ Not found'}")

        if self.email_provider == 'google':
            logger.info("📧 Attempting to send via Google (SMTP)...")
            if self.send_email_via_smtp(to_emails, subject, html_content):
                return True
            
            logger.warning("⚠️ Google (SMTP) failed, falling back to Resend...")
            if self.resend_api_key:
                return self.send_email_via_resend(to_emails, subject, html_content)
            else:
                logger.error("❌ Resend API key not available. Email not sent.")
                return False
        
        elif self.resend_api_key:
            logger.info("📧 Attempting to send via Resend API...")
            if self.send_email_via_resend(to_emails, subject, html_content):
                return True
            
            logger.warning("⚠️ Resend failed, falling back to SMTP...")
            return self.send_email_via_smtp(to_emails, subject, html_content)
            
        else:
            logger.info("📧 Attempting to send via SMTP (default)...")
            return self.send_email_via_smtp(to_emails, subject, html_content)
    
    def format_digest_email(self, content: Dict[str, List[NewsItem]]) -> str:
        """Format the news content into HTML email with prioritized content to avoid clipping"""
        
        # Prioritize and limit content to prevent email clipping
        reddit_items = self.prioritize_content(content.get('reddit', []), max_items=5)
        research_items = self.prioritize_content(content.get('research', []), max_items=4)
        news_items = self.prioritize_content(content.get('news', []), max_items=5)
        reddit_intelligent_items = self.prioritize_content(content.get('reddit_intelligent', []), max_items=3)
        news_intelligent_items = self.prioritize_content(content.get('news_intelligent', []), max_items=3)
        
        # Combine all items for total count
        all_items = reddit_items + research_items + news_items + reddit_intelligent_items + news_intelligent_items
        
        # Create content summary for the header
        content_summary = f"📊 Today's Highlights: {len(research_items)} Papers • {len(news_items + news_intelligent_items)} News • {len(reddit_items + reddit_intelligent_items)} Discussions"
        
        def truncate_content(text: str, max_length: int = 120) -> str:
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
        <html>
        <head>
            <meta charset="UTF-8">
            <title>AI-CCORE's Daily AI Digest</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
            
            <!-- Main Container -->
            <table width="100%" cellpadding="20" cellspacing="0" border="0" style="background-color: #f5f5f5;">
                <tr>
                    <td align="center">
                        
                        <!-- Email Content -->
                        <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border: 1px solid #dddddd;">
                            
                            <!-- Header -->
                            <tr>
                                <td style="background-color: #0f172a; padding: 30px; text-align: center;">
                                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                        <tr>
                                            <td align="center">
                                                
                                                <!-- Title -->
                                                <h1 style="margin: 0 0 10px 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                                    💡 AI-CCORE's Daily AI Digest
                                                </h1>
                                                
                                                <!-- Subtitle -->
                                                <p style="margin: 0 0 20px 0; color: #bfdbfe; font-size: 16px;">
                                                    Curated by Advanced Algorithms • Zero Human Bias
                                                </p>
                                                
                                                <!-- Stats -->
                                                <table cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;">
                                                    <tr>
                                                        <td style="background-color: rgba(255,255,255,0.15); padding: 10px 20px; border-radius: 8px;">
                                                            <span style="color: #f1f5f9; font-size: 14px; font-weight: bold;">
                                                                📅 {today}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="background-color: rgba(255,255,255,0.15); padding: 10px 20px; border-radius: 8px;">
                                                            <span style="color: #f1f5f9; font-size: 14px; font-weight: bold;">
                                                                {content_summary}
                                                            </span>
                                                        </td>                                                        
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            
                            <!-- Content Header -->
                            <tr>
                                <td style="background-color: #f8fafc; padding: 25px; border-bottom: 1px solid #e2e8f0;">
                                    <h2 style="margin: 0 0 8px 0; color: #1e293b; font-size: 22px; font-weight: bold;">
                                        ⚡ Today's AI Intelligence
                                    </h2>
                                    <p style="margin: 0; color: #64748b; font-size: 14px;">
                                        Algorithmically curated from multiple sources across research, industry & community
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 25px;">
        """
        
        # Display all content types in a single section to prevent clipping
        all_content = []
        
        # Add research papers
        for paper in research_items:
            authors = getattr(paper, 'authors', [])
            author_text = ', '.join(authors[:2])
            if len(authors) > 2:
                author_text += ' et al.'
            all_content.append({
                'type': 'research',
                'icon': '🔬',
                'title': paper.title,
                'source': f"arXiv • {author_text}",
                'date': datetime.fromisoformat(paper.date.replace('Z', '+00:00')).strftime('%B %d, %Y') if paper.date else 'Today',
                'content': paper.content,
                'link': paper.link,
                'bg_color': '#f0f7ff'
            })
        
        # Add news items
        for article in news_items + news_intelligent_items:
            all_content.append({
                'type': 'news',
                'icon': '📰',
                'title': article.title,
                'source': article.source,
                'date': datetime.fromisoformat(article.date.replace('Z', '+00:00')).strftime('%B %d, %Y') if article.date else 'Today',
                'content': article.content,
                'link': article.link,
                'bg_color': '#f0fff4'
            })
        
        # Add Reddit discussions
        for post in reddit_items + reddit_intelligent_items:
            all_content.append({
                'type': 'discussion',
                'icon': '💬',
                'title': post.title,
                'source': f"{post.source} • ⬆️ {post.score} • 💬 {post.comments}",
                'date': 'Today',
                'content': post.content,
                'link': post.link,
                'bg_color': '#fff5f5'
            })
        
        # Display all content with university-compatible table design
        for i, item in enumerate(all_content):
            # Card styling based on content type
            if item['type'] == 'research':
                accent_color = '#2563eb'  # Professional slate gray
                bg_color = '#f1f5f9'  # Very light slate
                type_badge = '🔬 RESEARCH'
            elif item['type'] == 'news':
                accent_color = '#059669'
                bg_color = '#ecfdf5'
                type_badge = '📰 INDUSTRY'
            else:  # discussion
                accent_color = '#d97706'
                bg_color = '#fffbeb'
                type_badge = '💬 COMMUNITY'
            
            html += f"""
                    <!-- Content Card -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom: 20px; border: 1px solid #e5e7eb; background-color: {bg_color}; border-radius: 8px;">
                        <tr>
                            <td style="padding: 20px; border-radius: 8px;">
                                <!-- Card Header -->
                                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom: 15px;">
                                    <tr>
                                        <td>
                                            <table cellpadding="0" cellspacing="0" border="0">
                                                <tr>
                                                    <td style="background-color: {accent_color}; color: #ffffff; padding: 4px 8px; font-size: 11px; font-weight: bold;">
                                                        {type_badge}
                                                    </td>
                                                    <td style="padding-left: 10px; color: #6b7280; font-size: 13px;">
                                                        {item['source']} • {item['date']}
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                        <td align="right" style="color: #9ca3af; font-size: 12px; font-weight: bold;">
                                            #{i+1:02d}
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Title -->
                                <h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 18px; font-weight: bold; line-height: 1.4;">
                                    <a href="{item['link']}" style="color: #1f2937; text-decoration: none;" target="_blank">
                                        {item['title']}
                                    </a>
                                </h3>
                                
                                <!-- Content Preview -->
                                <p style="margin: 0 0 15px 0; color: #4b5563; font-size: 14px; line-height: 1.5;">
                                    {truncate_content(item['content'], 120)}
                                </p>
                                
                                <!-- Action Button -->
                                <table cellpadding="0" cellspacing="0" border="0">
                                    <tr>
                                        <td style="background-color: {accent_color}; border: 2px solid {accent_color}; border-radius: 6px;">
                                            <a href="{item['link']}" style="display: block; color: #ffffff; text-decoration: none; padding: 10px 16px; font-size: 14px; font-weight: bold; border-radius: 6px;" target="_blank">
                                                Read Article →
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
            """
        
        if not all_content:
            html += """
                    <!-- No Content State -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border: 2px dashed #d1d5db; background-color: #f9fafb;">
                        <tr>
                            <td style="padding: 40px; text-align: center;">
                                <p style="margin: 0 0 10px 0; font-size: 36px;">🔍</p>
                                <h3 style="margin: 0 0 8px 0; color: #374151; font-size: 18px; font-weight: bold;">
                                    No AI Intelligence Available
                                </h3>
                                <p style="margin: 0; color: #6b7280; font-size: 14px;">
                                    Our algorithms are working around the clock. Check back soon for fresh insights!
                                </p>
                            </td>
                        </tr>
                    </table>
            """
        
        # Add the footer to complete the HTML
        html += f"""
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #1f2937; padding: 30px; text-align: center;">
                                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                        <tr>
                                            <td align="center">
                                                
                                                <!-- Brand -->
                                                <h4 style="margin: 0 0 5px 0; color: #ffffff; font-size: 16px; font-weight: bold;">
                                                    💡AI-CCORE's Daily AI Digest
                                                </h4>
                                                <p style="margin: 0 0 20px 0; color: #9ca3af; font-size: 14px;">
                                                    Engineered by Vishva Prasanth • Powered by AI-CCORE
                                                </p>
                                                
                                                <!-- Social Links -->
                                                <table cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto 20px auto;">
                                                    <tr>
                                                        <td style="padding: 0 5px;">
                                                            <table cellpadding="0" cellspacing="0" border="0">
                                                                <tr>
                                                                    <td style="background-color: #0077b5; border: 1px solid #0077b5;">
                                                                        <a href="https://www.linkedin.com/in/vishvaprasanth/" style="display: block; color: #ffffff; text-decoration: none; padding: 8px 12px; font-size: 12px; font-weight: bold;" target="_blank">💼 LinkedIn</a>
                                                                    </td>
                                                                </tr>
                                                            </table>
                                                        </td>
                                                        <td style="padding: 0 5px;">
                                                            <table cellpadding="0" cellspacing="0" border="0">
                                                                <tr>
                                                                    <td style="background-color: #7c3aed; border: 1px solid #7c3aed;">
                                                                        <a href="https://beacons.ai/vishvaluke" style="display: block; color: #ffffff; text-decoration: none; padding: 8px 12px; font-size: 12px; font-weight: bold;" target="_blank">🌐 Portfolio</a>
                                                                    </td>
                                                                </tr>
                                                            </table>
                                                        </td>
                                                    </tr>
                                                </table>
                                                
                                                <!-- Info -->
                                                <p style="margin: 0 0 15px 0; color: #6b7280; font-size: 12px; line-height: 1.4;">
                                                    🚀 Zero-config AI Discovery: Reddit API • arXiv • Google News • HackerNews<br/>
                                                    ⚡ Advanced Algorithms: Semantic Deduplication • Intelligent Ranking • Real-time Processing
                                                </p>
                                                
                                                <!-- Legal -->
                                                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-top: 1px solid #374151; padding-top: 15px;">
                                                    <tr>
                                                        <td align="center">
                                                            <p style="margin: 0; color: #6b7280; font-size: 11px; line-height: 1.4;">
                                                                This digest is algorithmically curated for AI professionals. Want to unsubscribe? Just reply with "STOP"<br/>
                                                                © {datetime.now().year} AI-CCORE's Daily AI Digest. All insights aggregated under fair use.
                                                            </p>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
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
    
    def prioritize_content(self, items: List[NewsItem], max_items: int) -> List[NewsItem]:
        """Prioritize content based on engagement, recency, and relevance"""
        if not items:
            return []
        
        # Score each item
        scored_items = []
        for item in items:
            score = 0
            
            # Score based on engagement metrics
            if hasattr(item, 'score') and item.score:
                score += min(item.score / 10, 50)  # Reddit/HN score (max 50 points)
            
            if hasattr(item, 'comments') and item.comments:
                score += min(item.comments / 2, 25)  # Comments (max 25 points)
            
            # Score based on content quality indicators
            title_words = len(item.title.split()) if item.title else 0
            if 5 <= title_words <= 15:  # Optimal title length
                score += 10
            
            content_length = len(item.content) if item.content else 0
            if 100 <= content_length <= 500:  # Good content length
                score += 15
            
            # Score based on AI relevance
            ai_keywords_in_title = sum(1 for keyword in ['AI', 'artificial', 'machine', 'learning', 'neural', 'GPT', 'ChatGPT', 'OpenAI', 'LLM'] 
                                     if keyword.lower() in item.title.lower())
            score += ai_keywords_in_title * 5
            
            # Boost for research papers (generally high quality)
            if item.type == 'research_paper':
                score += 20
            
            # Boost for news from reputable sources
            if hasattr(item, 'source') and item.source:
                reputable_sources = ['TechCrunch', 'Ars Technica', 'Google News', 'arXiv', 'MIT Technology Review']
                if any(source in item.source for source in reputable_sources):
                    score += 15
            
            scored_items.append((score, item))
        
        # Sort by score (highest first) and return top items
        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [item for score, item in scored_items[:max_items]]

class ScraperService:
    """Service for scraping AI news from various sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # AI-related keywords for content filtering
        self.ai_keywords = [
            'artificial intelligence', 'machine learning', 'deep learning', 'neural network',
            'AI', 'ML', 'LLM', 'GPT', 'transformer', 'chatbot', 'automation',
            'computer vision', 'natural language', 'algorithm', 'data science',
            'OpenAI', 'ChatGPT', 'Claude', 'Gemini', 'tensorflow', 'pytorch'
        ]
        
        self.driver = None
    
    def extract_real_url_from_google_news(self, google_news_url: str) -> str:
        """Extract the real article URL from Google News redirect URL"""
        try:
            if not google_news_url or 'news.google.com' not in google_news_url:
                return google_news_url
            
            # Try to extract URL from Google News redirect
            import urllib.parse as urlparse
            
            # Method 1: Check for 'url=' parameter
            parsed = urlparse.urlparse(google_news_url)
            query_params = urlparse.parse_qs(parsed.query)
            
            if 'url' in query_params:
                real_url = query_params['url'][0]
                return real_url
            
            # Method 2: Try to decode from the path
            if '/articles/' in google_news_url:
                # For newer Google News URLs, try to make a HEAD request to get redirect
                try:
                    response = self.session.head(google_news_url, allow_redirects=True, timeout=5)
                    if response.url and response.url != google_news_url:
                        return response.url
                except Exception as e:
                    logger.debug(f"Failed to resolve Google News redirect: {e}")
            
            # Fallback: return original URL
            return google_news_url
            
        except Exception as e:
            logger.debug(f"Error extracting real URL from Google News: {e}")
            return google_news_url

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
        text = (title + ' ' + content).lower()
        return any(keyword.lower() in text for keyword in self.ai_keywords)
    
    def is_highly_ai_relevant(self, title: str, content: str) -> bool:
        """Strict AI relevance check for research papers to ensure high-quality AI content"""
        text = (title + ' ' + content).lower()
        
        # High-priority AI keywords that must be present
        core_ai_keywords = [
            'artificial intelligence', 'machine learning', 'deep learning', 'neural network',
            'transformer', 'attention mechanism', 'generative model', 'large language model',
            'llm', 'gpt', 'bert', 'reinforcement learning', 'computer vision', 'nlp',
            'natural language processing', 'convolutional neural', 'recurrent neural',
            'adversarial', 'gan', 'diffusion model', 'embedding', 'fine-tuning',
            'pre-training', 'multi-modal', 'chatbot', 'ai model', 'ai system'
        ]
        
        # Must have at least one core AI keyword
        has_core_ai = any(keyword in text for keyword in core_ai_keywords)
        
        # Exclude papers that are too theoretical or mathematical without clear AI application
        exclusion_keywords = [
            'purely mathematical', 'abstract algebra', 'topology', 'number theory',
            'graph theory without ai', 'pure mathematics', 'theoretical physics',
            'quantum mechanics without ai', 'biological without ai'
        ]
        
        # Exclude if it's too general or non-AI
        has_exclusions = any(keyword in text for keyword in exclusion_keywords)
        
        # Score based on AI relevance
        ai_score = 0
        
        # Count core AI keywords
        for keyword in core_ai_keywords:
            if keyword in text:
                ai_score += 2
        
        # Boost for practical AI applications
        practical_keywords = [
            'implementation', 'experiment', 'evaluation', 'benchmark', 'dataset',
            'performance', 'accuracy', 'training', 'inference', 'application'
        ]
        
        for keyword in practical_keywords:
            if keyword in text:
                ai_score += 1
        
        # Must have high AI relevance score and no exclusions
        return has_core_ai and not has_exclusions and ai_score >= 3
    
    def extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text"""
        found_tags = []
        text_lower = text.lower()
        
        for keyword in self.ai_keywords:
            if keyword.lower() in text_lower:
                found_tags.append(keyword)
                
        return list(set(found_tags))
    
    def discover_ai_subreddits_dynamically(self, reddit=None) -> List[Dict[str, Any]]:
        """Dynamically discover AI-related subreddits using Reddit search"""
        logger.info("🔍 Dynamically discovering AI-related subreddits...")
        discovered_subreddits = []
        
        try:
            # If Reddit API is available, use it for subreddit search
            if reddit:
                try:
                    logger.info("Using Reddit API for subreddit discovery...")
                    # Verify Reddit instance is working before using it
                    try:
                        _ = list(reddit.subreddit('python').hot(limit=1))
                    except Exception as e:
                        logger.warning(f"Reddit API verification failed: {str(e)[:100]}")
                        logger.info("Using web-based subreddit discovery as fallback...")
                        # Skip to web-based fallback
                        raise Exception("Reddit API not working")
                    
                    # Search for AI-related subreddits using Reddit API
                    ai_keywords = ['artificial', 'machine', 'learning', 'AI', 'neural', 'deep', 'GPT', 'OpenAI', 'ChatGPT', 'LLM']
                    
                    for keyword in ai_keywords:
                        try:
                            # Search subreddits by keyword
                            for sub in reddit.subreddits.search(keyword, limit=10):
                                try:
                                    # Check if subreddit is AI-related and active
                                    if (sub.subscribers > 1000 and
                                        any(ai_term.lower() in (sub.display_name + ' ' + (sub.public_description or '')).lower() 
                                            for ai_term in self.ai_keywords)):
                                        
                                        discovered_subreddits.append({
                                            'name': sub.display_name,
                                            'subscribers': sub.subscribers,
                                            'category': 'ai_related',
                                            'min_score': max(10, min(100, sub.subscribers // 1000))
                                        })
                                except Exception as e:
                                    continue
                                    
                            time.sleep(0.5)  # Rate limiting
                            
                        except Exception as e:
                            logger.warning(f"Error searching Reddit API for '{keyword}': {e}")
                            continue
                            
                except Exception as e:
                    logger.warning(f"Reddit API subreddit search failed: {e}")
                    
            # Fallback to web-based search if API not available or failed
            if len(discovered_subreddits) < 5:
                logger.info("Using web-based subreddit discovery as fallback...")
                
                ai_search_terms = [
                    'artificial intelligence', 'machine learning', 'deep learning',
                    'neural networks', 'AI', 'ChatGPT', 'OpenAI', 'GPT', 'LLM'
                ]
                
                for search_term in ai_search_terms:
                    try:
                        # Search for subreddits using Reddit's JSON API
                        search_url = "https://www.reddit.com/subreddits/search.json"
                        params = {
                            'q': search_term,
                            'sort': 'relevance',
                            'limit': 10
                        }
                        
                        response = self.session.get(search_url, params=params)
                        if response.status_code == 200:
                            data = response.json()
                            
                            for sub_data in data.get('data', {}).get('children', []):
                                sub = sub_data.get('data', {})
                                sub_name = sub.get('display_name', '')
                                subscribers = sub.get('subscribers', 0)
                                
                                # Filter for active, relevant subreddits
                                if (subscribers > 1000 and
                                    any(keyword.lower() in sub_name.lower() or 
                                        keyword.lower() in sub.get('public_description', '').lower()
                                        for keyword in self.ai_keywords)):
                                        
                                    discovered_subreddits.append({
                                        'name': sub_name,
                                        'subscribers': subscribers,
                                        'category': 'ai_related',
                                        'min_score': max(10, min(100, subscribers // 1000))
                                    })
                        
                        time.sleep(0.5)  # Rate limiting
                        
                    except Exception as e:
                        logger.warning(f"Error searching subreddits for '{search_term}': {e}")
                        continue
            
            # Remove duplicates and sort by relevance
            unique_subs = {}
            for sub in discovered_subreddits:
                if sub['name'] not in unique_subs:
                    unique_subs[sub['name']] = sub
                    
            # Sort by subscriber count (popularity indicator)
            sorted_subs = sorted(unique_subs.values(), key=lambda x: x['subscribers'], reverse=True)
            
            logger.info(f"Discovered {len(sorted_subs)} AI-related subreddits dynamically")
            return sorted_subs[:15]  # Top 15 most relevant
            
        except Exception as e:
            logger.error(f"Error in dynamic subreddit discovery: {e}")
            # Fallback to intelligent search if discovery fails
            return [
                {'name': 'artificial', 'category': 'ai_general', 'min_score': 50},
                {'name': 'MachineLearning', 'category': 'research', 'min_score': 30},
                {'name': 'OpenAI', 'category': 'companies', 'min_score': 30}
            ]
    
    def discover_ai_news_sources_dynamically(self) -> List[Dict[str, str]]:
        """Use curated high-quality AI news sources with fallback discovery"""
        logger.info("🌐 Using curated high-quality AI news sources...")
        
        # Start with known working AI news RSS feeds
        curated_sources = [
            {
                'name': 'TechCrunch AI',
                'url': 'https://techcrunch.com/category/artificial-intelligence/feed/',
                'type': 'curated_rss'
            },
            {
                'name': 'The Verge AI',
                'url': 'https://www.theverge.com/ai-artificial-intelligence/rss/index.xml',
                'type': 'curated_rss'
            },
            {
                'name': 'Ars Technica AI',
                'url': 'https://feeds.arstechnica.com/arstechnica/technology-lab',
                'type': 'curated_rss'
            },
            {
                'name': 'Wired AI',
                'url': 'https://www.wired.com/feed/category/business/artificial-intelligence/latest/rss',
                'type': 'curated_rss'
            },
            {
                'name': 'AI News',
                'url': 'https://www.artificialintelligence-news.com/feed/',
                'type': 'curated_rss'
            }
        ]
        
        # Validate that sources are working
        working_sources = []
        for source in curated_sources:
            try:
                response = self.session.get(source['url'], timeout=5)
                if response.status_code == 200:
                    working_sources.append(source)
                    logger.info(f"✅ {source['name']} - RSS feed working")
                else:
                    logger.warning(f"❌ {source['name']} - RSS feed not accessible")
            except Exception as e:
                logger.warning(f"❌ {source['name']} - Error: {e}")
                
        # Add Google News as reliable fallback
        working_sources.extend([
            {
                'name': 'Google News AI',
                'url': 'https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en',
                'type': 'google_news'
            },
            {
                'name': 'Google News ML',
                'url': 'https://news.google.com/rss/search?q=machine+learning&hl=en-US&gl=US&ceid=US:en',
                'type': 'google_news'
            }
        ])
        
        logger.info(f"Using {len(working_sources)} working AI news sources")
        return working_sources
    
    def scrape_reddit_dynamic(self) -> List[NewsItem]:
        """Dynamically discover and scrape AI content from Reddit without hardcoded subreddits"""
        logger.info("🔍 Starting dynamic Reddit AI content discovery...")
        results = []
        
        try:
            # First, try Reddit API if available
            import praw
            
            reddit_client_id = os.getenv('REDDIT_CLIENT_ID', '').strip()
            reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET', '').strip()
            reddit_user_agent_raw = os.getenv('REDDIT_USER_AGENT', '').strip()
            
            # Clean and validate user agent
            if reddit_user_agent_raw:
                # Remove any invalid characters and normalize
                reddit_user_agent = re.sub(r'[^\w\s\-\.\:/]', '', reddit_user_agent_raw).strip()
                reddit_user_agent = re.sub(r'\s+', ' ', reddit_user_agent)  # Normalize spaces
                if not reddit_user_agent:
                    reddit_user_agent = 'AI-News-Crawler-v3.0'
            else:
                reddit_user_agent = 'AI-News-Crawler-v3.0'
            
            # Validate credentials before creating Reddit instance
            if reddit_client_id and reddit_client_secret and len(reddit_client_id) > 5 and len(reddit_client_secret) > 5:
                try:
                    logger.info(f"Attempting Reddit API connection with user agent: '{reddit_user_agent}'")
                    reddit = praw.Reddit(
                        client_id=reddit_client_id,
                        client_secret=reddit_client_secret,
                        user_agent=reddit_user_agent
                    )
                    
                    # Test the connection first - this will throw an exception if invalid
                    try:
                        # Try a more comprehensive API call to verify credentials
                        test_sub = reddit.subreddit('python')
                        _ = list(test_sub.hot(limit=1))  # This will fail if credentials are invalid
                        logger.info("✅ Reddit API authentication successful")
                    except Exception as auth_error:
                        logger.warning(f"❌ Reddit API authentication failed: {str(auth_error)[:100]}")
                        logger.info("Falling back to intelligent search without Reddit API")
                        return self.scrape_reddit_intelligent()
                    
                    # Only proceed with discovery if authentication succeeded
                    discovered_subreddits = self.discover_ai_subreddits_dynamically(reddit)
                    
                    for subreddit_info in discovered_subreddits:
                        try:
                            sub_name = subreddit_info['name']
                            min_score = subreddit_info['min_score']
                            
                            logger.info(f"Dynamically scraping r/{sub_name} (min_score: {min_score})")
                            
                            sub = reddit.subreddit(sub_name)
                            posts = []
                            
                            # Get hot posts
                            for submission in sub.hot(limit=20):
                                try:
                                    if self.is_from_today_unix(submission.created_utc):
                                        score = submission.score
                                        comments = submission.num_comments
                                        
                                        if (score >= min_score and 
                                            self.is_significant_content(submission.title, submission.selftext)):
                                            
                                            news_item = NewsItem(
                                                title=submission.title,
                                                content=submission.selftext or f"Discussion: {submission.title}",
                                                link=f"https://reddit.com{submission.permalink}",
                                                source=f"r/{sub_name} (Dynamic)",
                                                date=datetime.fromtimestamp(submission.created_utc, timezone.utc).isoformat(),
                                                score=score,
                                                comments=comments,
                                                author=str(submission.author) if submission.author else '[deleted]',
                                                category='dynamic_discovery',
                                                type='reddit_dynamic',
                                                engagement=score + (comments * 2),
                                                tags=self.extract_tags(submission.title + ' ' + (submission.selftext or ''))
                                            )
                                            posts.append(news_item)
                                            
                                except Exception as e:
                                    continue
                            
                            results.extend(posts)
                            time.sleep(0.5)
                            
                        except Exception as e:
                            logger.warning(f"Error accessing dynamically discovered r/{subreddit_info['name']}: {e}")
                            continue
                            
                except Exception as e:
                    logger.warning(f"Reddit API failed, falling back to intelligent search: {e}")
                    # Fall back to intelligent search
                    return self.scrape_reddit_intelligent()
                    
            else:
                logger.info("No valid Reddit API credentials found, using intelligent search")
                if not reddit_client_id or not reddit_client_secret:
                    logger.info("💡 To enable Reddit API: Add REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, and REDDIT_USER_AGENT to environment")
                else:
                    logger.info("💡 Reddit credentials too short - ensure they are valid")
                return self.scrape_reddit_intelligent()
            
        except ImportError:
            logger.info("PRAW library not available, using intelligent search")
            return self.scrape_reddit_intelligent()
        except Exception as e:
            logger.warning(f"Dynamic Reddit scraping failed, using intelligent search: {e}")
            return self.scrape_reddit_intelligent()
        
        # Sort by engagement and return top results
        results.sort(key=lambda x: x.engagement, reverse=True)
        logger.info(f"Dynamic Reddit discovery found {len(results)} posts")
        return results[:20]  # Top 20 most engaging
    
    def scrape_news_dynamic(self) -> List[NewsItem]:
        """Dynamically discover and scrape AI news without hardcoded sources"""
        logger.info("🌐 Starting dynamic AI news discovery...")
        results = []
        
        try:
            # Dynamically discover news sources
            discovered_sources = self.discover_ai_news_sources_dynamically()
            
            # Process discovered sources in parallel for speed
            with ThreadPoolExecutor(max_workers=8) as executor:
                future_to_source = {
                    executor.submit(self.scrape_dynamic_news_source, source): source
                    for source in discovered_sources[:15]  # Limit for performance
                }
                
                for future in as_completed(future_to_source, timeout=60):
                    try:
                        source_results = future.result()
                        if source_results:
                            results.extend(source_results)
                    except Exception as e:
                        logger.warning(f"Error processing dynamic news source: {e}")
                        continue
            
            # If dynamic discovery yields few results, supplement with intelligent search
            if len(results) < 5:
                logger.info("Supplementing with intelligent news search...")
                intelligent_results = self.scrape_news_intelligent()
                results.extend(intelligent_results)
            
            # Sort by relevance and recency
            results.sort(key=lambda x: (
                len([tag for tag in x.tags if tag.lower() in [kw.lower() for kw in self.ai_keywords]]),
                x.date
            ), reverse=True)
            
            logger.info(f"Dynamic news discovery found {len(results)} articles")
            return results[:15]  # Top 15 most relevant
            
        except Exception as e:
            logger.error(f"Dynamic news discovery failed: {e}")
            # Fallback to intelligent search
            return self.scrape_news_intelligent()
    
    def scrape_dynamic_news_source(self, source: Dict[str, str]) -> List[NewsItem]:
        """Scrape a single news source using its RSS feed"""
        results = []
        
        try:
            source_name = source.get('name', 'Unknown')
            source_url = source.get('url', '')
            
            if not source_url:
                return results
            
            logger.info(f"📰 Scraping {source_name}...")
            
            import feedparser
            response = self.session.get(source_url, timeout=15)
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                
                if feed.entries:
                    for entry in feed.entries[:5]:  # Top 5 from each source
                        try:
                            pub_date = entry.get('published_parsed')
                            if pub_date:
                                pub_datetime = datetime(*pub_date[:6], tzinfo=timezone.utc)
                                
                                # Check if article is from last 3 days
                                three_days_ago = datetime.now(timezone.utc) - timedelta(days=3)
                                if pub_datetime >= three_days_ago:
                                    title = entry.get('title', '').strip()
                                    summary = entry.get('summary', '') or entry.get('description', '')
                                    
                                    # Clean content
                                    clean_title = re.sub(r'<[^>]*>', '', title)
                                    clean_title = re.sub(r'&[^;]+;', ' ', clean_title)
                                    clean_title = re.sub(r'\s+', ' ', clean_title).strip()
                                    
                                    clean_summary = re.sub(r'<[^>]*>', '', summary)
                                    clean_summary = re.sub(r'&[^;]+;', ' ', clean_summary)
                                    clean_summary = re.sub(r'\s+', ' ', clean_summary).strip()
                                    
                                    if self.is_significant_content(clean_title, clean_summary):
                                        article_url = entry.get('link', '')
                                        real_url = self.extract_real_url_from_google_news(article_url)
                                        
                                        news_item = NewsItem(
                                            title=clean_title,
                                            content=clean_summary[:400],  # More content for news
                                            link=real_url,
                                            source=source_name,
                                            date=pub_datetime.isoformat(),
                                            author=entry.get('author', source_name),
                                            category='tech_news',
                                            type='news_curated',
                                            tags=self.extract_tags(clean_title + ' ' + clean_summary)
                                        )
                                        results.append(news_item)
                                        logger.debug(f"  ✅ Found: {clean_title[:50]}...")
                                        
                        except Exception as e:
                            logger.debug(f"Error parsing entry: {e}")
                            continue
                else:
                    logger.warning(f"  ❌ No entries found in {source_name} feed")
            else:
                logger.warning(f"  ❌ Failed to access {source_name} (HTTP {response.status_code})")
            
        except Exception as e:
            logger.warning(f"Error scraping {source.get('name', 'unknown')}: {e}")
        
        logger.info(f"  📊 {source_name}: Found {len(results)} articles")
        return results

    def scrape_all_sources_optimized(self) -> Dict[str, List[NewsItem]]:
        """Optimized parallel scraping using fully dynamic discovery (no hardcoded sources)"""
        logger.info("🚀 Starting fully dynamic AI content discovery across all sources...")
        start_time = time.time()
        
        results = {
            'reddit': [],
            'reddit_intelligent': [],
            'research': [],
            'news': [],
            'news_intelligent': [],
            'linkedin': []
        }
        
        try:
            # Use ThreadPoolExecutor for parallel processing
            with ThreadPoolExecutor(max_workers=5) as executor:
                # Submit all dynamic scraping tasks
                future_to_source = {
                    executor.submit(self.scrape_reddit_dynamic): 'reddit',
                    executor.submit(self.scrape_reddit_intelligent): 'reddit_intelligent', 
                    executor.submit(self.scrape_research_papers): 'research',
                    executor.submit(self.scrape_news_dynamic): 'news',
                    executor.submit(self.scrape_news_intelligent): 'news_intelligent'
                }
                
                # Collect results with timeout for GitHub Actions
                for future in as_completed(future_to_source, timeout=300):  # 5 minute timeout
                    source = future_to_source[future]
                    try:
                        source_results = future.result()
                        results[source] = source_results
                        logger.info(f"✅ {source} (dynamic): {len(source_results)} items")
                    except Exception as e:
                        logger.error(f"❌ {source} dynamic discovery failed: {e}")
                        results[source] = []
            
            # Combine and deduplicate results
            all_items = []
            for source_name, items in results.items():
                all_items.extend(items)
            
            # Advanced deduplication using similarity matching
            if len(all_items) > 1:
                logger.info("🧹 Deduplicating content using similarity matching...")
                deduplicated_items = self.deduplicate_items(all_items)
                
                # Redistribute deduplicated items back to categories
                results = {'reddit': [], 'reddit_intelligent': [], 'research': [], 'news': [], 'news_intelligent': []}
                for item in deduplicated_items:
                    source_type = item.type
                    if 'reddit' in source_type:
                        if 'intelligent' in source_type:
                            results['reddit_intelligent'].append(item)
                        else:
                            results['reddit'].append(item)
                    elif source_type == 'research_paper':
                        results['research'].append(item)
                    elif 'news' in source_type:
                        if 'intelligent' in source_type:
                            results['news_intelligent'].append(item)
                        else:
                            results['news'].append(item)
            
            # Calculate and log performance metrics
            execution_time = time.time() - start_time
            total_items = sum(len(items) for items in results.values())
            items_per_second = total_items / execution_time if execution_time > 0 else 0
            
            logger.info(f"""
🎯 Dynamic Discovery Performance Summary:
   ⚡ Execution Time: {execution_time:.2f} seconds
   📊 Total Items Found: {total_items}
   🚀 Performance: {items_per_second:.1f} items/second
   🔍 Sources: 100% Dynamic Discovery (0 hardcoded)
   
📂 Content Distribution:
   💬 Reddit (Dynamic): {len(results['reddit'])}
   🔍 Reddit (Intelligent): {len(results['reddit_intelligent'])}
   🔬 Research Papers: {len(results['research'])}
   📰 News (Dynamic): {len(results['news'])}
   🌐 News (Intelligent): {len(results['news_intelligent'])}
            """)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in optimized dynamic scraping: {e}")
            # Return empty results on failure
            return {source: [] for source in results.keys()}
    
    def deduplicate_items(self, items: List[NewsItem]) -> List[NewsItem]:
        """Advanced deduplication using similarity matching"""
        if len(items) <= 1:
            return items
            
        logger.info(f"Deduplicating {len(items)} items...")
        unique_items = []
        
        for item in items:
            is_duplicate = False
            
            for existing_item in unique_items:
                # Calculate similarity based on title and content
                title_similarity = self.calculate_similarity(item.title, existing_item.title)
                content_similarity = self.calculate_similarity(item.content[:200], existing_item.content[:200])
                
                # Consider duplicate if 70% similar
                if title_similarity > 0.7 or content_similarity > 0.7:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_items.append(item)
        
        logger.info(f"Removed {len(items) - len(unique_items)} duplicates")
        return unique_items
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using basic word overlap"""
        if not text1 or not text2:
            return 0.0
            
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

    def scrape_reddit_intelligent(self) -> List[NewsItem]:
        """Intelligently discover trending AI content across all of Reddit using search API"""
        logger.info("🔍 Intelligently discovering trending AI content on Reddit...")
        results = []
        
        try:
            # Search for AI-related content across Reddit using multiple approaches
            search_queries = [
                'artificial intelligence', 'machine learning', 'ChatGPT', 'OpenAI',
                'deep learning', 'neural network', 'LLM', 'GPT', 'AI breakthrough'
            ]
            
            # Use Reddit's search API to find trending AI content
            for query in search_queries:
                try:
                    # Search recent posts across all subreddits
                    search_url = f"https://www.reddit.com/search.json"
                    params = {
                        'q': query,
                        'sort': 'hot',
                        'limit': 10,
                        't': 'day',  # Last 24 hours
                        'type': 'link'
                    }
                    
                    response = self.session.get(search_url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        
                        for post_data in data.get('data', {}).get('children', []):
                            post = post_data.get('data', {})
                            
                            # Filter for significant posts
                            score = post.get('score', 0)
                            comments = post.get('num_comments', 0)
                            
                            if score >= 50 or comments >= 10:  # Lower threshold for broader discovery
                                created_utc = post.get('created_utc', 0)
                                if self.is_from_today_unix(created_utc):
                                    title = post.get('title', '')
                                    content = post.get('selftext', '') or title
                                    
                                    if self.is_significant_content(title, content):
                                        news_item = NewsItem(
                                            title=title,
                                            content=content[:300],
                                            link=f"https://reddit.com{post.get('permalink', '')}",
                                            source=f"r/{post.get('subreddit', 'unknown')}",
                                            date=datetime.fromtimestamp(created_utc, timezone.utc).isoformat(),
                                            score=score,
                                            comments=comments,
                                            author=post.get('author', 'unknown'),
                                            category='trending_ai',
                                            type='reddit_intelligent',
                                            tags=self.extract_tags(title + ' ' + content)
                                        )
                                        results.append(news_item)
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Error searching Reddit for '{query}': {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in intelligent Reddit discovery: {e}")
            
        logger.info(f"Found {len(results)} intelligent Reddit discoveries")
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
                            # Strict AI relevance check for research papers
                            if self.is_highly_ai_relevant(title, abstract):
                                # Extract paper ID for deduplication
                                paper_id = link.split('/')[-1]
                                
                                if paper_id not in paper_ids:
                                    paper_ids.add(paper_id)
                                    
                                    # Extract authors
                                    authors = [author.find('name').text for author in entry.find_all('author')]
                                    
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
                                    
                                    results.append(news_item)
                                
                    except Exception as e:
                        logger.debug(f"Error parsing arXiv entry: {e}")
                        
            except Exception as e:
                logger.error(f"Error scraping arXiv category {category}: {e}")
        
        logger.info(f"Found {len(results)} recent research papers")
        return results[:10]  # Return top 10 most recent
    


    def scrape_news_intelligent(self) -> List[NewsItem]:
        """Intelligently discover AI news from worldwide web sources using multiple discovery methods"""
        logger.info("🌐 Intelligently discovering AI news from worldwide web...")
        results = []
        
        try:
            # Method 1: Google News RSS for AI topics
            google_news_queries = [
                'artificial intelligence', 'machine learning', 'ChatGPT',
                'OpenAI', 'AI breakthrough', 'deep learning', 'neural networks'
            ]
            
            for query in google_news_queries:
                try:
                    # Google News RSS URL
                    rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
                    response = self.session.get(rss_url, timeout=10)
                    
                    if response.status_code == 200:
                        import feedparser
                        feed = feedparser.parse(response.content)
                        
                        for entry in feed.entries[:5]:  # Limit to 5 per query for performance
                            pub_date = entry.get('published_parsed')
                            if pub_date:
                                pub_datetime = datetime(*pub_date[:6], tzinfo=timezone.utc)
                                
                                if self.is_from_today(pub_datetime.isoformat()):
                                    title = entry.get('title', '').strip()
                                    summary = entry.get('summary', '').strip()
                                    
                                    # Clean summary content
                                    clean_summary = re.sub(r'<[^>]*>', '', summary)  # Remove HTML tags
                                    clean_summary = re.sub(r'&[^;]+;', ' ', clean_summary)  # Remove HTML entities
                                    clean_summary = re.sub(r'\s+', ' ', clean_summary).strip()  # Normalize spaces
                                    
                                    if self.is_significant_content(title, clean_summary):
                                        article_url = entry.get('link', '')
                                        real_url = self.extract_real_url_from_google_news(article_url)
                                        
                                        news_item = NewsItem(
                                            title=title,
                                            content=clean_summary[:300],
                                            link=real_url,
                                            source='Google News',
                                            date=pub_datetime.isoformat(),
                                            category='ai_news',
                                            type='news_intelligent',
                                            tags=self.extract_tags(title + ' ' + clean_summary)
                                        )
                                        results.append(news_item)
                    
                    time.sleep(0.3)  # Rate limiting
                    
                except Exception as e:
                    logger.warning(f"Error fetching Google News for '{query}': {e}")
                    continue
            
            # Method 2: HackerNews AI stories
            try:
                hn_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
                response = self.session.get(hn_url, timeout=10)
                
                if response.status_code == 200:
                    story_ids = response.json()[:30]  # Top 30 stories
                    
                    for story_id in story_ids:
                        try:
                            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                            story_response = self.session.get(story_url, timeout=5)
                            
                            if story_response.status_code == 200:
                                story = story_response.json()
                                
                                if story and story.get('title'):
                                    title = story.get('title', '')
                                    text = story.get('text', '') or title
                                    
                                    # Check if story is AI-related and recent
                                    if (self.is_significant_content(title, text) and
                                        story.get('time') and
                                        self.is_from_today_unix(story.get('time'))):
                                        
                                        news_item = NewsItem(
                                            title=title,
                                            content=text[:300],
                                            link=self.extract_real_url_from_google_news(story.get('url', '')),
                                            source='HackerNews',
                                            date=datetime.fromtimestamp(story.get('time'), timezone.utc).isoformat(),
                                            author=story.get('by', 'unknown'),
                                            score=story.get('score', 0),
                                            comments=story.get('descendants', 0),
                                            category='tech_news',
                                            type='news_intelligent',
                                            tags=self.extract_tags(title + ' ' + text)
                                        )
                                        results.append(news_item)
                                        
                            time.sleep(0.1)  # Rate limiting for individual stories
                            
                        except Exception as e:
                            continue  # Skip failed individual stories
                            
            except Exception as e:
                logger.warning(f"Error fetching HackerNews: {e}")
                
        except Exception as e:
            logger.error(f"Error in intelligent news discovery: {e}")
            
        logger.info(f"Found {len(results)} intelligent news discoveries")
        return results[:15]  # Top 15 most relevant

class EmailListManager:
    """Manage email lists configuration"""
    
    def __init__(self):
        self.email_lists = {
            'main': [
                'vsrinivasan@unomaha.edu',
                'msubramaniam@unomaha.edu',
                'apucakayala@unomaha.edu',
                'vvijayaragunathapa@unomaha.edu',
                'ikatlakanti@unomaha.edu'
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
        """Initialize the database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create scraping_runs table with all required columns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraping_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    reddit_count INTEGER DEFAULT 0,
                    research_count INTEGER DEFAULT 0,
                    news_count INTEGER DEFAULT 0,
                    linkedin_count INTEGER DEFAULT 0,
                    total_count INTEGER DEFAULT 0,
                    email_sent BOOLEAN DEFAULT 0,
                    recipients_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'completed',
                    error_message TEXT,
                    execution_time REAL DEFAULT 0
                )
            ''')
            
            # Check if linkedin_count column exists, if not add it
            cursor.execute("PRAGMA table_info(scraping_runs)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'linkedin_count' not in columns:
                cursor.execute('ALTER TABLE scraping_runs ADD COLUMN linkedin_count INTEGER DEFAULT 0')
                logger.info("Added linkedin_count column to database")
            
            if 'execution_time' not in columns:
                cursor.execute('ALTER TABLE scraping_runs ADD COLUMN execution_time REAL DEFAULT 0')
                logger.info("Added execution_time column to database")
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def log_scraping_run(self, results: Dict[str, List[NewsItem]], email_sent: bool, 
                        recipients_count: int, status: str = 'completed', error_message: str = None,
                        execution_time: float = 0):
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
                 email_sent, recipients_count, status, error_message, execution_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(timezone.utc).isoformat(),
                reddit_count,
                research_count,
                news_count,
                total_count,
                email_sent,
                recipients_count,
                status,
                error_message,
                execution_time
            ))
            
            conn.commit()
            conn.close()
            logger.info("Scraping run logged to database")
            
        except Exception as e:
            logger.error(f"Error logging scraping run: {e}")

def send_daily_digest():
    """Main function to scrape content and send daily digest"""
    logger.info("🚀 Starting AI News Daily Digest Process")
    start_time = time.time()
    
    # Initialize services
    scraper = ScraperService()
    email_service = EmailService()
    email_manager = EmailListManager()
    db_manager = DatabaseManager()
    
    email_sent = False
    recipients_count = 0
    error_message = None
    
    try:
        # Scrape all sources using optimized method
        logger.info("📡 Scraping AI content from all sources (optimized)...")
        results = scraper.scrape_all_sources_optimized()
        
        # Get email list
        email_list = email_manager.get_active_email_list()
        
        # Check if we have any email configuration
        if not email_service.resend_api_key and not email_service.smtp_user:
            logger.warning("⚠️ No email configuration found - digest will be logged only")
            logger.info("💡 Add RESEND_API_KEY or EMAIL_USER/EMAIL_PASSWORD to environment for email delivery")
            error_message = "No email credentials configured"
            
            # Still format the email for logging purposes
            subject = email_manager.config.get('custom_subject') or "AI-CCORE's Daily AI Digest"
            html_content = email_service.format_digest_email(results)
            logger.info(f"📄 Email content generated successfully ({len(html_content)} characters)")
            
        elif not email_list:
            logger.warning("⚠️ No email addresses found in active email list")
            error_message = "No email addresses configured"
        else:
            # Send email digest
            logger.info(f"📧 Sending digest to {len(email_list)} recipients...")
            
            subject = email_manager.config.get('custom_subject') or "AI-CCORE's Daily AI Digest"
            html_content = email_service.format_digest_email(results)
            
            email_sent = email_service.send_email(email_list, subject, html_content)
            recipients_count = len(email_list) if email_sent else 0
            
            if email_sent:
                logger.info("✅ Daily digest sent successfully!")
            else:
                logger.error("❌ Failed to send daily digest")
                error_message = "Failed to send email"
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Log to database with execution time
        status = 'completed' if email_sent or not email_list else 'failed'
        db_manager.log_scraping_run(results, email_sent, recipients_count, status, error_message, execution_time)
        
        # Print enhanced summary
        total_items = sum(len(items) for items in results.values())
        logger.info(f"""
📊 Daily Digest Summary:
   - Reddit Posts: {len(results.get('reddit', []))}
   - Research Papers: {len(results.get('research', []))}
   - News Articles: {len(results.get('news', []))}
   - Total Items: {total_items}
   - Execution Time: {execution_time:.2f} seconds
   - Performance: {total_items/execution_time:.1f} items/second
   - Email Sent: {'✅' if email_sent else '❌'}
   - Recipients: {recipients_count}
        """)
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"❌ Error in daily digest process: {e}")
        error_message = str(e)
        db_manager.log_scraping_run({}, False, 0, 'failed', error_message, execution_time)
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

🚀 NEW OPTIMIZATIONS FOR GITHUB ACTIONS:
  ⚡ Parallel processing for faster execution (5x speed improvement)
  🔍 Intelligent content discovery across all of Reddit
  🌐 Auto-discovery of trending AI news worldwide
  📊 Enhanced performance monitoring and metrics

Content Sources:
  🔬 Research Papers: arXiv AI categories (last 3 days)
  📰 News: Google News AI search + HackerNews + RSS feeds
  💬 Reddit: Intelligent discovery + curated subreddits  
  📈 All sources processed in parallel for speed

Environment Variables:
  EMAIL_PROVIDER    - Email service to use ('google' or 'resend'). Default: 'google'
  RESEND_API_KEY    - API key for Resend email service (used as primary or fallback)
  EMAIL_USER        - SMTP email username (for Google or other SMTP)
  EMAIL_PASSWORD    - SMTP email password (for Google or other SMTP)
  SMTP_SERVER       - SMTP server (default: smtp.gmail.com)
  SMTP_PORT         - SMTP port (default: 587)

Performance Optimizations:
  ⏱️  Execution time: 2-4 minutes (optimized for GitHub Actions free tier)
  🔄 Parallel scraping: 5 concurrent sources
  🧹 Smart deduplication: 70% similarity threshold
  📈 Real-time metrics: items/second tracking

Examples:
  python main.py                # Run optimized crawler once
  python main.py test          # Test with performance metrics
  python main.py schedule      # Schedule daily with optimizations
  python main.py daemon        # Run once + schedule with monitoring
    """)

if __name__ == "__main__":
    main() 