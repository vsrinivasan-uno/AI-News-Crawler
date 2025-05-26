const { Resend } = require('resend');

class EmailService {
  constructor() {
    this.resend = new Resend(process.env.RESEND_API_KEY);
  }

  async sendEmail(to, subject, content) {
    try {
      // Handle both single email string and array of emails
      const recipients = Array.isArray(to) ? to : [to];
      
      const { data, error } = await this.resend.emails.send({
        from: 'Vishva - AI News Digest <vishva@resend.dev>',
        to: recipients,
        subject: subject,
        html: content
      });

      if (error) {
        console.error('Error sending email:', error);
        throw error;
      }

      console.log(`Email sent successfully to ${recipients.length} recipient(s):`, data);
      return data;
    } catch (error) {
      console.error('Failed to send email:', error);
      throw error;
    }
  }

  async sendDailyDigest(user, content) {
    try {
      const subject = 'AI Intelligence Brief';
      const htmlContent = this.formatDigestEmail(content);
      return await this.sendEmail(user.email, subject, htmlContent);
    } catch (error) {
      console.error('Failed to send daily digest:', error);
      throw error;
    }
  }

  async sendBulkDailyDigest(users, content) {
    try {
      const subject = 'AI Intelligence Brief';
      const htmlContent = this.formatDigestEmail(content);
      
      // Extract email addresses from user objects
      const emailAddresses = users.map(user => user.email);
      
      // Resend allows up to 50 recipients per email on free plan
      const maxRecipientsPerEmail = 50;
      const emailBatches = [];
      
      for (let i = 0; i < emailAddresses.length; i += maxRecipientsPerEmail) {
        emailBatches.push(emailAddresses.slice(i, i + maxRecipientsPerEmail));
      }
      
      console.log(`Sending digest to ${emailAddresses.length} users in ${emailBatches.length} batch(es)`);
      
      const results = [];
      for (const batch of emailBatches) {
        try {
          const result = await this.sendEmail(batch, subject, htmlContent);
          results.push(result);
          console.log(`Batch sent to ${batch.length} recipients`);
        } catch (error) {
          console.error(`Failed to send batch to ${batch.length} recipients:`, error);
          // Continue with other batches even if one fails
        }
      }
      
      return results;
    } catch (error) {
      console.error('Failed to send bulk daily digest:', error);
      throw error;
    }
  }

  // NEW: Send to specific email list (no user registration required)
  async sendToEmailList(emailList, content) {
    try {
      const subject = 'AI Intelligence Brief';
      const htmlContent = this.formatDigestEmail(content);
      
      // Validate email list
      if (!Array.isArray(emailList) || emailList.length === 0) {
        throw new Error('Email list must be a non-empty array');
      }
      
      // Resend allows up to 50 recipients per email on free plan
      const maxRecipientsPerEmail = 50;
      const emailBatches = [];
      
      for (let i = 0; i < emailList.length; i += maxRecipientsPerEmail) {
        emailBatches.push(emailList.slice(i, i + maxRecipientsPerEmail));
      }
      
      console.log(`Sending digest to ${emailList.length} email addresses in ${emailBatches.length} batch(es)`);
      
      const results = [];
      for (const batch of emailBatches) {
        try {
          const result = await this.sendEmail(batch, subject, htmlContent);
          results.push(result);
          console.log(`Batch sent to ${batch.length} recipients: ${batch.join(', ')}`);
        } catch (error) {
          console.error(`Failed to send batch to ${batch.length} recipients:`, error);
          // Continue with other batches even if one fails
        }
      }
      
      return results;
    } catch (error) {
      console.error('Failed to send to email list:', error);
      throw error;
    }
  }

  truncateContent(content, maxLength = 150) {
    if (!content || content.trim() === '') return 'Click to read the full article for more details.';
    
    // Strip HTML tags and decode HTML entities
    const cleanContent = content
      .replace(/<[^>]*>/g, '') // Remove HTML tags
      .replace(/&[^;]+;/g, ' ') // Remove HTML entities
      .replace(/\s+/g, ' ') // Replace multiple spaces with single space
      .trim();
    
    if (cleanContent.length === 0) return 'Click to read the full article for more details.';
    
    return cleanContent.length > maxLength 
      ? cleanContent.substring(0, maxLength) + '...' 
      : cleanContent;
  }

