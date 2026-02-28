import psycopg2
from pymongo import MongoClient
import os
import datetime

class PostgresDB:
    """Handles all PostgreSQL interactions for the tracking framework."""
    def __init__(self):
        # Database connection configuration from environment variables (useful for CI/CD)
        self.host = os.getenv("PG_HOST", "localhost")
        self.port = os.getenv("PG_PORT", "5432")
        self.user = os.getenv("PG_USER", "postgres")
        self.password = os.getenv("PG_PASSWORD", "postgres")
        self.dbname = os.getenv("PG_DB", "postgres")
        self.conn = None

    def connect(self):
        """Connect to the PostgreSQL database."""
        self.conn = psycopg2.connect(
            host=self.host, 
            port=self.port, 
            user=self.user, 
            password=self.password, 
            dbname=self.dbname
        )
        self.conn.autocommit = True

    def init_tables(self):
        """Create devices, tests, and results tables if they do not exist."""
        with self.conn.cursor() as cur:
            # 1. Devices table: tracks device status (AVAILABLE, RUNNING, etc.)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    device_id VARCHAR(255) PRIMARY KEY,
                    status VARCHAR(50),
                    updated_at TIMESTAMP
                )
            """)
            # 2. Tests table: tracks aggregated test definitions/sessions
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tests (
                    test_id SERIAL PRIMARY KEY,
                    test_name VARCHAR(255),
                    created_at TIMESTAMP
                )
            """)
            # 3. Results table: tracks granular results per device per test
            cur.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    result_id SERIAL PRIMARY KEY,
                    test_name VARCHAR(255),
                    device_id VARCHAR(255),
                    status VARCHAR(50),
                    duration_sec REAL,
                    error TEXT,
                    timestamp TIMESTAMP
                )
            """)

    def register_device(self, device_id: str, status: str):
        """Upsert a device's status into the devices table initially."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO devices (device_id, status, updated_at) 
                VALUES (%s, %s, %s) 
                ON CONFLICT (device_id) DO UPDATE 
                SET status = EXCLUDED.status, updated_at = EXCLUDED.updated_at
            """, (device_id, status, datetime.datetime.now()))

    def update_device_status(self, device_id: str, status: str):
        """Update just the status of an existing device during test runs."""
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE devices SET status = %s, updated_at = %s WHERE device_id = %s",
                (status, datetime.datetime.now(), device_id)
            )

    def log_result(self, test_name: str, device_id: str, status: str, duration: float, error: str):
        """Writes result to both tests and results tables after a test finishes."""
        with self.conn.cursor() as cur:
            now = datetime.datetime.now()
            # First, record the fact that this test was executed in the 'tests' table
            cur.execute(
                "INSERT INTO tests (test_name, created_at) VALUES (%s, %s)", 
                (test_name, now)
            )
            # Next, insert the precise outcome in the 'results' table
            cur.execute("""
                INSERT INTO results (test_name, device_id, status, duration_sec, error, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (test_name, device_id, status, duration, error, now))
            
    def close(self):
        """Safely close the connection."""
        if self.conn:
            self.conn.close()


class MongoDB:
    """Handles all MongoDB interactions for raw log ingestion."""
    def __init__(self):
        # Allow Mongo URI to be overridden by CI environment variables
        self.uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        self.client = None
        self.db = None
        self.logs = None

    def connect(self):
        """Connect to the MongoDB server."""
        self.client = MongoClient(self.uri)
        self.db = self.client["framework_db"]
        # Creating or connecting to the 'test_logs' collection directly
        self.logs = self.db["test_logs"]

    def write_log(self, test_name: str, device_id: str, status: str, duration: float, error: str, timestamp: datetime.datetime):
        """Writes a raw log document for a given test execution directly to MongoDB."""
        doc = {
            "test_name": test_name,
            "device_id": device_id,
            "status": status,
            "duration": duration,
            "error": error,
            "timestamp": timestamp
        }
        self.logs.insert_one(doc)

    def close(self):
        """Safely close the MongoDB client."""
        if self.client:
            self.client.close()
