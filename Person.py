from agentscope.agents import AgentBase
from typing import Optional, Union, Any, Callable
from enums import InfectionLevel, HealthLevel
from Resource import Resource
from Virus import Virus
from agentscope.message import Msg
from utils import send_chat_msg, send_role_status
from utils import SYS_MSG_PREFIX, COMMON_STATUS, COMMON_RESOURCE, MEDICINE, RELATION
from utils import HealthLevel_TEXT, InfectionLevel_TEXT, WearingMask_TEXT, RelationLevel_TEXT
from agentscope.prompt import PromptType, PromptEngine
import time
import random

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
        if self.physicalHealth == HealthLevel.DEAD:
            send_chat_msg(f" {SYS_MSG_PREFIX}{self.name}因饥饿而死亡。", uid=self.uid)
            self.isDead = True
        elif self.mindHealth == HealthLevel.DEAD:
            send_chat_msg(f" {SYS_MSG_PREFIX}{self.name}因心理不健康而自杀。", uid=self.uid)
            self.isDead = True
        elif self.infection == InfectionLevel.DEAD:
            send_chat_msg(f" {SYS_MSG_PREFIX}{self.name}因感染{self.virus.name}而死亡。", uid=self.uid)
            self.isDead = True
        else:
            self.isDead = False
     
    def self_introduction(self):
        send_chat_msg("**speak**", role=self.name, uid=self.uid, avatar=self.avatar)
        
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

    def welcome(self) -> Msg:
        send_chat_msg("**speak**", role=self.name, uid=self.uid, avatar=self.avatar)
        
        if self.relations[0].level == 1:
            hint = self.sys_prompt + f'你与玩家的熟悉程度是{RelationLevel_TEXT[self.relations[0].level]}，你需要根据熟悉程度生成一段欢迎的话，并且开启一个话题。'
        else:
            hint = f'你与玩家的熟悉程度是{RelationLevel_TEXT[self.relations[0].level]}，你需要根据熟悉程度生成一段欢迎的话，并且开启一个话题。'
        prompt = self.engine.join(hint,self.memory.get_memory())
        response = self.model(prompt, max=3)
        send_chat_msg(response.text, role=self.name, uid=self.uid, avatar=self.avatar)
        msg = Msg(
            name=self.name,
            content=response.text
        )
        return msg
    
    def reply(self, x: dict = None) -> dict:
        if x is not None:
            self.memory.add(x)
        content = x.get("content")
        time.sleep(0.5)
        if self.name != '玩家':
            send_chat_msg("**speak**", role=self.name, uid=self.uid, avatar=self.avatar)
            
            prompt = self.engine.join(
                content,
                self.memory.get_memory()
            )
            response = self.model(prompt, max=3)
            send_chat_msg(response.text, role=self.name, uid=self.uid, avatar=self.avatar)
            content = response.text
        msg = Msg(
            self.name,
            content=content
        )
        return msg

    def add_resource(self, item: str) -> Msg:
        item_arr = item.split(":")
        item_name = item_arr[0]
        item_count = int(item_arr[1])
        
        send_chat_msg("**speak**", role=self.name, uid=self.uid, avatar=self.avatar)

        hint = f"""现在要判断一个物品的属于哪个类别。
        例子1
        食物 食物
        例子2
        面包 食物
        例子3
        N95 口罩
        例子4
        口罩 口罩
        例子5
        青霉素 盘尼西林
        例子6
        奥司他韦 奥司他韦
        例子7
        RNA RNA疫苗
        例子8
        强力消毒液 强力消毒液
        请在food, mask, 盘尼西林, 奥司他韦, RNA疫苗, 强力消毒液这六个类别内返回，并且只返回类别名称。
        """
        prompt = self.engine.join(
            hint + "\n" + item_name
        )
        response = self.model(prompt, max=3)
        res_str = response.text
        print("------判断物资类型------" + res_str)
        if res_str == "食物":
            res_str = "food"
        elif res_str == "口罩":
            res_str = "mask"

        if res_str == "food":
            self.resource.inc_food(item_count)
            res_str = "***success***"
        elif res_str == "mask":
            self.resource.inc_mask(item_count)
            res_str = "***success***"
        elif res_str in ["盘尼西林", "奥司他韦", "RNA疫苗", "强力消毒液"]:
            self.resource.inc_medicine(res_str, item_count)
            res_str = "***success***"
        else:
            err_hint = f"因为没有判断清楚对方给的到底是食物、口罩还是要皮，说一句要重新购买的话，并且告诉对方给出的是{res_str}。"
            prompt = self.engine.join(
                err_hint
            )
            response = self.model(prompt, max=3)
            res_str = response.text
        
        msg = Msg(
            name=self.name,
            role="user",
            content=res_str
        )

        return msg

    def gen_random_resource(self):
        # 获得随机数量的资源，暂定十个以内
        pass
    
    def set_medicine_status(self, medicine_status):
        self.medicine_status = medicine_status

    def virus_growing(self):
        if self.infection != InfectionLevel.CLEAN and self.infection != InfectionLevel.DEAD:
            self.infection = InfectionLevel(self.infection + 1)

    def update_status(self):
        common_status = [
            ["感染程度", InfectionLevel_TEXT[self.infection]],
            ["健康程度", HealthLevel_TEXT[self.physicalHealth]],
            ["精神状况", HealthLevel_TEXT[self.mindHealth]],
            ["佩戴口罩", WearingMask_TEXT[self.isWearingMask]],
        ]
        send_role_status(self.name, COMMON_STATUS, common_status, self.uid)

        common_resource = [
            ["食物数量", self.resource.get_food()],
            ["口罩数量", self.resource.get_mask()],
        ]
        send_role_status(self.name, COMMON_RESOURCE, common_resource, self.uid)

        medicine = []
        for medicine_key in self.resource.medicine:
            medicine.append([medicine_key, self.resource.medicine[medicine_key]])
        send_role_status(self.name, MEDICINE, medicine, self.uid)

        relation = []
        for rel in self.relations :
            relation.append([rel.person2.name, RelationLevel_TEXT[rel.level]])
        send_role_status(self.name, RELATION, relation, self.uid)

