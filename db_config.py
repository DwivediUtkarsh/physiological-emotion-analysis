"""
MongoDB Configuration for SURJA System
Database connection settings and configuration
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Connection Settings
MONGODB_HOST = "localhost"
MONGODB_PORT = 27017
DATABASE_NAME = "surja_db"
CONNECTION_TIMEOUT = 5000  # milliseconds

# Collection Names
COLLECTIONS = {
    'signals': 'signals',                      # Raw physiological signals
    'video_starts': 'video_starts',            # Video start timestamps
    'windowed_data': 'windowed_data',          # Windowed physiological data
    'change_scores': 'change_scores',          # Change point detection scores
    'features': 'features',                    # Extracted features for ML
    'predictions': 'predictions',              # Permanent prediction log
    'active_predictions': 'active_predictions' # Active predictions for frontend
}


class DatabaseConnection:
    """MongoDB Connection Manager"""
    
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        """Singleton pattern to ensure single connection"""
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance
    
    def connect(self):
        """Establish connection to MongoDB"""
        if self._client is None:
            try:
                self._client = MongoClient(
                    host=MONGODB_HOST,
                    port=MONGODB_PORT,
                    serverSelectionTimeoutMS=CONNECTION_TIMEOUT
                )
                # Test connection
                self._client.admin.command('ping')
                self._db = self._client[DATABASE_NAME]
                logger.info(f"✅ Connected to MongoDB at {MONGODB_HOST}:{MONGODB_PORT}")
                logger.info(f"✅ Using database: {DATABASE_NAME}")
                return True
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(f"❌ Failed to connect to MongoDB: {e}")
                return False
        return True
    
    def get_database(self):
        """Get database instance"""
        if self._db is None:
            self.connect()
        return self._db
    
    def get_collection(self, collection_name):
        """Get collection instance"""
        db = self.get_database()
        if db is not None:
            return db[COLLECTIONS[collection_name]]
        return None
    
    def close(self):
        """Close MongoDB connection"""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("🔌 MongoDB connection closed")


def get_db():
    """Helper function to get database instance"""
    conn = DatabaseConnection()
    conn.connect()
    return conn.get_database()


def get_collection(collection_name):
    """Helper function to get collection instance"""
    conn = DatabaseConnection()
    conn.connect()
    return conn.get_collection(collection_name)


def initialize_indexes():
    """
    Create indexes for all collections to optimize queries
    Should be run once during setup
    """
    conn = DatabaseConnection()
    if not conn.connect():
        logger.error("Cannot create indexes - database connection failed")
        return False
    
    db = conn.get_database()
    
    try:
        # Signals collection indexes
        db[COLLECTIONS['signals']].create_index([("timestamp", ASCENDING)])
        db[COLLECTIONS['signals']].create_index([("created_at", DESCENDING)])
        # Multi-user support indexes
        db[COLLECTIONS['signals']].create_index([("user_id", ASCENDING)])
        db[COLLECTIONS['signals']].create_index([("session_id", ASCENDING)])
        db[COLLECTIONS['signals']].create_index([("user_id", ASCENDING), ("video_id", ASCENDING)])
        logger.info("✅ Created indexes for 'signals' collection (including user_id)")
        
        # Video starts collection indexes
        db[COLLECTIONS['video_starts']].create_index([("video_id", ASCENDING)])
        db[COLLECTIONS['video_starts']].create_index([("timestamp", ASCENDING)])
        db[COLLECTIONS['video_starts']].create_index([("created_at", DESCENDING)])
        # Multi-user support indexes
        db[COLLECTIONS['video_starts']].create_index([("user_id", ASCENDING)])
        db[COLLECTIONS['video_starts']].create_index([("session_id", ASCENDING)])
        db[COLLECTIONS['video_starts']].create_index([("user_id", ASCENDING), ("video_id", ASCENDING)])
        logger.info("✅ Created indexes for 'video_starts' collection (including user_id)")
        
        # Windowed data collection indexes
        db[COLLECTIONS['windowed_data']].create_index([("start_time", ASCENDING)])
        db[COLLECTIONS['windowed_data']].create_index([("video_id", ASCENDING)])
        db[COLLECTIONS['windowed_data']].create_index([("window_type", ASCENDING)])
        logger.info("✅ Created indexes for 'windowed_data' collection")
        
        # Change scores collection indexes
        db[COLLECTIONS['change_scores']].create_index([("start_time", ASCENDING)])
        db[COLLECTIONS['change_scores']].create_index([("created_at", DESCENDING)])
        logger.info("✅ Created indexes for 'change_scores' collection")
        
        # Features collection indexes
        db[COLLECTIONS['features']].create_index([("start_time", ASCENDING)])
        db[COLLECTIONS['features']].create_index([("video_id", ASCENDING)])
        db[COLLECTIONS['features']].create_index([("created_at", DESCENDING)])
        logger.info("✅ Created indexes for 'features' collection")
        
        # Predictions collection indexes
        db[COLLECTIONS['predictions']].create_index([("starttime", ASCENDING)])
        db[COLLECTIONS['predictions']].create_index([("video_no", ASCENDING)])
        db[COLLECTIONS['predictions']].create_index([("created_at", DESCENDING)])
        # Multi-user support indexes (compound for efficient filtering)
        db[COLLECTIONS['predictions']].create_index([("user_id", ASCENDING)])
        db[COLLECTIONS['predictions']].create_index([("session_id", ASCENDING)])
        db[COLLECTIONS['predictions']].create_index([("user_id", ASCENDING), ("video_no", ASCENDING)])
        db[COLLECTIONS['predictions']].create_index([("user_id", ASCENDING), ("video_no", ASCENDING), ("starttime", ASCENDING)])
        logger.info("✅ Created indexes for 'predictions' collection (including user_id)")
        
        # Active predictions collection indexes
        db[COLLECTIONS['active_predictions']].create_index([("video_no", ASCENDING)])
        db[COLLECTIONS['active_predictions']].create_index([("created_at", DESCENDING)])
        # TTL index to auto-delete old predictions after 1 hour
        db[COLLECTIONS['active_predictions']].create_index(
            [("created_at", ASCENDING)], 
            expireAfterSeconds=3600
        )
        # Multi-user support indexes
        db[COLLECTIONS['active_predictions']].create_index([("user_id", ASCENDING)])
        db[COLLECTIONS['active_predictions']].create_index([("session_id", ASCENDING)])
        db[COLLECTIONS['active_predictions']].create_index([("user_id", ASCENDING), ("video_no", ASCENDING)])
        logger.info("✅ Created indexes for 'active_predictions' collection (with TTL + user_id)")
        
        logger.info("✅ All indexes created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating indexes: {e}")
        return False


if __name__ == "__main__":
    """Test database connection and create indexes"""
    print("\n" + "="*60)
    print("SURJA Database Configuration Test")
    print("="*60 + "\n")
    
    # Test connection
    conn = DatabaseConnection()
    if conn.connect():
        print("✅ Database connection successful!\n")
        
        # List existing collections
        db = conn.get_database()
        collections = db.list_collection_names()
        print(f"📋 Existing collections: {collections if collections else 'None (new database)'}\n")
        
        # Create indexes
        print("Creating indexes...")
        if initialize_indexes():
            print("\n✅ Database setup complete!")
        else:
            print("\n❌ Index creation failed")
        
        conn.close()
    else:
        print("❌ Database connection failed!")

