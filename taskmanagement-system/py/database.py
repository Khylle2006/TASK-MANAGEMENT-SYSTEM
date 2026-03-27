import sqlite3
import os

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'task_management.db')

def get_connection():
    """Create and return a SQLite database connection"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # This allows column access by name
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def initialize_db():
    """Initialize the database with all required tables"""
    conn = get_connection()
    if conn is None:
        print("Failed to connect to database")
        return
    
    cursor = conn.cursor()

    try:
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create lists table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                name TEXT NOT NULL,
                section TEXT DEFAULT 'WORK',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
                UNIQUE(username, name)
            )
        """)
        
        # Create tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                list_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT CHECK(priority IN ('High', 'Medium', 'Low')) DEFAULT 'Medium',
                due_date TEXT,
                due_time TEXT,
                recurring TEXT DEFAULT 'None',
                is_done INTEGER DEFAULT 0,
                is_draft INTEGER DEFAULT 0,
                done_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
                FOREIGN KEY (list_id) REFERENCES lists(id) ON DELETE SET NULL
            )
        """)
        
        # Create task_tags junction table

        # Insert default admin user if not exists
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, first_name, last_name, email, password, role)
            VALUES ('admin', 'Admin', 'User', 'admin@taskly.com', 'admin123', 'admin')
        """)

        conn.commit()
        print("✅ Database initialized successfully!")
        print(f"📁 Database created at: {DB_PATH}")
        
        # Show created tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("\n📋 Tables created:")
        for table in tables:
            print(f"   - {table['name']}")

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    initialize_db()