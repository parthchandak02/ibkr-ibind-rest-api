"""
Utility functions for the ibind REST API.
"""
import os
import logging
import time
from pathlib import Path
from ibind import IbkrClient, ibind_logs_initialize
from ibind.oauth.oauth1a import OAuth1aConfig
from ibind.support.errors import ExternalBrokerError

from config import Config

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_ibkr_client(environment="paper_trading", max_retries=8, retry_delay=2):
    """
    Get a configured IbkrClient with automatic retry logic.

    Args:
        environment (str): Trading environment (paper_trading or live_trading)
        max_retries (int): Maximum number of connection attempts
        retry_delay (int): Base delay between retries in seconds (increases with each attempt)

    Returns:
        IbkrClient: Configured client

    Raises:
        ExternalBrokerError: If connection fails after max retries
    """
    # Set environment variable for OAuth
    os.environ["IBIND_USE_OAUTH"] = "true"
    
    # Get base directory
    base_dir = Path(__file__).resolve().parent
    
    # Load configuration
    config = Config(environment)
    oauth_config = config.get_oauth_config()
    api_config = config.get_api_config()

    # Get host based on environment
    host = api_config.get('paper_trading_host' if environment == 'paper_trading' else 'live_trading_host')

    # Ensure absolute paths for key files
    oauth_dir = f"{environment}_oauth_files"
    encryption_key_path = str(base_dir / oauth_dir / "private_encryption.pem")
    signature_key_path = str(base_dir / oauth_dir / "private_signature.pem")
    
    # Log the paths for debugging
    logger.info(f"Using encryption key path: {encryption_key_path}")
    logger.info(f"Using signature key path: {signature_key_path}")
    
    # Verify files exist
    if not os.path.exists(encryption_key_path):
        logger.error(f"Encryption key file not found: {encryption_key_path}")
        raise FileNotFoundError(f"Encryption key file not found: {encryption_key_path}")
    if not os.path.exists(signature_key_path):
        logger.error(f"Signature key file not found: {signature_key_path}")
        raise FileNotFoundError(f"Signature key file not found: {signature_key_path}")

    # Set up OAuth configuration
    oauth1a_config = OAuth1aConfig(
        access_token=oauth_config.get("access_token"),
        access_token_secret=oauth_config.get("access_token_secret"),
        consumer_key=oauth_config.get("consumer_key"),
        dh_prime=oauth_config.get("dh_prime"),
        encryption_key_fp=encryption_key_path,
        signature_key_fp=signature_key_path,
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

            # Test connection
            health_check = client.check_health()
            logger.info("Successfully connected to IBKR API. Health check: %s", health_check)

            # Start connection maintenance
            client.start_tickler()
            logger.info("Started tickler to maintain connection")

            # Set account ID
            account_id = os.getenv('IBIND_ACCOUNT_ID')
            if account_id:
                client.account_id = account_id
                logger.info("Using account ID from environment: %s", account_id)
            else:
                try:
                    accounts = client.portfolio_accounts().data
                    if accounts:
                        client.account_id = accounts[0]['accountId']
                        logger.info("Using first available account ID: %s", client.account_id)
                    else:
                        logger.warning("No accounts found")
                except Exception as e:
                    logger.error("Failed to get account ID: %s", str(e))

            return client

        except (ExternalBrokerError, Exception) as e:
            last_error = e
            logger.warning("Connection attempt %s failed: %s", attempt+1, str(e))
            if attempt < max_retries - 1:
                retry_time = retry_delay * (attempt + 1)
                logger.info("Retrying in %s seconds...", retry_time)
                time.sleep(retry_time)

    logger.error("Maximum retries reached (%s), could not connect to IBKR API: %s", max_retries, str(last_error))
    raise last_error
