import aiosqlite

DB_NAME = "users.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            user_name TEXT,
            full_name TEXT,
            phone TEXT,
            role TEXT DEFAULT 'user',
            checked_in  INTEGER DEFAULT 0
        )
                         """)
        await db.commit()

async def add_user(user_id: int, user_name: str, full_name: str, phone: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, user_name, full_name, phone) VALUES (?, ?, ?, ?)",
                         (user_id, user_name, full_name, phone)
        )
        await db.commit()

async def if_registered(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE user_id = ?",
                                 (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] > 0
    
async def get_user_role(user_id: int) -> str:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT role FROM users WHERE user_id = ?",
                                  (user_id,)
        )
        row = await cursor.fetchone()
        return row[0]
    
async def get_users():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM users WHERE role = 'user'")
        rows = await cursor.fetchall()
        return rows
    
async def add_organizer_(user_id: int, user_name: str, full_name: str, phone: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO users (user_id, user_name, full_name, phone, role) VALUES (?, ?, ?, ?, 'organizer')",
                         (user_id, user_name, full_name, phone)
        )
        await db.commit()

async def get_number_of_users_():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE role = 'user'")
        row = await cursor.fetchone()
        return row[0]
    
async def get_checked_in(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT checked_in FROM users WHERE user_id = ?",
                         (user_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return row[0]
    
async def set_checked_in(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET checked_in = 1 WHERE user_id = ?",
                         (user_id,)
        )
        await db.commit()