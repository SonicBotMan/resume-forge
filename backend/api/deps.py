from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_owned(model, item_id: str, user_id: str, db: AsyncSession):
    result = await db.execute(select(model).where(model.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail=f"{model.__name__}不存在")
    if item.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权访问")
    return item
