// Test the cron function directly
require('dotenv').config();

async function testCronFunction() {
  console.log('🧪 Testing Cron Function');
  console.log('========================');
  
  try {
    console.log('📡 Loading scrape controller...');
    const scrapeController = require('./src/controllers/scrapeController');
    
    console.log('🚀 Running sendDailyDigest function...');
    console.log('⏳ This may take a few minutes to scrape all sources...');
    
    const startTime = Date.now();
    await scrapeController.sendDailyDigest();
    const endTime = Date.now();
    
    console.log(`✅ Cron function completed successfully!`);
    console.log(`⏱️ Total execution time: ${((endTime - startTime) / 1000).toFixed(2)} seconds`);
    console.log('📧 Check your email for the daily digest!');
    
  } catch (error) {
    console.error('❌ Error testing cron function:', error);
  }
}

testCronFunction(); 