# 玩家
class User(Person):
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
        super().__init__(name, sys_prompt, model_config_name, infection, resource, virus, avatar, uid)
    
    def set_medicine_status(self, medicine_status: dict):
        self.medicine_status = medicine_status
    
    def gen_random_resource(self):
        resourceType = random.randint(1, 3)
        resourceSum = random.randint(1, 9)
        # 生成食物
        if resourceType == 1:
            print(self.name + " 获得随机数量食物：" + str(resourceSum))
            self.resource.inc_food(resourceSum)
        # 生成
        elif resourceType == 2:
            print(self.name + " 获得随机口罩：" + str(resourceSum))
            self.resource.inc_mask(resourceSum)
        else:
            avail_medicine_name = []
            for key in self.medicine_status:
                if self.medicine_status[key] == "Y":
                    avail_medicine_name.append(key)    
            medicine_name = avail_medicine_name[random.randint(0, len(avail_medicine_name) - 1)]
        
            randint = random.randint(1, 9)
            print(self.name + " 获得随机药品：" + medicine_name + " " + str(randint))
            self.resource.inc_medicine(medicine_name, randint)
            
    def doResearch(self):
        pass


# NPC1，拥有商场职员背景
class MallStaff(Person):
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
        super().__init__(name, sys_prompt, model_config_name, infection, resource, virus, avatar, uid)
    
    def gen_random_resource(self):
        randint = random.randint(1, 9)
        print(self.name + " 获得随机数量食物：" + str(randint))
        self.resource.inc_food(randint)


# NPC2，拥有药店职员背景
class DrugstoreStaff(Person):
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
        super().__init__(name, sys_prompt, model_config_name, infection, resource, virus, avatar, uid)
    
    def gen_random_resource(self):
        randint = random.randint(1, 9)
        print(self.name + " 获得随机口罩：" + str(randint))
        self.resource.inc_mask(randint)


# NPC3 拥有医生背景
class Doctor(Person):
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
        super().__init__(name, sys_prompt, model_config_name, infection, resource, virus, avatar, uid)
    
    def set_medicine_status(self, medicine_status: dict):
        self.medicine_status = medicine_status
    
    def gen_random_resource(self):
        avail_medicine_name = []
        for key in self.medicine_status:
            if self.medicine_status[key] == "Y":
                avail_medicine_name.append(key)    
        medicine_name = avail_medicine_name[random.randint(0, len(avail_medicine_name) - 1)]
        
        randint = random.randint(1, 9)
        print(self.name + " 获得随机药品：" + medicine_name + " " + str(randint))
        self.resource.inc_medicine(medicine_name, randint)


if __name__ == "__main__":
    person = Person(name="reymond")
    print(person.name)