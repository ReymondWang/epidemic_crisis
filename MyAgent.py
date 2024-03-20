from agentscope.agents import AgentBase
from agentscope.prompt import PromptType, PromptEngine
from agentscope.message import Msg
from agentscope.models import ModelResponse
import json

hint = (
    '\n 你应该使用如下格式进行响应，以方便可以在'
    'Python中使用`json.loads`进行加载: '
    '{\n'
    '   "thought":"你想的是什么",\n'
    '   "speak":"你说的是什么"'
    '}'
)

def my_parse_func(response: ModelResponse) -> ModelResponse:
    print("The `my_parse_func ` is called.")
    print(response.text)
    res_json = json.loads(response.text)
    # if "agreement" not in res_json:
    #     raise RuntimeError("Can not find agreement in the response.")
    return ModelResponse(raw=res_json)
    
def my_fault_handler(response: ModelResponse) -> ModelResponse:
    print("The `my_fault_handler` is called.")
    res_json = json.loads(response.text)
    return ModelResponse(raw=res_json)

class MyAgent(AgentBase):
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
            self.sys_prompt + hint,
            self.memory.get_memory()
        )
        
        response = self.model(
            prompt,
            parse_func = my_parse_func,
            fault_handler = my_fault_handler,
            max=3
        )
        
        ret_dict = response.raw
        
        return Msg(self.name, ret_dict["speak"])