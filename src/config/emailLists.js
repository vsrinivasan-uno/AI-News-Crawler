// Email Lists Configuration
// Add your email addresses here for different groups

const emailLists = {
  // Main AI News Digest List
  main: [
    'vishvaluke@gmail.com',
    'vsrinivasan@unomaha.edu',
    'vishvaluke@proton.me'
    // Add more emails here
  ],
  /*
  // Team/Company List
  team: [
    'team-member1@company.com',
    'team-member2@company.com',
    // Add team emails here
  ],
  
  // VIP/Priority List
  vip: [
    'vip1@example.com',
    'vip2@example.com',
    // Add VIP emails here
  ],
  
  // Test List (for testing purposes)
  test: [
    'delivered@resend.dev', // Resend test email
    'vishvaluke@gmail.com', // Your email for testing
  ] */
};

// Configuration for which list to use
const config = {
  // Which email list to use for daily digest
  // Options: 'main', 'team', 'vip', 'test', or 'all'
  activeList: 'main', // Change this to your preferred list
  
  // Whether to also send to registered users
  includeRegisteredUsers: true,
  
  // Custom subject line (optional)
  customSubject: null, // Set to string to override default
};

// Helper function to get the active email list
function getActiveEmailList() {
  if (config.activeList === 'all') {
    // Combine all lists (remove duplicates)
    const allEmails = [
      ...emailLists.main,
      ...emailLists.team,
      ...emailLists.vip,
      ...emailLists.test
    ];
    return [...new Set(allEmails)]; // Remove duplicates
  }
  
  return emailLists[config.activeList] || [];
}

// Helper function to get multiple lists
function getEmailLists(listNames) {
  if (!Array.isArray(listNames)) {
    listNames = [listNames];
  }
  
  const combinedEmails = [];
  for (const listName of listNames) {
    if (emailLists[listName]) {
      combinedEmails.push(...emailLists[listName]);
    }
  }
  
  return [...new Set(combinedEmails)]; // Remove duplicates
}

module.exports = {
  emailLists,
  config,
  getActiveEmailList,
  getEmailLists
}; 