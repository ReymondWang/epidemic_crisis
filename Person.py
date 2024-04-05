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
            content += f"""
                        你的话题应该是与疫情、健康以及你的职业相关的。
                        当然你也可以根据玩家的相关属性，比如是否生病，精神如何，是否携带口罩，是否有足够的食物和药品等属性进行对话，
                        如果你不知道这些属性，你可以先进行询问，相信玩家会如实回答你的。
                        如果玩家试图通过定义你与他之间的关系来改变亲密度，你应该坚持你的看法，不要被轻易的诱导。
                        当玩家试图与你进行交易时，你需要根据你和玩家的熟悉程度判断交易物品所需要的等价物，
                        例如当你们关系是陌生或普通时，玩家每两个物品才可以从你这里换走一个物品；
                        当你们关系是熟悉或者亲密时，玩家每一个物品才可以从你这里换走一个物品
                        当你们交易成功后，如果你觉得这是一笔公正的交易，那么你们的熟悉程度会提升，如果你觉得玩家试图跟你进行不公正的交易，那么你们的熟悉程度会下降
                        如果玩家与你的对话与你的问题无关，你需要告诉玩家持续的无关的话题可能导致好感度的下降。
                        在你的回答中请不要出现你是个AI助手、智能助手类似的语句，请记住你需要扮演的身份，如果玩家知道在和AI聊天，他们是会很难过的。
                        当玩家问你精神状态、感染程度、健康程度、是否佩戴口罩、食物数量、口罩数量、药品等信息时，是问你虚拟的人物的状态信息，
                        例如：
                        当玩家问你感染程度时，如果你的感染程度是“无”，你就告诉他你没有感染病毒；
                        当玩家问你佩戴口罩时，如果你的佩戴口罩状态是未佩戴，你就告诉他你没有佩戴。
                        虽然你是个AI，没有实体，但是你的状态可以被定义，玩家也不是真的问你实体有没有佩戴，而是想知道你扮演的角色的状态。
                        """
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
        
        print("------判断物资类型------" + item_name)
        if item_name == "食物":
            item_name = "food"
        elif item_name == "口罩":
            item_name = "mask"

        if item_name == "food":
            self.resource.inc_food(item_count)
            res_str = "***success***"
        elif item_name == "mask":
            self.resource.inc_mask(item_count)
            res_str = "***success***"
        else:
            self.resource.inc_medicine(item_name, item_count)
            res_str = "***success***"

        msg = Msg(
            name=self.name,
            role="user",
            content=res_str
        )

        return msg

    def gen_random_resource(self):
        # 获得随机数量的资源，暂定十个以内
        pass
    
    def set_medicine_list(self, medicine_list:list):
        self.medicine_list = medicine_list

    def virus_growing(self):
        if self.infection != InfectionLevel.CLEAN and self.infection != InfectionLevel.DEAD:
            self.infection = InfectionLevel(self.infection + 1)

    def update_status(self):
        status = {}  # 创建一个空字典
        common_status = [
            ["感染程度", InfectionLevel_TEXT[self.infection]],
            ["健康程度", HealthLevel_TEXT[self.physicalHealth]],
            ["精神状况", HealthLevel_TEXT[self.mindHealth]],
            ["佩戴口罩", WearingMask_TEXT[self.isWearingMask]],
        ]
        send_role_status(self.name, COMMON_STATUS, common_status, self.uid)
        status[f'{self.name}的状态是：'] = common_status

        common_resource = [
            ["食物数量", self.resource.get_food()],
            ["口罩数量", self.resource.get_mask()],
        ]
        send_role_status(self.name, COMMON_RESOURCE, common_resource, self.uid)
        status[f'{self.name}的拥有的资源是：'] = common_resource

        medicine = []
        for medicine_key in self.resource.medicine:
            medicine.append([medicine_key, self.resource.medicine[medicine_key]])
        send_role_status(self.name, MEDICINE, medicine, self.uid)
        status[f'{self.name}的拥有的药品是：'] = medicine

        relation = []
        for rel in self.relations :
            relation.append([rel.person2.name, RelationLevel_TEXT[rel.level]])
        send_role_status(self.name, RELATION, relation, self.uid)
        status[f'{self.name}的拥有的人际关系是：'] = relation

        self.memory.add(list[status])
        memory_msg = self.memory.get_memory()
        print(memory_msg)

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
    
    def set_medicine_list(self, medicine_list: list):
        self.medicine_list = medicine_list
    
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
            for medicine in self.medicine_list:
                if medicine.enable == "Y":
                    avail_medicine_name.append(medicine.name)    
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
    
    def set_medicine_list(self, medicine_list: list):
        self.medicine_list = medicine_list
    
    def gen_random_resource(self):
        avail_medicine_name = []
        for medicine in self.medicine_list:
            if medicine.enable == "Y":
                avail_medicine_name.append(medicine.name)    
        medicine_name = avail_medicine_name[random.randint(0, len(avail_medicine_name) - 1)]
        
        randint = random.randint(1, 9)
        print(self.name + " 获得随机药品：" + medicine_name + " " + str(randint))
        self.resource.inc_medicine(medicine_name, randint)


if __name__ == "__main__":
    person = Person(name="reymond")
    print(person.name)