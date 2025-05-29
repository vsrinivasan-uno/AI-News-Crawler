#!/bin/bash

echo "🚀 AI News Crawler - GitHub Actions Deployment Script"
echo "===================================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing Git repository..."
    git init
fi

# Check for GitHub CLI
if command -v gh &> /dev/null; then
    HAS_GH_CLI=true
    echo "✅ GitHub CLI detected"
else
    HAS_GH_CLI=false
    echo "⚠️  GitHub CLI not found - manual setup required"
fi

# Add all files
echo "📂 Adding files to Git..."
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "ℹ️  No changes to commit"
else
    echo "💾 Committing changes..."
    git commit -m "Deploy AI News Crawler with GitHub Actions

- Add automated daily digest workflow
- Configure email service with Resend API
- Set up comprehensive scraping (Reddit, arXiv, News)
- Include manual trigger capability
- Add logging and monitoring"
fi

# Check for remote origin
if git remote get-url origin &> /dev/null; then
    echo "🔗 Remote origin already configured"
    REMOTE_EXISTS=true
else
    echo "⚠️  No remote origin configured"
    REMOTE_EXISTS=false
fi

if [ "$HAS_GH_CLI" = true ] && [ "$REMOTE_EXISTS" = false ]; then
    echo ""
    echo "🤖 Would you like to create a GitHub repository? (y/n)"
    read -r CREATE_REPO
    
    if [ "$CREATE_REPO" = "y" ] || [ "$CREATE_REPO" = "Y" ]; then
        echo "📝 Repository name (default: ai-news-crawler):"
        read -r REPO_NAME
        REPO_NAME=${REPO_NAME:-ai-news-crawler}
        
        echo "🔒 Make repository private? (y/n, default: n):"
        read -r PRIVATE_REPO
        
        if [ "$PRIVATE_REPO" = "y" ] || [ "$PRIVATE_REPO" = "Y" ]; then
            VISIBILITY="--private"
        else
            VISIBILITY="--public"
        fi
        
        echo "🚀 Creating GitHub repository..."
        gh repo create "$REPO_NAME" $VISIBILITY --description "AI News Crawler with automated daily digest via GitHub Actions" --source .
        
        echo "⬆️  Pushing to GitHub..."
        git push -u origin main
    fi
elif [ "$REMOTE_EXISTS" = true ]; then
    echo "⬆️  Pushing to existing repository..."
    git push
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Go to your GitHub repository"
echo "2. Navigate to Settings → Secrets and variables → Actions"
echo "3. Add required secrets:"
echo "   - RESEND_API_KEY (required)"
echo "   - EMAIL_USER (optional - Gmail fallback)"
echo "   - EMAIL_PASSWORD (optional - Gmail App Password)"
echo ""
echo "4. Test the workflow:"
echo "   - Go to Actions tab"
echo "   - Click 'AI News Daily Digest'"
echo "   - Click 'Run workflow'"
echo "   - Select test mode and run"
echo ""
echo "📖 For detailed setup instructions, see:"
echo "   → GITHUB_ACTIONS_SETUP.md"
echo ""
echo "⏰ Scheduled to run daily at 10:00 AM Omaha time!"
echo "🎯 Manual triggers available anytime via GitHub Actions" 