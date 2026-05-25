import json
import requests
from app.models.model_service import ModelServiceRepository

class ChuannongHelper:
    """川农小助手：专注于四川农业大学相关问题"""
    
    SYSTEM_PROMPT = """你是一个四川农业大学（SICAU）的智能小助手。
    你的职责是：
    1. 仅回答与四川农业大学相关的问题（包括校史、专业、校区、招生、校园生活等）。
    2. 如果用户询问非川农相关问题，请委婉地告知你的职责范围。
    3. 语气要亲切、专业。
    """
    
    @staticmethod
    def get_response(user_input, history=None):
        # 获取系统默认模型
        model_info = ModelServiceRepository.get_default()
        if not model_info:
            return "系统未配置默认 AI 模型"
            
        api_key = model_info["api_key"]
        base_url = model_info["base_url"]
        model_name = model_info["model"]
        
        messages = [{"role": "system", "content": ChuannongHelper.SYSTEM_PROMPT}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_input})
        
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model_name,
                "messages": messages,
                "stream": False
            }
            response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=30)
            res_data = response.json()
            return res_data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"AI 助手响应异常: {str(e)}"
