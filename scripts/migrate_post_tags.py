import asyncio

from sqlalchemy import inspect
from sqlalchemy import text

from app.core.config import engine


async def migrate_post_tags():
    async with engine.begin() as conn:
        has_tag_column = await conn.run_sync(
            lambda sync_conn: any(
                column["name"] == "tag"
                for column in inspect(sync_conn).get_columns("posts")
            )
        )
        if has_tag_column:
            print("posts.tag column already exists")
        else:
            await conn.execute(
                text("ALTER TABLE posts ADD COLUMN tag VARCHAR(20) NOT NULL DEFAULT '野钓'")
            )
            print("Added posts.tag column")


if __name__ == "__main__":
    asyncio.run(migrate_post_tags())
