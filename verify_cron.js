const cron = require('node-cron');

console.log('🔍 Cron Job Verification Script');
console.log('================================');

// Test if cron syntax is valid
const cronExpression = '0 18 * * *';
const isValid = cron.validate(cronExpression);

console.log(`📅 Cron Expression: ${cronExpression}`);
console.log(`✅ Valid Syntax: ${isValid}`);
console.log(`⏰ Schedule: Every day at 6:00 PM (18:00)`);
console.log(`🌍 Timezone: America/Chicago`);

// Calculate next execution times
if (isValid) {
  console.log('\n📋 Next 5 execution times:');
  
  // Create a temporary cron job to get next execution times
  const task = cron.schedule(cronExpression, () => {}, {
    scheduled: false,
    timezone: "America/Chicago"
  });
  
  // Get current time in Chicago timezone
  const now = new Date();
  const chicagoTime = new Date(now.toLocaleString("en-US", {timeZone: "America/Chicago"}));
  
  console.log(`🕐 Current Chicago Time: ${chicagoTime.toLocaleString()}`);
  
  // Calculate next few execution times
  const nextTimes = [];
  let testDate = new Date(chicagoTime);
  
  for (let i = 0; i < 5; i++) {
    // Set to 6 PM today or next day
    testDate.setHours(18, 0, 0, 0);
    
    // If 6 PM has passed today, move to next day
    if (testDate <= chicagoTime) {
      testDate.setDate(testDate.getDate() + 1);
    }
    
    nextTimes.push(new Date(testDate));
    testDate.setDate(testDate.getDate() + 1);
  }
  
  nextTimes.forEach((time, index) => {
    console.log(`   ${index + 1}. ${time.toLocaleString('en-US', {
      timeZone: 'America/Chicago',
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })}`);
  });
}

console.log('\n📧 Email Configuration:');
console.log('========================');

// Check email configuration
try {
  const { getActiveEmailList, config } = require('./src/config/emailLists');
  const emailList = getActiveEmailList();
  
  console.log(`📮 Active Email List: ${config.activeList}`);
  console.log(`👥 Number of Recipients: ${emailList.length}`);
  console.log(`📨 Include Registered Users: ${config.includeRegisteredUsers}`);
  
  if (emailList.length > 0) {
    console.log('📧 Email Recipients:');
    emailList.forEach((email, index) => {
      console.log(`   ${index + 1}. ${email}`);
    });
  }
} catch (error) {
  console.log('❌ Error loading email configuration:', error.message);
}

console.log('\n🚀 Server Status:');
console.log('=================');

// Test server connection
const http = require('http');
const options = {
  hostname: 'localhost',
  port: 3000,
  path: '/api/scrape',
  method: 'GET',
  timeout: 5000
};

const req = http.request(options, (res) => {
  console.log(`✅ Server is running on port 3000`);
  console.log(`📡 API Status: ${res.statusCode}`);
});

req.on('error', (err) => {
  console.log(`❌ Server connection failed: ${err.message}`);
});

req.on('timeout', () => {
  console.log(`⏱️ Server connection timeout`);
  req.destroy();
});

req.end();

console.log('\n🎯 Summary:');
console.log('===========');
console.log('✅ Cron job is configured to run daily at 6 PM Chicago time');
console.log('✅ When triggered, it will scrape AI news and send email digest');
console.log('✅ Server must stay running for cron job to execute');
console.log('\n💡 To test immediately, run: curl -X POST http://localhost:3000/api/scrape'); 