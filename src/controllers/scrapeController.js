const scraperService = require('../services/scraperService');
const emailService = require('../services/emailService');
const User = require('../models/User');
const { getActiveEmailList, config } = require('../config/emailLists');

exports.triggerScraping = async (req, res) => {
  try {
    const data = await scraperService.scrapeAllSources();
    
    // If this is a manual trigger, send email to the requesting user
    if (req.user) {
      await emailService.sendDailyDigest(req.user, data);
    }

    res.json({
      message: 'Scraping completed successfully',
      data
    });
  } catch (error) {
    console.error('Scraping error:', error);
    res.status(500).json({ message: 'Error during scraping' });
  }
};

exports.sendDailyDigest = async () => {
  try {
    const data = await scraperService.scrapeAllSources();
    
    // Get email list from configuration
    const emailList = getActiveEmailList();
    
    // Get registered users if enabled
    let registeredUsers = [];
    if (config.includeRegisteredUsers) {
      registeredUsers = await User.findAll({
        where: {
          'preferences.emailFrequency': 'daily'
        }
      });
    }
    
    // Send to email list (primary method)
    if (emailList.length > 0) {
      try {
        await emailService.sendToEmailList(emailList, data);
        console.log(`✅ Daily digest sent to ${emailList.length} email addresses from configured list`);
      } catch (error) {
        console.error('❌ Failed to send to email list:', error);
      }
    } else {
      console.log('⚠️ No email addresses found in active email list');
    }
    
    // Send to registered users (if enabled and users exist)
    if (config.includeRegisteredUsers && registeredUsers.length > 0) {
      try {
        await emailService.sendBulkDailyDigest(registeredUsers, data);
        console.log(`✅ Daily digest also sent to ${registeredUsers.length} registered users`);
      } catch (error) {
        console.error('❌ Failed to send to registered users:', error);
        
        // Fallback: Send individual emails if bulk fails
        for (const user of registeredUsers) {
          try {
            await emailService.sendDailyDigest(user, data);
            console.log(`Daily digest sent to ${user.email}`);
          } catch (error) {
            console.error(`Failed to send digest to ${user.email}:`, error);
          }
        }
      }
    }
    
    // Summary
    const totalRecipients = emailList.length + (config.includeRegisteredUsers ? registeredUsers.length : 0);
    console.log(`📧 Daily digest process completed. Total potential recipients: ${totalRecipients}`);
    
  } catch (error) {
    console.error('Error sending daily digest:', error);
  }
}; 