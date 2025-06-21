import os
import logging
import requests
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import time
import json
import streamlit as st

load_dotenv()
logger = logging.getLogger("linkedin_scraper")

# We'll initialize the API token inside functions to avoid st.secrets issues during import
_APIFY_API_TOKEN = None

def _get_apify_token():
    """Get the Apify API token with proper error handling."""
    global _APIFY_API_TOKEN
    if _APIFY_API_TOKEN is None:
        # Try Streamlit secrets first (deployment)
        try:
            _APIFY_API_TOKEN = st.secrets["APIFY_API_TOKEN"]
        except (KeyError, AttributeError, Exception):
            # Fall back to environment variable (local development)
            _APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
            
        if not _APIFY_API_TOKEN:
            raise ValueError("APIFY_API_TOKEN not found in secrets or environment variables")
    
    return _APIFY_API_TOKEN

# Updated actor list with more reliable LinkedIn scrapers
POSSIBLE_ACTOR_IDS = [
    "2SyF0bVxmgGr8IVCZ",
    "VhxlqQXRwhW8H5hNV"
]

class LinkedInScraperError(Exception):
    pass

def validate_linkedin_url(url: str) -> bool:
    """Enhanced LinkedIn URL validation with better pattern matching."""
    import re
    
    patterns = [
        r"^https://(www\.)?linkedin\.com/in/[A-Za-z0-9\-_%]+/?$",
        r"^https://(www\.)?linkedin\.com/in/[A-Za-z0-9\-_%]+/.*$",
        r"^https://linkedin\.com/in/[A-Za-z0-9\-_%]+/?$"
    ]
    
    url = url.strip()
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    
    return False

def clean_linkedin_url(url: str) -> str:
    """Clean and normalize LinkedIn URL."""
    url = url.strip()
    
    if '/in/' in url:
        base_part = url.split('/in/')[0] + '/in/' + url.split('/in/')[1].split('/')[0]
        if not base_part.endswith('/'):
            base_part += '/'
        return base_part
    
    return url

def get_actor_input_schema(actor_id: str) -> Dict[str, Any]:
    """Get the input schema for a specific actor."""
    try:
        response = requests.get(
            f"https://api.apify.com/v2/acts/{actor_id}?token={_get_apify_token()}",
            timeout=10
        )
        if response.status_code == 200:
            actor_data = response.json()
            input_schema = actor_data.get('data', {}).get('defaultRunOptions', {}).get('inputSchema', {})
            return input_schema
        return {}
    except Exception as e:
        logger.warning(f"Failed to get input schema for {actor_id}: {e}")
        return {}

def create_actor_payload(actor_id: str, linkedin_url: str) -> Dict[str, Any]:
    """Create the correct payload format for different actors."""
    
    # Get input schema to understand required fields
    schema = get_actor_input_schema(actor_id)
    properties = schema.get('properties', {})
    
    logger.info(f"Actor {actor_id} input schema properties: {list(properties.keys())}")
    
    # Try to match schema requirements
    if 'profileUrls' in properties:
        return {"profileUrls": [linkedin_url]}
    elif 'urls' in properties:
        return {"urls": [linkedin_url]}
    elif 'startUrls' in properties:
        return {"startUrls": [{"url": linkedin_url}]}
    elif 'profileUrl' in properties:
        return {"profileUrl": linkedin_url}
    
    # Default to most common format
    return {"profileUrls": [linkedin_url]}

