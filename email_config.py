# Email Lists Configuration for AI News Crawler
# Add your email addresses here for different groups

EMAIL_LISTS = {
    # Main AI News Digest List
    'main': [
        'vishvaluke@gmail.com',
        'vsrinivasan@unomaha.edu',
        'vishvaluke@proton.me'
        # Add more emails here
    ],
    
    # Team/Company List
    'team': [
        # 'team-member1@company.com',
        # 'team-member2@company.com',
        # Add team emails here
    ],
    
    # VIP/Priority List  
    'vip': [
        # 'vip1@example.com',
        # 'vip2@example.com',
        # Add VIP emails here
    ],
    
    # Test List (for testing purposes)
    'test': [
        'delivered@resend.dev',  # Resend test email
        'vishvaluke@gmail.com',  # Your email for testing
    ]
}

# Configuration for which list to use
CONFIG = {
    # Which email list to use for daily digest
    # Options: 'main', 'team', 'vip', 'test', or 'all'
    'active_list': 'main',  # Change this to your preferred list
    
    # Whether to also send to registered users (for future database integration)
    'include_registered_users': True,
    
    # Custom subject line (optional)
    'custom_subject': None,  # Set to string to override default
}

def get_active_email_list():
    """Helper function to get the active email list"""
    if CONFIG['active_list'] == 'all':
        # Combine all lists (remove duplicates)
        all_emails = []
        for email_list in EMAIL_LISTS.values():
            all_emails.extend(email_list)
        return list(set(all_emails))  # Remove duplicates
    
    return EMAIL_LISTS.get(CONFIG['active_list'], [])

def get_email_lists():
    """Get all email lists"""
    return EMAIL_LISTS

def get_config():
    """Get configuration"""
    return CONFIG 