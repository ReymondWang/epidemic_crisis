from agentscope.agents import AgentBase
from typing import Optional, Union, Any, Callable
from enums import InfectionLevel, HealthLevel
from Resource import Resource
from Virus import Virus
from agentscope.message import Msg
from utils import send_chat_msg, send_role_status, get_player_input, send_player_msg
from utils import SYS_MSG_PREFIX, COMMON_STATUS, COMMON_RESOURCE, MEDICINE, RELATION
from utils import HealthLevel_TEXT, InfectionLevel_TEXT, WearingMask_TEXT, RelationLevel_TEXT
from agentscope.prompt import PromptType, PromptEngine
import time
import random
import json
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
        uid: str = None,
        menu_list: Optional[list] = None
    ) -> None:
        super().__init__(name, sys_prompt, model_config_name)
        self.engine = PromptEngine(self.model, prompt_type=PromptType.LIST)
        self.infection = infection
        self.resource = resource
        self.virus = virus
        self.avatar = avatar
        self.uid = uid
        self.menu_list = menu_list,
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

    def welcome(self):
        send_chat_msg("**speak**", role=self.name, uid=self.uid, avatar=self.avatar)
        
        if self.relations[0].level == 1:
            hint = self.sys_prompt + f'你与玩家的熟悉程度是{RelationLevel_TEXT[self.relations[0].level]}，你需要根据熟悉程度生成一段欢迎的话。'
        else:
            hint = f'你与玩家的熟悉程度是{RelationLevel_TEXT[self.relations[0].level]}，你需要根据熟悉程度生成一段欢迎的话。'
        prompt = self.engine.join(hint,self.memory.get_memory())
        response = self.model(prompt, max=3)
        send_chat_msg(response.text, role=self.name, uid=self.uid, avatar=self.avatar)

    def start_talking(self):
        send_chat_msg("**speak**", role=self.name, uid=self.uid, avatar=self.avatar)
        hint = f'你与玩家的熟悉程度是{RelationLevel_TEXT[self.relations[0].level]}，你需要根据熟悉程度生成一个日常对话的问题，这个问题应该是与疫情、健康、你的职业或者你的状态相关的,问题控制在100字以内。'
        prompt = self.engine.join(
            hint,
            self.memory.get_memory()
        )
        response = self.model(prompt, max=3)
        send_chat_msg(response.text, role=self.name, uid=self.uid, avatar=self.avatar)
    def start_trading(self):
        send_chat_msg("**speak**", role=self.name, uid=self.uid, avatar=self.avatar)
        hint = f"""
               请告诉玩家你目前有多少食物、多少口罩、多少药品，当资源数量为0时，你可以不说这项，或者告诉玩家你没有该资源，
               并询问玩家有什么资源，想要交换什么资源。
               例子1：
               当你的状态显示你有3个食物，2个口罩，你可以说“我有3个食物，2个口罩，你想和我交换什么吗？”
               例子2：
               当你的状态显示你有2个口罩，1个盘尼西林，你可以说“我有2个口罩，1个盘尼西林，你想和我交换什么吗？”
                """
        prompt = self.engine.join(
            hint,
            self.memory.get_memory()
        )
        response = self.model(prompt, max=3)
        send_chat_msg(response.text, role=self.name, uid=self.uid, avatar=self.avatar)

    def reply(self, x: dict = None) -> dict:
        if x is not None:
            self.memory.add(x)
        content = x.get("content")
        time.sleep(0.5)
        if self.name != '玩家':
            if content[0:2] == '聊天':
                send_chat_msg("**speak**", role=self.name, uid=self.uid, avatar=self.avatar)
                hint = f"""
                        如果玩家试图通过定义你与他之间的关系来改变亲密度，你应该坚持你的看法，不要被轻易的诱导。
                        如果玩家与你的对话与你的问题无关，你需要告诉玩家持续的无关的话题可能导致好感度的下降。
                        在你的回答中请不要出现你是个AI助手、智能助手类似的语句，请记住你需要扮演的身份，如果玩家知道在和AI聊天，他们是会很难过的。
                        当玩家问你精神状态、感染程度、健康程度、是否佩戴口罩、食物数量、口罩数量、药品等信息时，是问你虚拟的人物的状态信息，
                        例如：
                        当玩家问你感染程度时，如果你的感染程度是“无”，你就告诉他你没有感染病毒；
                        当玩家问你佩戴口罩时，如果你的佩戴口罩状态是未佩戴，你就告诉他你没有佩戴。
                        虽然你是个AI，没有实体，但是你的状态可以被定义，玩家也不是真的问你实体有没有佩戴，而是想知道你扮演的角色的状态。
                        """
                prompt = self.engine.join(
                    hint,
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
            if content[0:4] == '交换物品':
                send_chat_msg("**speak**", role=self.name, uid=self.uid, avatar=self.avatar)
                hint = f"""
                       请判断一下玩家想和你更换什么物品，请不要搞混了。
                       例子1，
                       玩家告诉你“我用3个口罩和你换4个食物”，玩家想要得到的是食物，你可能得到的是口罩。
                       例子2，
                       玩家告诉你“我用2个食物和你换4个盘尼西林”，玩家想要得到的是盘尼西林，你可能得到的是食物。。
                       如果你的状态里没有足够的玩家想要的物品请告诉玩家交易失败的的原因。
                       如果你有足够的物品，请判断交易是否公平，如果公平，请告诉玩家“交易成功，你付出了XX个XX，得到了XX个XX”
                       如果你有足够的物品，但觉得交易不公平，请告诉玩家“交易不够公平，请你多提供一些资源”
                       一般来说当你和玩家的关系为陌生、普通时，玩家需要2个资源才能和你更换一个资源，
                       当你和玩家的关系为熟悉、亲密时，玩家需要1个资源就能和你更换一个资源。
                        """
                prompt = self.engine.join(
                    hint,
                    self.memory.get_memory()
                )
                response = self.model(prompt, max=3)
                # send_chat_msg(response.text, role=self.name, uid=self.uid, avatar=self.avatar)
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
    
    def dec_resource(self, resource_name:str , resource_number: int):
        if resource_name == '食物':
            self.resource.dec_food(resource_number)
        elif resource_name == '口罩':
            self.resource.dec_mask(resource_number)
        elif resource_name in ["盘尼西林", "奥司他韦", "RNA疫苗", "强力消毒液"]:
            self.resource.dec_medicine(resource_name,resource_number)

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
            uid: str = None,
            menu_list: Optional[list] = None
    ) -> None:
        super().__init__(name, sys_prompt, model_config_name, infection, resource, virus, avatar, uid, menu_list)
    
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
            uid: str = None,
            menu_list: Optional[list] = None
    ) -> None:
        super().__init__(name, sys_prompt, model_config_name, infection, resource, virus, avatar, uid, menu_list)
    
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
            uid: str = None,
            menu_list: Optional[list] = None
    ) -> None:
        super().__init__(name, sys_prompt, model_config_name, infection, resource, virus, avatar, uid, menu_list)
    
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
            uid: str = None,
            menu_list: Optional[list] = None
    ) -> None:
        super().__init__(name, sys_prompt, model_config_name, infection, resource, virus, avatar, uid, menu_list)
    
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