def test_actor_with_payload(actor_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Test an actor with a specific payload format."""
    try:
        # First, validate the payload by starting a test run
        test_url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={_get_apify_token()}"
        headers = {"Content-Type": "application/json"}
        
        logger.info(f"Testing actor {actor_id} with payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(test_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 201:
            run_data = response.json()
            run_id = run_data.get("data", {}).get("id")
            logger.info(f"✅ Actor {actor_id} accepted payload. Run ID: {run_id}")
            return {
                'success': True,
                'actor_id': actor_id,
                'run_id': run_id,
                'payload': payload
            }
        else:
            error_data = response.json() if response.content else {}
            logger.warning(f"❌ Actor {actor_id} rejected payload. Status: {response.status_code}")
            logger.warning(f"Error: {error_data}")
            return {
                'success': False,
                'actor_id': actor_id,
                'status_code': response.status_code,
                'error': error_data
            }
            
    except Exception as e:
        logger.error(f"Failed to test actor {actor_id}: {e}")
        return {'success': False, 'actor_id': actor_id, 'error': str(e)}

def find_working_actor_and_payload(linkedin_url: str) -> Dict[str, Any]:
    """Find a working actor and the correct payload format."""
    
    if not _get_apify_token():
        raise LinkedInScraperError("APIFY_API_TOKEN not set in environment")
    
    for actor_id in POSSIBLE_ACTOR_IDS:
        logger.info(f"🔍 Testing actor: {actor_id}")
        
        # Test if actor exists
        try:
            response = requests.get(
                f"https://api.apify.com/v2/acts/{actor_id}?token={_get_apify_token()}",
                timeout=10
            )
            if response.status_code != 200:
                logger.warning(f"Actor {actor_id} not accessible (status: {response.status_code})")
                continue
        except Exception as e:
            logger.warning(f"Failed to check actor {actor_id}: {e}")
            continue
        
        # Create payload for this actor
        payload = create_actor_payload(actor_id, linkedin_url)
        
        # Test the payload
        result = test_actor_with_payload(actor_id, payload)
        if result.get('success'):
            return result
    
    raise LinkedInScraperError(
        "No working actor found. This could be due to:\n"
        "1. Invalid API token\n"
        "2. No available LinkedIn scraper actors\n"
        "3. All actors require authentication/cookies\n"
        "4. API quota exceeded"
    )

def get_run_dataset_id(actor_id: str, run_id: str) -> Optional[str]:
    """Get the default dataset ID for a run."""
    try:
        response = requests.get(
            f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}?token={_get_apify_token()}",
            timeout=30
        )
        response.raise_for_status()
        
        run_data = response.json()
        dataset_id = run_data.get("data", {}).get("defaultDatasetId")
        logger.info(f"Found dataset ID: {dataset_id}")
        return dataset_id
        
    except Exception as e:
        logger.error(f"Failed to get dataset ID: {e}")
        return None

def wait_for_run_completion(actor_id: str, run_id: str, max_wait: int = 180) -> Dict[str, Any]:
    """Wait for a run to complete and return results."""
    
    wait_time = 0
    poll_interval = 10
    
    while wait_time < max_wait:
        time.sleep(poll_interval)
        wait_time += poll_interval
        
        try:
            # Check run status
            status_response = requests.get(
                f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}?token={_get_apify_token()}",
                timeout=30
            )
            status_response.raise_for_status()
            
            status_data = status_response.json()
            run_status = status_data.get("data", {}).get("status")
            
            logger.info(f"Run {run_id} status after {wait_time}s: {run_status}")
            
            if run_status == "SUCCEEDED":
                # Get the dataset ID from the run data
                dataset_id = status_data.get("data", {}).get("defaultDatasetId")
                
                if not dataset_id:
                    logger.warning("No dataset ID found in run data")
                    return {'success': False, 'error': 'No dataset ID found'}
                
                logger.info(f"Using dataset ID: {dataset_id}")
                
                # Try multiple dataset URL formats
                dataset_urls = [
                    f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={_get_apify_token()}",
                    f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}/dataset/items?token={_get_apify_token()}",
                ]
                
                for dataset_url in dataset_urls:
                    try:
                        logger.info(f"Trying dataset URL: {dataset_url}")
                        results_response = requests.get(dataset_url, timeout=30)
                        
                        if results_response.status_code == 200:
                            data = results_response.json()
                            if data and isinstance(data, list) and len(data) > 0:
                                logger.info(f"✅ Got {len(data)} results from dataset")
                                return {'success': True, 'data': data[0]}
                            else:
                                logger.warning("Dataset returned empty results")
                        else:
                            logger.warning(f"Dataset URL failed with status: {results_response.status_code}")
                            
                    except Exception as e:
                        logger.warning(f"Failed to fetch from {dataset_url}: {e}")
                        continue
                
                return {'success': False, 'error': 'Could not fetch results from any dataset URL'}
                    
            elif run_status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                error_info = status_data.get("data", {})
                logger.error(f"Run failed with status: {run_status}")
                logger.error(f"Error details: {error_info}")
                return {
                    'success': False, 
                    'error': f"Run failed with status: {run_status}",
                    'details': error_info
                }
        
        except Exception as e:
            logger.error(f"Error checking run status: {e}")
            
    return {'success': False, 'error': f'Run timed out after {max_wait} seconds'}

def sanitize_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced profile sanitization with better error handling."""
    
    field_mappings = {
        "name": ["fullName", "firstName", "lastName", "name"],
        "headline": ["headline", "title"],
        "about": ["about", "summary", "description"],
        "experience": ["experience", "positions", "workExperience"],
        "education": ["education", "schools"],
        "skills": ["skills", "skillsAndEndorsements"],
        "certifications": ["certifications", "certificates"],
        "languages": ["languages", "spokenLanguages"],
        "location": ["location", "locationName"],
        "profileUrl": ["profileUrl", "url", "linkedinUrl"]
    }
    
    sanitized = {}
    
    for target_key, possible_keys in field_mappings.items():
        value = None
        
        for key in possible_keys:
            if key in profile and profile[key]:
                value = profile[key]
                break
        
        if value is None:
            if target_key in ["experience", "education", "skills", "certifications", "languages"]:
                sanitized[target_key] = []
            else:
                sanitized[target_key] = ""
        else:
            sanitized[target_key] = value
    
    # Handle name combination if needed
    if not sanitized["name"] and "firstName" in profile:
        first_name = profile.get("firstName", "")
        last_name = profile.get("lastName", "")
        sanitized["name"] = f"{first_name} {last_name}".strip()
    
    return sanitized

def fetch_linkedin_profile(linkedin_url: str) -> Dict[str, Any]:
    """Main function to fetch LinkedIn profile with improved error handling."""
    
    if not validate_linkedin_url(linkedin_url):
        raise LinkedInScraperError("Invalid LinkedIn profile URL")
    
    cleaned_url = clean_linkedin_url(linkedin_url)
    logger.info(f"🚀 Starting LinkedIn profile scrape for: {cleaned_url}")
    
    # Find working actor and payload
    actor_config = find_working_actor_and_payload(cleaned_url)
    actor_id = actor_config['actor_id']
    run_id = actor_config['run_id']
    
    logger.info(f"✅ Using actor: {actor_id}, Run ID: {run_id}")
    
    # Wait for completion
    result = wait_for_run_completion(actor_id, run_id)
    
    if result.get('success'):
        profile_data = result['data']
        logger.info("✅ Profile scraped successfully!")
        return sanitize_profile(profile_data)
    else:
        error_msg = result.get('error', 'Unknown error')
        logger.error(f"❌ Scraping failed: {error_msg}")
        raise LinkedInScraperError(f"Scraping failed: {error_msg}")