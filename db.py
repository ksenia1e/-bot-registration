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
            qr_received INTEGER DEFAULT 0,
            checked_in  INTEGER DEFAULT 0
        )
                         """)
        await db.commit()

async def add_user(user_id: int, user_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, user_name) VALUES (?, ?)",
                         (user_id, user_name)
        )
        await db.commit()

async def set_full_name(user_id: int, full_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET full_name = ? WHERE user_id = ?",
                         (full_name, user_id)
        )
        await db.commit()

async def set_phone(user_id: int, phone: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET phone = ? WHERE user_id = ?",
                         (phone, user_id)
        )
        await db.commit()

async def if_registered(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE user_id = ? AND full_name NOT NULL AND phone NOT NULL",
                                 (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] > 0
    
async def get_user_role(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT role FROM users WHERE user_id = ?",
                                  (user_id,)
        )
        row = await cursor.fetchone()
        return row[0]