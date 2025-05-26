const User = require('../models/User');

exports.getPreferences = async (req, res) => {
  try {
    const user = await User.findByPk(req.user.id);
    res.json({ preferences: user.preferences });
  } catch (error) {
    console.error('Error fetching preferences:', error);
    res.status(500).json({ message: 'Error fetching preferences' });
  }
};

exports.updatePreferences = async (req, res) => {
  try {
    const { sources, topics, emailFrequency } = req.body;

    const user = await User.findByPk(req.user.id);
    
    if (sources) user.preferences.sources = sources;
    if (topics) user.preferences.topics = topics;
    if (emailFrequency) user.preferences.emailFrequency = emailFrequency;

    await user.save();

    res.json({
      message: 'Preferences updated successfully',
      preferences: user.preferences
    });
  } catch (error) {
    console.error('Error updating preferences:', error);
    res.status(500).json({ message: 'Error updating preferences' });
  }
}; 