# AI News Crawler

A web crawler application that automatically collects and summarizes the latest AI news, tools, updates, and projects from various online sources.

## Features

- Automated web scraping of AI-related content
- Customizable user preferences for content sources and topics
- Daily email summaries of the most relevant AI news
- User authentication and preference management
- Mobile-friendly email design

## Tech Stack

- Frontend: React
- Backend: Node.js with Express
- Database: MongoDB
- Web Scraping: Cheerio/Puppeteer
- Email Service: Nodemailer

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create a `.env` file in the root directory with the following variables:
   ```
   MONGODB_URI=your_mongodb_connection_string
   JWT_SECRET=your_jwt_secret
   EMAIL_USER=your_email
   EMAIL_PASS=your_email_password
   ```
4. Start the development server:
   ```bash
   npm run dev
   ```

## Project Structure

```
src/
├── config/         # Configuration files
├── controllers/    # Route controllers
├── models/         # Database models
├── routes/         # API routes
├── services/       # Business logic
├── utils/          # Utility functions
└── server.js       # Application entry point
```

## API Endpoints

- POST /api/auth/register - Register a new user
- POST /api/auth/login - User login
- GET /api/preferences - Get user preferences
- PUT /api/preferences - Update user preferences
- GET /api/emails - Get past email summaries
- POST /api/scrape - Trigger manual scraping

## License

MIT 