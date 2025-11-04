import os
import subprocess
import boto3
import logging
from datetime import datetime
from dotenv import load_dotenv

# === Setup Logging ===
# Create logs/database/ directory
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs", "database")
os.makedirs(LOG_DIR, exist_ok=True)

# Dynamic log file per day
LOG_FILE = os.path.join(LOG_DIR, f"backup_{datetime.now().strftime('%Y-%m-%d')}.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("%(message)s"))
logging.getLogger("").addHandler(console)

logging.info("🔍 Starting backup process...")

# === Load .env ===
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
logging.info(f"Loading environment from: {env_path}")
load_dotenv(env_path)

# === Database Configuration ===
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_PASSWORD = os.getenv("DB_PASSWORD")
BACKUP_DIR = os.getenv("BACKUP_DIR")

# === AWS Configuration ===
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# === Validate .env Variables ===
missing_vars = [k for k, v in {
    "DB_NAME": DB_NAME,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "BACKUP_DIR": BACKUP_DIR,
    "S3_BUCKET_NAME": S3_BUCKET_NAME,
}.items() if not v]

if missing_vars:
    logging.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
    raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")

# === Prepare Backup ===
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
backup_file = os.path.join(BACKUP_DIR, f"Propcare_{timestamp}.backup")

os.makedirs(BACKUP_DIR, exist_ok=True)

logging.info(f"🗄️ Creating PostgreSQL backup: {backup_file}")
pg_env = os.environ.copy()
pg_env["PGPASSWORD"] = DB_PASSWORD

dump_command = [
    "pg_dump",
    "-U", DB_USER,
    "-h", DB_HOST,
    "-p", DB_PORT,
    "-d", DB_NAME,
    "-F", "c",
    "-b",
    "-v",
    "-f", backup_file
]

# === Execute Backup ===
start_time = datetime.now()
try:
    subprocess.run(dump_command, env=pg_env, check=True)
    logging.info(f"✅ Backup successfully created at: {backup_file}")
except subprocess.CalledProcessError as e:
    logging.error(f"❌ Backup failed: {e}")
    exit(1)

# === Upload to AWS S3 ===
logging.info("☁️ Uploading to AWS S3...")

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

s3_key = f"backups/Database/{timestamp}/Propcare.backup"
try:
    s3.upload_file(backup_file, S3_BUCKET_NAME, s3_key)
    logging.info(f"✅ Successfully uploaded to s3://{S3_BUCKET_NAME}/{s3_key}")
except Exception as e:
    logging.error(f"❌ Upload to S3 failed: {e}")
    exit(1)

end_time = datetime.now()
duration = (end_time - start_time).seconds
logging.info(f"🎉 Backup and S3 upload completed successfully at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
logging.info(f"⏱️ Duration: {duration} seconds")
