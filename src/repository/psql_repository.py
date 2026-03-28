from typing import Any, Generic, Sequence, Type, TypeVar

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.db.postgres import Base
from repository.abstract_repository import Repository

ModelType = TypeVar('ModelType', bound=Base)  # type: ignore
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)


class RepositoryPsql(
    Repository,
    Generic[ModelType, CreateSchemaType],
):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self._model = model
        self._session = session

    async def delete(
        self,
        db_obj: ModelType,
    ):
        await self._session.delete(db_obj)
        await self._session.commit()
        return db_obj

    async def get(self, obj_id: Any) -> ModelType | None:
        statement = select(self._model).where(self._model.id == obj_id)
        results = await self._session.execute(statement=statement)
        return results.scalar_one_or_none()

    async def get_multi(self, *, skip=0, limit=100) -> Sequence[ModelType]:
        statement = select(self._model).offset(skip).limit(limit)
        results = await self._session.execute(statement=statement)
        return results.scalars().all()

    async def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self._model(**obj_in_data)
        self._session.add(db_obj)
        await self._session.commit()
        return db_obj
