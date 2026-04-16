import asyncio
import sys
import os
import time
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

CONCURRENCY = 3

async def main():
    from db import AsyncSessionLocal
    from sqlalchemy import select, update
    from models.material import Material
    from tasks.v2_analyze import analyze_material
    from services.ai.client import llm_client

    llm_client._fallback_until = time.time() + 3600
    logger.info("Forced fallback model for all calls")

    user_id = os.environ.get("BATCH_USER_ID")
    if not user_id:
        logger.error("BATCH_USER_ID environment variable required")
        return

    target_ids = []
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Material).where(
                Material.user_id == user_id,
                Material.analysis_status == "pending",
            )
        )
        materials = result.scalars().all()
        target_ids = [m.id for m in materials]
        for m in materials:
            logger.info(f"  {m.name}")

    if not target_ids:
        logger.info("No pending materials found")
        return

    logger.info(f"Starting {len(target_ids)} analyses with concurrency={CONCURRENCY}")

    sem = asyncio.Semaphore(CONCURRENCY)
    results = {"success": 0, "failed": 0}

    async def run_one(mid):
        async with sem:
            try:
                await asyncio.wait_for(analyze_material(mid), timeout=600)
                results["success"] += 1
                logger.info(f"DONE: {mid[:8]}")
            except asyncio.TimeoutError:
                results["failed"] += 1
                logger.error(f"TIMEOUT: {mid[:8]}")
                async with AsyncSessionLocal() as db:
                    await db.execute(
                        update(Material)
                        .where(Material.id == mid)
                        .values(analysis_status="failed", analysis_error="分析超时")
                    )
                    await db.commit()
            except Exception as e:
                results["failed"] += 1
                logger.error(f"ERROR: {mid[:8]} - {e}")
                async with AsyncSessionLocal() as db:
                    await db.execute(
                        update(Material)
                        .where(Material.id == mid)
                        .values(analysis_status="failed", analysis_error=str(e)[:200])
                    )
                    await db.commit()

    start = time.time()
    await asyncio.gather(*[run_one(mid) for mid in target_ids])
    elapsed = time.time() - start
    logger.info(f"All done in {elapsed:.0f}s — success={results['success']}, failed={results['failed']}")

if __name__ == "__main__":
    asyncio.run(main())
