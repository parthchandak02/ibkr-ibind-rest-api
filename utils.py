import os
import logging
import time
from ibind import IbkrClient, ibind_logs_initialize
from ibind.oauth.oauth1a import OAuth1aConfig
from ibind.support.errors import ExternalBrokerError

from config import Config

# Utility functions for the ibind REST API.

# Initialize ibind logs for better debugging
ibind_logs_initialize(log_level="DEBUG")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_ibind_logs(level=logging.DEBUG):
    """Initialize ibind logs with specified logging level."""
    ibind_logs_initialize(log_level=level)

def get_ibkr_client(environment="paper_trading", mock_mode=False, max_retries=8, retry_delay=2):
    """
    Get a configured IbkrClient.
    
    Args:
        environment (str): Trading environment (paper_trading or live_trading)
        mock_mode (bool): If True, returns a mock client
        max_retries (int): Maximum number of connection attempts
        retry_delay (int): Delay between retries in seconds
        
    Returns:
        IbkrClient: Configured client
    """
    if mock_mode:
        logger.info("Using mock mode, returning dummy client")
        return type('obj', (object,), {
            'check_health': lambda: True,
            'portfolio_accounts': lambda: type('obj', (object,), {'data': [{'accountId': 'MOCK123456'}]}),
            'get_ledger': lambda: type('obj', (object,), {'data': {}}),
            'positions': lambda: type('obj', (object,), {'data': []}),
            'live_orders': lambda: type('obj', (object,), {'data': []}),
            'order_status': lambda order_id: type('obj', (object,), {'data': {}}),
            'account_id': 'MOCK123456',
            'start_tickler': lambda: None
        })
    
    # Set environment variable for OAuth
    os.environ["IBIND_USE_OAUTH"] = "true"
    
    # Load configuration
    config = Config(environment)
    oauth_config = config.get_oauth_config()
    api_config = config.get_api_config()
    
    # Get host with scheme based on environment
    host = api_config.get('paper_trading_host') if environment == 'paper_trading' else api_config.get('live_trading_host')
    
    # Set up OAuth configuration
    oauth1a_config = OAuth1aConfig(
        access_token=oauth_config.get("access_token"),
        access_token_secret=oauth_config.get("access_token_secret"),
        consumer_key=oauth_config.get("consumer_key"),
        dh_prime=oauth_config.get("dh_prime"),
        encryption_key_fp=oauth_config.get("encryption_key_path"),
        signature_key_fp=oauth_config.get("signature_key_path"),
        realm=oauth_config.get("realm", "limited_poa")
    )
    
    # Initialize client with retries
    last_error = None
    for attempt in range(max_retries):
        try:
            logger.info("Connecting to IBKR API at %s (attempt %s/%s)", host, attempt+1, max_retries)
            client = IbkrClient(
                url=host,
                use_oauth=True,
                oauth_config=oauth1a_config
            )
            
            # Test connection with a simple API call
            # The check_health method may return a boolean, not an object with data attribute
            health_check = client.check_health()
            logger.info("Successfully connected to IBKR API. Health check: %s", health_check)
            
            # Make sure the tickler is running to maintain the connection
            client.start_tickler()
            logger.info("Started tickler to maintain connection alive")
            
            # Set the account ID if available from environment
            account_id = os.getenv('IBIND_ACCOUNT_ID')
            if account_id:
                client.account_id = account_id
                logger.info("Using account ID from environment: %s", account_id)
            else:
                # Try to get the first account ID
                try:
                    accounts = client.portfolio_accounts().data
                    if accounts and len(accounts) > 0:
                        client.account_id = accounts[0]['accountId']
                        logger.info("Using first available account ID: %s", client.account_id)
                    else:
                        logger.warning("No accounts found")
                except Exception as e:
                    logger.error("Failed to get account ID: %s", str(e))
            
            return client
        except ExternalBrokerError as e:
            last_error = e
            logger.warning("Connection attempt %s failed: %s", attempt+1, str(e))
            if attempt < max_retries - 1:
                retry_time = retry_delay * (attempt + 1)  # Increase delay with each attempt
                logger.info("Retrying in %s seconds...", retry_time)
                time.sleep(retry_time)
        except Exception as e:
            last_error = e
            logger.warning("Connection attempt %s failed: %s", attempt+1, str(e))
            if attempt < max_retries - 1:
                retry_time = retry_delay * (attempt + 1)  # Increase delay with each attempt
                logger.info("Retrying in %s seconds...", retry_time)
                time.sleep(retry_time)
    
    logger.error("Maximum retries reached (%s), could not connect to IBKR API: %s", max_retries, str(last_error))
    raise last_error
