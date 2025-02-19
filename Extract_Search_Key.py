import re

import re
from urllib.parse import quote_plus

def extract_search_keywords(error_info):
    """
    Dynamically extract search keywords from an error message.
    
    :param error_info: Error message or dictionary containing error details
    :return: List of relevant search keywords
    """
    # Convert input to string for processing
    if isinstance(error_info, dict):
        # Try to extract message from common dictionary keys
        error_message = error_info.get('message', 
                                       error_info.get('recent_logs', 
                                       str(error_info)))
    else:
        error_message = str(error_info)

    # Prevent empty input
    if not error_message:
        return []

    # Convert to lowercase for consistent processing
    cleaned_message = error_message.lower()

    # Initialize keyword set to ensure uniqueness
    keywords = set()

    # 1. Extract specific technical terms and library names
    tech_terms_patterns = [
        r'\b[a-z]+\.[a-z]+\b',              # Catch module.submodule patterns
        r'\bv\d+\.\d+\.\d+\b',              # Version numbers
        r'\bversion\s+\d+\.\d+\b',          # Version mentions
        r'\b[a-z]+\s+install\s+[^\s]+\b',   # Installation commands
    ]

    for pattern in tech_terms_patterns:
        keywords.update(re.findall(pattern, cleaned_message))

    # 2. Extract specific commands or code snippets
    code_patterns = [
        r'`[^`]+`',                         # Backtick-enclosed code snippets
        r'\bpip\s+install\s+[^\s]+\b',      # Pip install commands
        r'\b[a-z]+\s+migrate\b',            # Migration commands
    ]

    for pattern in code_patterns:
        code_matches = re.findall(pattern, cleaned_message)
        keywords.update(code_matches)

    # 3. Extract URLs and domain names
    url_pattern = r'https?://[^\s]+|www\.[^\s]+'
    url_matches = re.findall(url_pattern, cleaned_message)
    
    # Clean and extract domain names from URLs
    for url in url_matches:
        # Extract domain name
        domain_match = re.search(r'(?:https?://)?(?:www\.)?([^/]+)', url)
        if domain_match:
            keywords.add(domain_match.group(1))

    # 4. Extract potential error or warning keywords
    error_keywords = [
        'error', 'warning', 'exception', 'traceback', 
        'failed', 'not supported', 'deprecated'
    ]
    keywords.update(word for word in error_keywords if word in cleaned_message)

    # 5. Extract specific technical identifiers
    technical_patterns = [
        r'\b[A-Z][a-z]+[A-Z][a-z]+\b',  # CamelCase terms
        r'\b[a-z]+[A-Z][a-z]+\b',       # camelCase terms
    ]

    for pattern in technical_patterns:
        keywords.update(re.findall(pattern, error_message))

    # Convert to list and limit the number of keywords
    result_keywords = list(keywords)[:10]  # Limit to 10 keywords

    # Remove very short or generic keywords
    result_keywords = [
        kw for kw in result_keywords 
        if len(kw) > 2 and kw not in ['and', 'the', 'for']
    ]

    return result_keywords

