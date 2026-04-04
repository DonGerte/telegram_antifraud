import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Credentials for bots and API access
PUBLIC_BOT_TOKEN = os.environ.get("PUBLIC_BOT_TOKEN")
PRIVATE_BOT_TOKEN = os.environ.get("PRIVATE_BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "" )

# Redis / Kafka connection strings (use whichever broker you prefer)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")

# Scoring/raid parameters (can be overridden by env)
RAID_THRESHOLD = int(os.environ.get("RAID_THRESHOLD", "20"))
RAID_WINDOW = int(os.environ.get("RAID_WINDOW", "300"))

# path to JSON file containing decision rules (optional)
RULES_FILE = os.environ.get("RULES_FILE", "rules.json")

WEBHOOK_SECRET_TOKEN = os.environ.get("WEBHOOK_SECRET_TOKEN", "")
ALLOWED_UPDATES = os.environ.get("ALLOWED_UPDATES", "[\"message\",\"edited_channel_post\",\"callback_query\"]")

# Admin IDs for private bot control (comma-separated user IDs)
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

# External API authentication
API_KEY = os.environ.get("API_KEY", "")

# other configuration values can be added here
