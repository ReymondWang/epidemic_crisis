from agentscope.agents import AgentBase
from agentscope.prompt import PromptType, PromptEngine
from agentscope.message import Msg

class SystemAgent(AgentBase):
    def __init__(
        self, 
        name: str, 
        sys_prompt: str = None, 
        model_config_name: str = None, 
        use_memory: bool = True, 
        memory_config: dict = None
    ) -> None:
        super().__init__(name, sys_prompt, model_config_name, use_memory, memory_config)
        self.engine = PromptEngine(self.model, prompt_type=PromptType.LIST)
        
    def reply(self, x: dict = None) -> dict:
        if x is not None:
            self.memory.add(x)
            
        prompt = self.engine.join(
            self.sys_prompt,
            self.memory.get_memory()
        )
        
        response = self.model(prompt, max=3)
        return Msg(self.name, response.text)
    
    def start_game(self) -> dict:
        start_hint = "请生成一个逃出瘟疫危机游戏的背景，300字以内。"
        
        prompt = self.engine.join(
            self.sys_prompt + start_hint,
            self.memory.get_memory()
        )
        
        response = self.model(prompt, max=3)
        return Msg(self.name, response.text)
    
    def begin_new_round(self) -> dict:
        new_round_hint = "新的回合开始了,您可以通过回复以下文字进行游戏：\n查看状态\n研发药品\n与朋友交谈\n采购物资"
        return Msg(self.name, new_round_hint)