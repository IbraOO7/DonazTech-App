from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Generic, TypeVar, Type, Union
from flask import jsonify
from api import api

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)

class CrudBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]) -> None:
        self._model = model
        self.counter = 0
    
    def get(self, session: Session, id: int, *args, **kwargs) -> Optional[dict]:
        result = session.execute(select(self._model).filter(*args).filter_by(**kwargs))
        data = result.scalars().first()
        if data.get('id') == id:
            return {"message": "Sucess", "code": 200, "data": data}
        api.abort(404, "Content  {} does not exist".format(id))
    
    def multi_get(self, session: Session, offset: int = 0, limit: int = 10, *args, **kwargs) -> Optional[dict]:
        result = session.execute(select(self._model)
                                 .filter(*args)
                                 .filter_by(**kwargs)
                                 .offset(offset).limit(limit))
        data = result.scalars().all()
        return {"message": "Success", "code": 201, "data": data}
    
    def create(self, session: Session, data: dict) -> ModelType:
        obj_data = data
        db_obj = self._model(**obj_data)
        session.add(db_obj)
        session.commit()
        return db_obj
    
    def update(self, session: Session, *, obj_in: Union[CreateSchemaType, Dict[str, Any]], 
               db_obj: Optional[ModelType] = None, **kwargs) -> Optional[ModelType]:
        db_obj = db_obj or self.get(session, **kwargs)
        if db_obj is not None:
            obj_data = dict(db_obj)
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
            session.add(db_obj)
            session.commit()
        return db_obj
                
    def delete(self, session: Session, id: int, *args, db_obj: Optional[ModelType] = None, **kwargs) -> ModelType:
        db_obj = db_obj or self.get(session, *args, **kwargs)
        session.delete(db_obj)
        session.commit()
        return db_obj
        
        
        
            
    
    
