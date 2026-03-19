import aiosqlite
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                file_id TEXT NOT NULL,
                file_type TEXT DEFAULT 'video',
                views INTEGER DEFAULT 0,
                added_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                code TEXT,
                found INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def add_movie(code, title, description, file_id, file_type, added_by):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO movies (code, title, description, file_id, file_type, added_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (code.upper(), title, description, file_id, file_type, added_by))
        await db.commit()


async def get_movie(code):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM movies WHERE code = ?", (code.upper(),)
        ) as cursor:
            return await cursor.fetchone()


async def increment_views(code):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE movies SET views = views + 1 WHERE code = ?", (code.upper(),)
        )
        await db.commit()


async def delete_movie(code):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM movies WHERE code = ?", (code.upper(),))
        await db.commit()


async def get_all_movies(limit=20, offset=0):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM movies ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ) as cursor:
            return await cursor.fetchall()


async def get_top_movies(limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM movies ORDER BY views DESC LIMIT ?", (limit,)
        ) as cursor:
            return await cursor.fetchall()


async def count_movies():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM movies") as cursor:
            row = await cursor.fetchone()
            return row[0]


async def upsert_user(user_id, username, full_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (id, username, full_name)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name,
                last_active = CURRENT_TIMESTAMP
        """, (user_id, username, full_name))
        await db.commit()


async def count_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0]


async def get_all_user_ids():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]


async def log_request(user_id, code, found):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO requests (user_id, code, found) VALUES (?, ?, ?)",
            (user_id, code, 1 if found else 0)
        )
        await db.commit()


async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM requests") as c:
            total_requests = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM requests WHERE found=1") as c:
            found_requests = (await c.fetchone())[0]
        async with db.execute(
            "SELECT COUNT(*) FROM requests WHERE date(created_at) = date('now')"
        ) as c:
            today_requests = (await c.fetchone())[0]
    return {
        "total_requests": total_requests,
        "found_requests": found_requests,
        "today_requests": today_requests,
      }
