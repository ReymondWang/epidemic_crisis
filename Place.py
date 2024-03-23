from agentscope.agents import AgentBase
from agentscope.prompt import PromptType, PromptEngine
from agentscope.message import Msg

from typing import Optional
from enums import InfectionLevel,EffectLevel
from Resource import Resource
from Virus import Virus
from Medicine import Medicine
from Person import Person
import sys
import time
import random
import json
from utils import send_chat_msg, get_player_input, send_player_msg
from utils import SYS_MSG_PREFIX

class Place(AgentBase):
    """
    infection: 场所的污染等级
    Resource: 场所存储的资源
    Virus: 场所中存在的病毒
    background: 对应的场所，有商场、药店、医院
    """

    def __init__(
        self, 
        name: str, 
        sys_prompt: str = None, 
        model_config_name: str = None, 
        menu_list: Optional[list] = None,
        infection: InfectionLevel = InfectionLevel.CLEAN, 
        resource: Resource = None, 
        virus: Virus = None, 
        avatar: str = "",
        uid: str = None
    ) -> None:
        super().__init__(name, sys_prompt, model_config_name)
        self.engine = PromptEngine(self.model, prompt_type=PromptType.LIST)
        self.menu_list = menu_list,
        self.infection = infection
        self.resource = resource
        self.virus = virus
        self.avatar = avatar
        self.uid = uid


    def reply(self, x: dict = None) -> dict:
        if x is not None:
            self.memory.add(x)
            
        content = x.get("content")
        time.sleep(0.5)
        while True:
            if content == "采购物资":
                content = self.send_chat(hint="你现在有很多食物，请说一句欢迎采购的话，50字以内")
            elif content == "结束":
                content = "***end***"
            break
        
        msg = Msg(
            self.name,
            role="user",
            content=content
        )
        return msg
    
    
    def send_chat(self, hint):
        prompt = self.engine.join(
            self.sys_prompt + hint,
            self.memory.get_memory()
        )
        response = self.model(prompt, max=3)
        send_chat_msg(response.text, role=self.name, uid=self.uid, avatar=self.avatar)
        user_input = get_player_input(uid=self.uid)
        return user_input
    
    
    def welcome(self) -> Msg:
        start_hint = "请生成一段欢迎词，100字以内。"
        
        prompt = self.engine.join(
            self.sys_prompt + start_hint,
            self.memory.get_memory()
        )
        
        response = self.model(prompt, max=3)
        send_chat_msg(response.text, role=self.name, uid=self.uid, avatar=self.avatar)
        
        
    def show_main_menu(self) -> Msg:        
        choose_menu = f""" {SYS_MSG_PREFIX}请选择想要进行的事项: <select-box shape="card"
                    type="checkbox" item-width="auto"
                options='{json.dumps(self.menu_list[0], ensure_ascii=False)}' 
                select-once></select-box>"""
        send_chat_msg(
            choose_menu,
            flushing=False,
            uid=self.uid,
        )
        
        menu = []
        while True:
            sel_menu = get_player_input(uid=self.uid)
            if isinstance(sel_menu, str):
                send_chat_msg(f" {SYS_MSG_PREFIX}请在列表中进行选择。", uid=self.uid)
                continue
            menu = sel_menu
            break
        send_chat_msg("**end_choosing**", uid=self.uid)
        send_player_msg(menu[0], "我", uid=self.uid)
        
        return Msg(name="user", content=menu[0])
    
        
    def display_info(self):
        print(f"Infection Level: {self.infection}")
        print(f"Resource-food: {self.resource.food}")
        print(f"Resource-mask: {self.resource.mask}")
        print(f"Resource-medicine: {self.resource.medicine}")
        if self.virus is not None:
            print("Virus Info:")
            print(f"Name: {self.virus.name}")
            print(f"Description: {self.virus.description}")


    def sanitize(self, medicine: Medicine):
        # 实现对 infection 的控制，根据药物的 effect 对 infection 进行减少
        reduction = {
            EffectLevel.POOR: 1,
            EffectLevel.COMMON: 2,
            EffectLevel.GOOD: 4
        }
        if self.infection.value > 0:
            self.infection -= reduction[medicine.effect]
            if self.infection < 0 :
                self.infection = 0
            return True
        else:
            print(f"The {self.background}) is clean, you don't need to use medicine to sanitize it.")
            return False


    def infect(self, person: Person):
        # 判定来到场所的人是否会感染病毒
        infection_chance = {
            InfectionLevel.CLEAN: 0,
            InfectionLevel.TINY: 0.2,
            InfectionLevel.COMMON: 0.4,
            InfectionLevel.SERIOUS: 0.6,
            InfectionLevel.CRITICAL: 0.8,
            InfectionLevel.DEAD: 1
        }
        chance = infection_chance[self.infection]
        if random.random() < chance:
            print(f"{person.name} has been infected at {self.background}")


    def gen_resource(self, medicine_dict: dict):
        resource = Resource()
        medicine = {}
        for key, value in medicine_dict.items():
            if value == "Y":
                medicine[key] = sys.maxsize
        resource.medicine = medicine
        self.resource = resource
                

if __name__ == "__main__":
    resource = Resource()  # 实例化 Resource 类
    virus = Virus("Corona", "It is a very terrible virus")  # 实例化 Virus 类
    place = Place(InfectionLevel.DEAD, resource, virus, "market")  # 创建 Place 实例
    place.display_info()


    # 测试 sanitize 方法
    medicine = Medicine(name="盘尼西林", effect=EffectLevel.POOR, price=5, researchCnt=5)
    print("Before sanitize: ", place.infection)
    place.sanitize(medicine)
    print("After sanitize: ", place.infection)

    # 测试 infect 方法
    person = Person(name="reymond")
    place.infect(person)