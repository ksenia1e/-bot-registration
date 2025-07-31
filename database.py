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

        await db.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY,
                name TEXT,
                data TEXT,
                start_time TEXT,
                end_time TEXT,
                place TEXT,
                description TEXT
            )
                        """)
        await db.commit()

        await db.execute("""
            CREATE TABLE IF NOT EXISTS raffle (
                id INTEGER PRIMARY KEY,
                name TEXT,
                data TEXT,
                start_time TEXT,
                end_time TEXT,
                prizes TEXT
            )
                        """)
        await db.commit()

        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_event (
                user_id INTEGER,
                event_id INTEGER,
                PRIMARY KEY (user_id, event_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (event_id) REFERENCES schedule(id) ON DELETE CASCADE
            )
                        """)
        await db.commit()

        await db.execute("""
            CREATE TABLE IF NOT EXISTS event_prize (
                event_id INTEGER,
                prize_id INTEGER,
                PRIMARY KEY (event_id, prize_id),
                FOREIGN KEY (prize_id) REFERENCES raffle(id) ON DELETE CASCADE,
                FOREIGN KEY (event_id) REFERENCES schedule(id) ON DELETE CASCADE
            )
                        """)
        await db.commit()

async def add_user(user_id: int, user_name: str, full_name: str, phone: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO users (user_id, user_name, full_name, phone) VALUES (?, ?, ?, ?)",
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
        if row is None:
            return None
        return row[0]
    
async def get_users():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM users WHERE role = 'user'")
        return await cursor.fetchall()
    
async def add_organizer_(user_id: int, full_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO users (user_id, full_name, role) VALUES (?, ?, 'organizer')",
                         (user_id, full_name)
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

async def get_organizers():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id, full_name FROM users WHERE role = 'organizer'")
        return await cursor.fetchall()
    
async def delete_organizer_(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET role = 'user' WHERE user_id = ?",
                         (user_id,)
        )
        await db.commit()

async def get_users_id_name():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id, user_name FROM users WHERE role = 'user'")
        return await cursor.fetchall()
    
async def get_schedule():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM schedule")
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in await cursor.fetchall()]
    
async def get_raffle():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM raffle")
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in await cursor.fetchall()]
    
async def add_schedule(id: int, name: str, data: str, start_time: str, end_time: str, place: str, description: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO schedule (id, name, data, start_time, end_time, place, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (id, name, data, start_time, end_time, place, description)
        )
        await db.commit()

async def add_raffle(id: int, name: str, data: str, start_time: str, end_time: str, prizes: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO raffle (id, name, data, start_time, end_time, prizes) VALUES (?, ?, ?, ?, ?, ?)",
                         (id, name, data, start_time, end_time, prizes)
        )
        await db.commit()

async def clear_table(table_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(f"DELETE FROM {table_name}")
        await db.commit()

async def add_user_event(user_id: int, event_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        try:
            await db.execute("INSERT INTO user_event (user_id, event_id) VALUES (?, ?)",
                            (user_id, event_id))
            await db.commit()
            return (True,)
        except Exception as e:
            return (False, e)
        
async def get_all_table(table_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(f"SELECT * FROM {table_name}")
        return await cursor.fetchall()