  formatDigestEmail(content) {
    const { reddit, research, news } = content;
    
    return `
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
                      <p style="margin: 12px 0 0 0; color: rgba(255,255,255,0.8); font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${new Date().toLocaleDateString('en-US', { 
                        weekday: 'long', 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric' 
                      })}</p>
                    </td>
                  </tr>
                  
                  <!-- Research Papers Section -->
                  <tr>
                    <td style="padding: 30px;">
                      <h2 style="margin: 0 0 25px 0; color: #1f2937; font-size: 22px; font-weight: 700; border-bottom: 2px solid #e5e7eb; padding-bottom: 12px;">
                        🔬 Research Papers <span style="background: #3b82f6; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-left: 10px;">${research.length}</span>
                      </h2>
                      
                      ${research.length > 0 ? research.map(paper => `
                        <div style="margin-bottom: 20px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; background-color: #fafafa;">
                          <div style="padding: 24px;">
                            <h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 18px; font-weight: 600; line-height: 1.4;">
                              <a href="${paper.link}" style="color: #1f2937; text-decoration: none;" target="_blank">${paper.title}</a>
                            </h3>
                            <p style="margin: 0 0 15px 0; color: #6b7280; font-size: 14px; line-height: 1.5;">
                              📄 arXiv • 👥 ${paper.authors.slice(0, 2).join(', ')}${paper.authors.length > 2 ? ' et al.' : ''} • 📅 ${new Date(paper.date).toLocaleDateString()}
                            </p>
                            <p style="margin: 0 0 18px 0; color: #4b5563; font-size: 15px; line-height: 1.6;">${this.truncateContent(paper.content, 180)}</p>
                            <a href="${paper.link}" style="display: inline-block; background: #3b82f6; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: 500;" target="_blank">Read Paper →</a>
                          </div>
                        </div>
                      `).join('') : `
                        <p style="text-align: center; color: #6b7280; font-style: italic; padding: 40px 20px; background-color: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">No new research papers today. Check back tomorrow for the latest AI research!</p>
                      `}
                    </td>
                  </tr>
                  
                  <!-- Industry News Section -->
                  <tr>
                    <td style="padding: 0 30px 30px 30px;">
                      <h2 style="margin: 0 0 25px 0; color: #1f2937; font-size: 22px; font-weight: 700; border-bottom: 2px solid #e5e7eb; padding-bottom: 12px;">
                        📰 Industry News <span style="background: #3b82f6; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-left: 10px;">${news.length}</span>
                      </h2>
                      
                      ${news.length > 0 ? news.map(article => `
                        <div style="margin-bottom: 20px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; background-color: #fafafa;">
                          <div style="padding: 24px;">
                            <h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 18px; font-weight: 600; line-height: 1.4;">
                              <a href="${article.link}" style="color: #1f2937; text-decoration: none;" target="_blank">${article.title}</a>
                              ${article.is_trending ? '<span style="background: linear-gradient(135deg, #ef4444, #dc2626); color: white; padding: 3px 8px; border-radius: 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; margin-left: 8px;">Breaking</span>' : ''}
                            </h3>
                            <p style="margin: 0 0 15px 0; color: #6b7280; font-size: 14px; line-height: 1.5;">
                              🏢 ${article.source} • 📂 ${article.category} • 📅 ${new Date(article.date).toLocaleDateString()}
                            </p>
                            <p style="margin: 0 0 18px 0; color: #4b5563; font-size: 15px; line-height: 1.6;">${this.truncateContent(article.content, 180)}</p>
                            <a href="${article.link}" style="display: inline-block; background: #3b82f6; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: 500;" target="_blank">Read Article →</a>
                          </div>
                        </div>
                      `).join('') : `
                        <p style="text-align: center; color: #6b7280; font-style: italic; padding: 40px 20px; background-color: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">No significant industry news today. Stay tuned for the latest developments!</p>
                      `}
                    </td>
                  </tr>
                  
                  <!-- Community Insights Section -->
                  <tr>
                    <td style="padding: 0 30px 30px 30px;">
                      <h2 style="margin: 0 0 25px 0; color: #1f2937; font-size: 22px; font-weight: 700; border-bottom: 2px solid #e5e7eb; padding-bottom: 12px;">
                        💬 Community Insights <span style="background: #3b82f6; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-left: 10px;">${reddit.length}</span>
                      </h2>
                      
                      ${reddit.length > 0 ? reddit.map(post => `
                        <div style="margin-bottom: 20px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; background-color: #fafafa;">
                          <div style="padding: 24px;">
                            <h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 18px; font-weight: 600; line-height: 1.4;">
                              <a href="${post.link}" style="color: #1f2937; text-decoration: none;" target="_blank">${post.title}</a>
                              ${post.is_trending ? '<span style="background: linear-gradient(135deg, #ef4444, #dc2626); color: white; padding: 3px 8px; border-radius: 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; margin-left: 8px;">Trending</span>' : ''}
                            </h3>
                            <p style="margin: 0 0 15px 0; color: #6b7280; font-size: 14px; line-height: 1.5;">
                              📍 r/${post.subreddit} • 👤 ${post.author} • ⬆️ ${post.score} • 💬 ${post.comments}
                            </p>
                            <p style="margin: 0 0 18px 0; color: #4b5563; font-size: 15px; line-height: 1.6;">${this.truncateContent(post.content, 180)}</p>
                            <a href="${post.link}" style="display: inline-block; background: #3b82f6; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: 500;" target="_blank">Join Discussion →</a>
                          </div>
                        </div>
                      `).join('') : `
                        <p style="text-align: center; color: #6b7280; font-style: italic; padding: 40px 20px; background-color: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">No trending community discussions today. Check back for the latest conversations!</p>
                      `}
                    </td>
                  </tr>
                  
                  <!-- Footer -->
                  <tr>
                    <td style="background-color: #1f2937; padding: 30px; text-align: center;">
                      <h3 style="margin: 0 0 10px 0; color: #f9fafb; font-size: 18px; font-weight: 600;">AI Intelligence Brief</h3>
                      <p style="margin: 0 0 5px 0; color: #9ca3af; font-size: 14px;">Curated daily by your AI News Crawler</p>
                      <p style="margin: 0 0 20px 0; color: #9ca3af; font-size: 14px;">Bringing you the most significant developments in artificial intelligence</p>
                      <p style="margin: 0; color: #6b7280; font-size: 12px;">
                        <a href="#" style="color: #60a5fa; text-decoration: none;">Manage preferences</a> • 
                        <a href="#" style="color: #60a5fa; text-decoration: none;">Unsubscribe</a> • 
                        <a href="#" style="color: #60a5fa; text-decoration: none;">Archive</a>
                      </p>
                    </td>
                  </tr>
                  
                </table>
              </td>
            </tr>
          </table>
          
        </body>
      </html>
    `;
  }
}

module.exports = new EmailService(); 