import os

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

# other configuration values can be added here
