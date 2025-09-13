"""
Utility functions for the ibind REST API.
"""

import logging
import os
import time
import threading
from pathlib import Path

from ibind import IbkrClient
from ibind.oauth.oauth1a import OAuth1aConfig
from ibind.support.errors import ExternalBrokerError

from .config import Config

# Initialize logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Singleton IBKR Client --- #

class SingletonIBKRClient:
    """A thread-safe singleton to manage the IBKR client connection per environment."""
    _clients_by_env = {}
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, environment="live_trading"):
        """Get or create the singleton client instance for the specified environment."""
        env_key = environment or os.getenv("IBIND_TRADING_ENV", "live_trading")
        if env_key not in cls._clients_by_env:
            with cls._lock:
                # Double-check locking to prevent race conditions
                if env_key not in cls._clients_by_env:
                    logger.info(f"Initializing IBKR Client for env: {env_key}...")
                    cls._clients_by_env[env_key] = cls._create_new_client(env_key)
        return cls._clients_by_env[env_key]

    @classmethod
    def get_health(cls, environment: str | None = None):
        """Check the health of the client for the given environment (or current)."""
        try:
            client = cls.get_instance(environment)
            if not client:
                return False
            return client.check_health()
        except Exception as e:
            logger.error(f"Singleton health check failed: {e}")
            return False

    @classmethod
    def _create_new_client(cls, environment):
        """The actual client creation logic."""
        # This logic is moved from the old get_ibkr_client function
        os.environ["IBIND_USE_OAUTH"] = "true"
        base_dir = Path(__file__).resolve().parent.parent
        config = Config(environment)
        oauth_config = config.get_oauth_config()
        api_config = config.get_api_config()
        # Allow host to be configured per env; fallback to generic 'host'
        host = (
            api_config.get("host")
            or api_config.get("live_trading_host")
            or api_config.get("paper_trading_host")
        )

        oauth_dir = f"{environment}_oauth_files"
        encryption_key_path = str(base_dir / oauth_dir / "private_encryption.pem")
        signature_key_path = str(base_dir / oauth_dir / "private_signature.pem")

        if not os.path.exists(encryption_key_path) or not os.path.exists(signature_key_path):
            logger.error("OAuth key files not found. Cannot create client.")
            raise FileNotFoundError("OAuth key files not found.")

        oauth1a_config = OAuth1aConfig(
            access_token=oauth_config.get("access_token"),
            access_token_secret=oauth_config.get("access_token_secret"),
            consumer_key=oauth_config.get("consumer_key"),
            dh_prime=oauth_config.get("dh_prime"),
            encryption_key_fp=encryption_key_path,
            signature_key_fp=signature_key_path,
            realm=oauth_config.get("realm", "limited_poa"),
        )

        # Retry logic remains important for initial connection
        max_retries = 8
        retry_delay = 2
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Connecting to IBKR API at {host} (attempt {attempt + 1}/{max_retries})"
                )
                client = IbkrClient(url=host, use_oauth=True, oauth_config=oauth1a_config)
                if client.check_health():
                    logger.info("Successfully connected to IBKR API.")
                    client.start_tickler()
                    logger.info("Started tickler to maintain connection.")
                    cls._set_account_id(client)
                    return client
            except Exception as e:
                last_error = e
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))

        logger.error(f"Could not connect to IBKR API after {max_retries} retries: {last_error}")
        raise last_error

    @staticmethod
    def _set_account_id(client):
        """Sets the account ID on the client instance."""
        account_id = os.getenv("IBIND_ACCOUNT_ID")
        if account_id:
            client.account_id = account_id
            logger.info(f"Using account ID from environment: {account_id}")
        else:
            try:
                accounts = client.portfolio_accounts().data
                if accounts:
                    client.account_id = accounts[0]["accountId"]
                    logger.info(f"Using first available account ID: {client.account_id}")
                else:
                    logger.warning("No accounts found for this session.")
            except Exception as e:
                logger.error(f"Failed to automatically get account ID: {e}")

# --- End Singleton --- #

def get_ibkr_client(environment="live_trading"):
    """Public function to access the singleton client for the given environment."""
    return SingletonIBKRClient.get_instance(environment)

def check_ibkr_health_status(environment: str | None = None):
    """Public function to check the health of the client for the given environment."""
    return SingletonIBKRClient.get_health(environment)

def reset_ibkr_client(environment: str | None = None):
    """Reset the cached client for an environment (or all if None)."""
    with SingletonIBKRClient._lock:
        if environment:
            SingletonIBKRClient._clients_by_env.pop(environment, None)
        else:
            SingletonIBKRClient._clients_by_env.clear()

# The old get_ibkr_client logic has been moved into the Singleton class.
# The old caching functions are no longer needed.
