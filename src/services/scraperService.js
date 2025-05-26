const puppeteer = require('puppeteer');
const cheerio = require('cheerio');
const axios = require('axios');
const Parser = require('rss-parser');

class ScraperService {
  constructor() {
    this.browser = null;
    this.parser = new Parser();
  }

  async initialize() {
    try {
      if (!this.browser) {
        console.log('Initializing browser...');
        this.browser = await puppeteer.launch({
          headless: 'new',
          args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        console.log('Browser initialized successfully');
      }
    } catch (error) {
      console.error('Browser initialization error:', error);
      throw error;
    }
  }

  async close() {
    if (this.browser) {
      console.log('Closing browser...');
      await this.browser.close();
      this.browser = null;
      console.log('Browser closed successfully');
    }
  }

  isFromToday(dateString) {
    try {
      const contentDate = new Date(dateString);
      const now = new Date();
      const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      
      // Check if content is from the last 24 hours
      return contentDate >= yesterday && contentDate <= now;
    } catch (error) {
      console.error('Error parsing date:', dateString, error);
      return false;
    }
  }

  isFromTodayUnix(unixTimestamp) {
    try {
      const contentDate = new Date(unixTimestamp * 1000);
      const now = new Date();
      const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      
      return contentDate >= yesterday && contentDate <= now;
    } catch (error) {
      console.error('Error parsing unix timestamp:', unixTimestamp, error);
      return false;
    }
  }

  isSignificantContent(title, content) {
    const significantKeywords = [
      'breakthrough', 'advancement', 'new model', 'state of the art', 'sota',
      'significant', 'revolutionary', 'groundbreaking', 'major', 'important',
      'release', 'announcement', 'launch', 'update', 'improvement',
      'outperforms', 'better than', 'surpasses', 'achieves', 'milestone'
    ];

    const text = (title + ' ' + content).toLowerCase();
    return significantKeywords.some(keyword => text.includes(keyword.toLowerCase()));
  }

  async scrapeReddit() {
    console.log('Starting Reddit scraping...');
    const results = [];
    const subreddits = [
      { name: 'artificial', category: 'general', minScore: 100 },
      { name: 'MachineLearning', category: 'research', minScore: 50 },
      { name: 'AIdev', category: 'development', minScore: 30 },
      { name: 'OpenAI', category: 'companies', minScore: 50 },
      { name: 'deeplearning', category: 'research', minScore: 50 },
      { name: 'artificial_intelligence', category: 'general', minScore: 100 },
      { name: 'AIethics', category: 'ethics', minScore: 50 },
      { name: 'AGI', category: 'research', minScore: 30 },
      { name: 'ChatGPT', category: 'applications', minScore: 100 },
      { name: 'StableDiffusion', category: 'applications', minScore: 50 },
      { name: 'LocalLLaMA', category: 'development', minScore: 30 }
    ];

    for (const subreddit of subreddits) {
      try {
        console.log(`Scraping r/${subreddit.name}...`);
        const response = await axios.get(`https://www.reddit.com/r/${subreddit.name}/hot.json`, {
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
          }
        });

        if (response.data.data.children) {
          const posts = response.data.data.children
            .map(post => {
              const data = post.data;
              return {
                title: data.title,
                content: data.selftext,
                link: `https://reddit.com${data.permalink}`,
                source: `Reddit - r/${subreddit.name}`,
                date: new Date(data.created_utc * 1000).toISOString(),
                score: data.score,
                comments: data.num_comments,
                author: data.author,
                subreddit: subreddit.name,
                category: subreddit.category,
                type: 'reddit_post',
                engagement: data.score + (data.num_comments * 2),
                is_trending: data.score > subreddit.minScore || data.num_comments > 50,
                tags: this.extractTags(data.title + ' ' + data.selftext),
                created_utc: data.created_utc
              };
            })
            .filter(post => 
              this.isFromTodayUnix(post.created_utc) &&
              post.is_trending && 
              this.isSignificantContent(post.title, post.content)
            );

          results.push(...posts);
          console.log(`Found ${posts.length} significant posts from today in r/${subreddit.name}`);
        }
      } catch (error) {
        console.error(`Error scraping r/${subreddit.name}:`, error.message);
      }
    }

    return results
      .sort((a, b) => b.engagement - a.engagement)
      .slice(0, 15);
  }

  async scrapeResearchPapers() {
    console.log('Starting research paper scraping...');
    try {
      const categories = [
        'cs.AI',    // Artificial Intelligence
        'cs.LG',    // Machine Learning
        'cs.CL',    // Computation and Language
        'cs.CV',    // Computer Vision
        'cs.RO',    // Robotics
        'cs.NE',    // Neural and Evolutionary Computing
        'stat.ML'   // Machine Learning (Statistics)
      ];

      const results = [];
      const today = new Date();
      const threeDaysAgo = new Date(today.getTime() - 3 * 24 * 60 * 60 * 1000);
      
      console.log(`Searching for papers from last 3 days: ${threeDaysAgo.toISOString().split('T')[0]} to ${today.toISOString().split('T')[0]}`);
      
      for (const category of categories) {
        try {
          const response = await axios.get('http://export.arxiv.org/api/query', {
            params: {
              search_query: `cat:${category}`,
              sortBy: 'submittedDate',
              sortOrder: 'descending',
              max_results: 30
            }
          });

          const $ = cheerio.load(response.data, { xmlMode: true });
          let foundPapers = 0;
          let recentPapers = 0;
          
          $('entry').each((i, element) => {
            foundPapers++;
            const title = $(element).find('title').text().trim();
            const abstract = $(element).find('summary').text().trim();
            const publishedDate = $(element).find('published').text();
            
            // Parse the date properly
            const paperDate = new Date(publishedDate);
            
            // Check if paper is from last 3 days
            const isRecent = paperDate >= threeDaysAgo && paperDate <= today;
            
            if (isRecent) {
              recentPapers++;
              const link = $(element).find('link').attr('href');
              const authors = $(element).find('author name').map((i, el) => $(el).text()).get();
              const categories = $(element).find('category').map((i, el) => $(el).attr('term')).get();

              results.push({
                title,
                content: abstract,
                link,
                source: 'arXiv',
                date: publishedDate,
                authors,
                categories,
                type: 'research_paper',
                tags: this.extractTags(title + ' ' + abstract),
                is_trending: true
              });
            }
          });
          
          console.log(`Category ${category}: Found ${foundPapers} total papers, ${recentPapers} from last 3 days`);
          
        } catch (error) {
          console.error(`Error scraping category ${category}:`, error.message);
        }
      }

      console.log(`Found ${results.length} research papers from last 3 days`);
      return results
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .slice(0, 10);
    } catch (error) {
      console.error('Research paper scraping error:', error);
      return [];
    }
  }

  async scrapeAINews() {
    console.log('Starting AI news scraping...');
    const newsSources = [
      {
        name: 'MIT Technology Review - AI',
        url: 'https://www.technologyreview.com/topic/artificial-intelligence/feed/',
        category: 'research'
      },
      {
        name: 'VentureBeat AI',
        url: 'https://venturebeat.com/category/ai/feed/',
        category: 'industry'
      },
      {
        name: 'AI News',
        url: 'https://artificialintelligence-news.com/feed/',
        category: 'general'
      },
      {
        name: 'Synced',
        url: 'https://syncedreview.com/feed/',
        category: 'industry'
      },
      {
        name: 'Unite.AI',
        url: 'https://www.unite.ai/feed/',
        category: 'general'
      }
    ];

    try {
      const results = [];

      for (const source of newsSources) {
        console.log(`Scraping ${source.name}...`);
        try {
          const feed = await this.parser.parseURL(source.url);
          let foundArticles = 0;
          let filteredArticles = 0;
          
          const articles = feed.items
            .map(item => {
              foundArticles++;
              console.log(`Found article: "${item.title.substring(0, 50)}..." published: ${item.pubDate}`);
              
              return {
                title: item.title,
                content: item.content || item.contentSnippet || '',
                link: item.link,
                source: source.name,
                date: item.pubDate,
                category: source.category,
                type: 'news',
                tags: this.extractTags(item.title + ' ' + (item.content || item.contentSnippet || '')),
                is_trending: true // Temporarily set all as trending
              };
            })
            .filter(article => {
              const isFromToday = this.isFromToday(article.date);
              if (isFromToday) filteredArticles++;
              return isFromToday;
            });

          results.push(...articles);
          console.log(`${source.name}: Found ${foundArticles} total articles, ${filteredArticles} from today`);
        } catch (error) {
          console.error(`Error scraping ${source.name}:`, error.message);
        }
      }

      return results
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .slice(0, 10);
    } catch (error) {
      console.error('News scraping error:', error);
      return [];
    }
  }

  extractTags(text) {
    const commonTags = [
      'AI', 'ML', 'Deep Learning', 'Neural Networks', 'LLM', 'GPT', 'ChatGPT',
      'Computer Vision', 'NLP', 'Robotics', 'AGI', 'Ethics', 'Research',
      'Startup', 'Industry', 'Development', 'Applications', 'Framework',
      'Open Source', 'Commercial', 'Academic', 'Tutorial', 'News'
    ];

    const tags = new Set();
    const lowerText = text.toLowerCase();

    commonTags.forEach(tag => {
      if (lowerText.includes(tag.toLowerCase())) {
        tags.add(tag);
      }
    });

    return Array.from(tags);
  }

  async scrapeAllSources() {
    console.log('Starting scraping from all sources for today\'s content...');
    try {
      const results = {
        reddit: await this.scrapeReddit(),
        research: await this.scrapeResearchPapers(),
        news: await this.scrapeAINews()
      };

      // Add trending flag to all items
      Object.keys(results).forEach(key => {
        results[key] = results[key].map(item => ({
          ...item,
          is_trending: item.is_trending || false
        }));
      });

      const totalItems = results.reddit.length + results.research.length + results.news.length;
      console.log(`Scraping completed. Found ${totalItems} items from today:`, {
        reddit: results.reddit.length,
        research: results.research.length,
        news: results.news.length
      });

      await this.close();
      return results;
    } catch (error) {
      console.error('Error in scrapeAllSources:', error);
      await this.close();
      return {
        reddit: [],
        research: [],
        news: []
      };
    }
  }
}

module.exports = new ScraperService(); 