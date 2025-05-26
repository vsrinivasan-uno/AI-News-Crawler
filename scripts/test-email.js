require('dotenv').config();
const sequelize = require('../src/config/database');
const scrapeController = require('../src/controllers/scrapeController');

async function testEmail() {
  try {
    console.log('🚀 Testing email functionality...');
    console.log('📧 RESEND_API_KEY configured:', !!process.env.RESEND_API_KEY);
    
    // Sync database
    await sequelize.sync();
    
    // Trigger the daily digest manually
    await scrapeController.sendDailyDigest();
    
    console.log('✅ Email test completed!');
    process.exit(0);
  } catch (error) {
    console.error('❌ Email test failed:', error);
    process.exit(1);
  }
}

testEmail(); 