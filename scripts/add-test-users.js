const sequelize = require('../src/config/database');
const User = require('../src/models/User');

async function addTestUsers() {
  try {
    // Sync database
    await sequelize.sync();
    
    const testUsers = [
      {
        email: 'test1@example.com',
        password: 'password123',
        preferences: {
          sources: ['reddit', 'blogs', 'news'],
          topics: ['machine-learning', 'deep-learning', 'nlp'],
          emailFrequency: 'daily'
        }
      },
      {
        email: 'test2@example.com',
        password: 'password123',
        preferences: {
          sources: ['reddit', 'blogs', 'news'],
          topics: ['computer-vision', 'robotics'],
          emailFrequency: 'daily'
        }
      },
      {
        email: 'test3@example.com',
        password: 'password123',
        preferences: {
          sources: ['reddit', 'blogs', 'news'],
          topics: ['ai-ethics', 'machine-learning'],
          emailFrequency: 'daily'
        }
      }
    ];
    
    for (const userData of testUsers) {
      try {
        // Check if user already exists
        const existingUser = await User.findOne({ where: { email: userData.email } });
        if (existingUser) {
          console.log(`User ${userData.email} already exists, skipping...`);
          continue;
        }
        
        const user = await User.create(userData);
        console.log(`Created user: ${user.email}`);
      } catch (error) {
        console.error(`Failed to create user ${userData.email}:`, error.message);
      }
    }
    
    console.log('Test users setup complete!');
    process.exit(0);
  } catch (error) {
    console.error('Error setting up test users:', error);
    process.exit(1);
  }
}

addTestUsers(); 