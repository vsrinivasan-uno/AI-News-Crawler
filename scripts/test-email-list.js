require('dotenv').config();
const sequelize = require('../src/config/database');
const scraperService = require('../src/services/scraperService');
const emailService = require('../src/services/emailService');
const { getActiveEmailList, getEmailLists, config } = require('../src/config/emailLists');

async function testEmailList() {
  try {
    console.log('🚀 Testing Email List Functionality...');
    console.log('📧 RESEND_API_KEY configured:', !!process.env.RESEND_API_KEY);
    
    // Sync database
    await sequelize.sync();
    
    // Show current configuration
    console.log('\n📋 Current Configuration:');
    console.log(`   Active List: ${config.activeList}`);
    console.log(`   Include Registered Users: ${config.includeRegisteredUsers}`);
    
    // Show active email list
    const emailList = getActiveEmailList();
    console.log(`\n📮 Active Email List (${emailList.length} addresses):`);
    emailList.forEach((email, index) => {
      console.log(`   ${index + 1}. ${email}`);
    });
    
    if (emailList.length === 0) {
      console.log('⚠️ No email addresses in active list. Please update src/config/emailLists.js');
      return;
    }
    
    // Get sample data (you can use mock data for faster testing)
    console.log('\n🔍 Scraping latest AI content...');
    const data = await scraperService.scrapeAllSources();
    
    console.log(`\n📊 Content Summary:`);
    console.log(`   Reddit Posts: ${data.reddit.length}`);
    console.log(`   Research Papers: ${data.research.length}`);
    console.log(`   News Articles: ${data.news.length}`);
    
    // Send to email list
    console.log('\n📤 Sending emails...');
    await emailService.sendToEmailList(emailList, data);
    
    console.log('\n✅ Email list test completed successfully!');
    console.log('\n💡 Tips:');
    console.log('   - Check your email inbox (including spam folder)');
    console.log('   - Update email addresses in src/config/emailLists.js');
    console.log('   - Change activeList to "main", "team", "vip", or "all"');
    
    process.exit(0);
  } catch (error) {
    console.error('❌ Email list test failed:', error);
    process.exit(1);
  }
}

// Allow command line arguments to test different lists
const args = process.argv.slice(2);
if (args.length > 0) {
  const listName = args[0];
  console.log(`🎯 Testing specific list: ${listName}`);
  
  // Override config for this test
  config.activeList = listName;
}

testEmailList(); 