# backend/services/behavior_interpreter_service.py
from datetime import datetime, timedelta
from app.services import user_state_service
from app.utils.bkt import update_bkt_model  # BKT算法实现

class BehaviorInterpreterService:
    def __init__(self):
        self.profile_cache = {}
    
    def interpret_event(self, event_data: dict):
        """解释原始事件并触发领域事件（严格遵循流程图步骤7-11）"""
        # 获取用户当前状态（流程图步骤5-6）
        participant_id = event_data["participant_id"]
        profile = self._get_user_profile(participant_id)
        
        # 根据事件类型应用规则（流程图步骤7）
        if event_data["event_type"] == "test_submission":
            self._interpret_test_submission(participant_id, event_data, profile)
        elif event_data["event_type"] == "ai_help_request":
            self._interpret_ai_request(participant_id, event_data, profile)
        # 其他事件类型的解释规则可以在这里添加
        
    def _get_user_profile(self, participant_id: str):
        """获取用户状态（使用缓存优化性能）"""
        if participant_id not in self.profile_cache:
            self.profile_cache[participant_id] = user_state_service.get_profile(participant_id)
        return self.profile_cache[participant_id]
    
    def _interpret_test_submission(self, participant_id: str, event_data: dict, profile: dict):
        """解释测试提交事件（PRD挫败感规则实现）"""
        # 获取事件详情
        passed = event_data["event_data"].get("passed", False)
        
        # 应用挫败感检测规则（流程图步骤7）
        is_frustrated = self._check_frustration(profile, event_data["timestamp"])
        
        # 如果判定挫败，则触发领域事件（流程图步骤8-11）
        if is_frustrated and not passed:
            # 更新挫败状态（流程图步骤9）
            user_state_service.handle_frustration_event(participant_id)
            
            # 更新BKT模型（流程图步骤10-11）
            topic_id = event_data["event_data"].get("topic_id")
            if topic_id:
                update_bkt_on_submission(participant_id, topic_id, passed)
    
    def _check_frustration(self, profile: dict, event_time: datetime) -> bool:
        """检查挫败状态（严格遵循PRD规则）"""
        # 规则1: 获取过去2分钟内的提交记录
        submissions = [s for s in profile.get("submissions", []) 
                       if event_time - s["timestamp"] <= timedelta(minutes=2)]
        
        # 规则2: 检查是否满足最小提交次数
        if len(submissions) < 3:
            return False
            
        # 规则3: 计算错误率
        error_count = sum(1 for s in submissions if not s.get("passed", False))
        error_rate = error_count / len(submissions)
        
        # 规则4: 计算平均提交间隔
        intervals = [(submissions[i]["timestamp"] - submissions[i-1]["timestamp"]).total_seconds()
                    for i in range(1, len(submissions))]
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        
        # PRD规则：过去2分钟内错误率>75%且提交间隔<10秒
        return error_rate > 0.75 and avg_interval < 10

    def _interpret_ai_request(self, participant_id: str, event_data: dict, profile: dict):
        """解释AI帮助请求（困惑规则实现）"""
        message = event_data["event_data"].get("message", "").lower()
        
        # 简单困惑规则：包含特定关键词
        if any(phrase in message for phrase in ["how", "what", "why", "confused", "don't understand"]):
            user_state_service.handle_confusion_event(participant_id)

# 全局单例服务实例
behavior_interpreter_service = BehaviorInterpreterService()