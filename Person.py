from agentscope.agents import AgentBase
from typing import Optional, Union, Any, Callable
from enums import InfectionLevel, HealthLevel
from Resource import Resource
from Virus import Virus
from agentscope.message import Msg
from utils import send_chat_msg
from agentscope.prompt import PromptType, PromptEngine

InfectionLevel_TEXT = {
    0: "Clean",
    1: "Tiny",
    2: "Common",
    3: "Serious",
    4: "Critical",
    5: "Dead"
}
HealthLevel_TEXT = {
    5: "Perfect",
    4: "Good",
    3: "Common",
    2: "Bad",
    1: "Poor",
    0: "Dead"
}
WearingMask_TEXT = {
    True: "已佩戴",
    False: "未佩戴"
}
RelationLevel_TEXT = {
    1: "STRANGE",
    2: "COMMON",
    3: "FAMILIAR",
    4: "INTIMATE"
}
class Person(AgentBase):
    def __init__(
        self, 
        name: str, 
        sys_prompt: str = None, 
        model_config_name: str = None, 
        infection: InfectionLevel = InfectionLevel.CLEAN, 
        resource: Resource = None, 
        virus: Virus = None, 
        avatar: str = "",
        uid: str = None
    ) -> None:
        super().__init__(name, sys_prompt, model_config_name)
        self.engine = PromptEngine(self.model, prompt_type=PromptType.LIST)
        self.infection = infection
        self.resource = resource
        self.virus = virus
        self.avatar = avatar
        self.uid = uid
        
        self._init_status()
    
    def _init_status(self):
        self.physicalHealth = HealthLevel.PERFECT
        self.mindHealth = HealthLevel.PERFECT
        self.isWearingMask = False
        self.isDead = False
        self.relations = []
        
    def die(self):
        pass
    def self_introduction(self) -> Msg:
        start_hint = "请生成一段自我介绍，100字以内。"

        prompt = self.engine.join(
            self.sys_prompt + start_hint,
            self.memory.get_memory()
        )

        response = self.model(prompt, max=3)
        information = (f"我的状态:\n"
                       f"感染程度: {InfectionLevel_TEXT[self.infection]}\n"
                       f"健康程度: {HealthLevel_TEXT[self.physicalHealth]}\n"
                       f"精神状况: {HealthLevel_TEXT[self.mindHealth]}\n"
                       f"佩戴口罩: {WearingMask_TEXT[self.isWearingMask]}\n"
                       f"携带病毒: {'未携带' if self.infection == 0 else self.virus.name}\n"
                       f"食物数量: {self.resource.get_food()}\n"
                       f"口罩数量: {self.resource.get_mask()}\n"
                       f"携带的药品: {self.resource.medicine}\n"
                       )
        for relation in self.relations :
            if relation != '':
                information += f'我和{relation.person2.name}的关系程度是: {RelationLevel_TEXT[relation.level]}\n'
        msg = response.text + '\n' + information
        send_chat_msg(msg, role=self.name, uid=self.uid, avatar=self.avatar)
if __name__ == "__main__":
    person = Person(name="reymond")
    print(person.name)