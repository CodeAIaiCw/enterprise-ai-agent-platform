import asyncio
import os

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


CHECKPOINT_DB_URI = os.getenv(
    "CHECKPOINT_DB_URI",
    "postgresql://postgres:postgres@localhost:5432/enterprise_ai",
)


async def main() -> None:
    async with AsyncPostgresSaver.from_conn_string(
        CHECKPOINT_DB_URI
    ) as checkpointer:
        await checkpointer.setup()

    print("LangGraph checkpoint database initialized.")


if __name__ == "__main__":
    asyncio.run(main())