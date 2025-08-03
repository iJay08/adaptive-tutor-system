# backend/app/api/endpoints/behavior.py
from fastapi import APIRouter, BackgroundTasks, Depends, status  # 修复1：导入status模块
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import behavior_interpreter_service
from app.crud import crud_behavior_event

# 修复2：定义缺失的BehaviorEventCreate模型（临时解决方案）
class BehaviorEventCreate:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        
    def dict(self):
        return self.__dict__

router = APIRouter()

@router.post("/log", status_code=status.HTTP_202_ACCEPTED)  # 修复3：使用正确的status常量
async def log_behavior(
    event_in: BehaviorEventCreate,  # 使用修复后的模型
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # 任务1: 异步持久化原始事件
    background_tasks.add_task(crud_behavior_event.create_behavior_event, db=db, event_in=event_in)
    
    # 任务2: 同步处理事件解释
    behavior_interpreter_service.interpret_event(event_in.dict())
    
    return {"status": "accepted", "message": "Event processing started"}