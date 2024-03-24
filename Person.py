from agentscope.agents import AgentBase
from typing import Optional, Union, Any, Callable
from enums import InfectionLevel, HealthLevel
from Resource import Resource
from Virus import Virus
from agentscope.message import Msg
from utils import send_chat_msg
import random
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
        for relation in self.relations:
            if relation != '':
                information += f'我和{relation.person2.name}的关系程度是: {RelationLevel_TEXT[relation.level]}\n'
        msg = response.text + '\n' + information
        send_chat_msg(msg, role=self.name, uid=self.uid, avatar=self.avatar)

    def add_resource(self, item: str) -> Msg:
        item_arr = item.split(":")
        item_name = item_arr[0]
        item_count = int(item_arr[1])

        hint = f"""现在要判断一个物品的属于哪个类别。
        例子1
        食物
        food
        例子2
        面包
        food
        例子3
        N95
        mask
        例子4
        口罩
        mask
        例子5
        青霉素
        盘尼西林
        例子6
        奥司他韦
        奥斯他韦
        例子7
        RNA
        RNA疫苗
        例子7
        强力消毒液
        强力消毒液
        请在food, mask, 盘尼西林, 奥斯他韦, RNA疫苗, 强力消毒液这六个类别内返回，并且只返回类别名称。如果不能判断出是哪个类别，则返回未知物品。
        """
        prompt = self.engine.join(
            hint + "\n" + item_name
        )
        response = self.model(prompt, max=3)
        res_str = response.text
        print("------判断物资类型------" + res_str)
        if res_str == "food":
            self.resource.inc_food(item_count)
            res_str = "***success***"
        elif res_str == "mask":
            self.resource.inc_mask(item_count)
            res_str = "***success***"
        elif res_str in ["盘尼西林", "奥斯他韦", "RNA疫苗", "强力消毒液"]:
            self.resource.inc_medicine(res_str, item_count)
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


# 玩家
class User(Person):
    def gen_random_resource(self):
        resourceType = random.randint(1, 3)
        resourceSum = random.randint(1, 9)
        # 生成食物
        if resourceType == 1:
            print(self.name + " 获得随机数量食物：" + resourceSum)
            self.resource.inc_food(resourceSum)
        # 生成
        elif resourceType == 2:
            print(self.name + " 获得随机口罩：" + resourceSum)
            self.resource.inc_mask(resourceSum)
        else:
            # FIXME 仅可获取已研发完成的药物
            medicine_name = ""
            randint = random.randint(1, 9)
            print(self.name + " 获得随机药品：" + medicine_name + " " + randint)
            self.resource.inc_medicine(medicine_name, randint)
    def doResearch(self):
        pass




#
class MallStaff(Person):
    def gen_random_resource(self):
        randint = random.randint(1, 9)
        print(self.name + " 获得随机数量食物：" + randint)
        self.resource.inc_food(randint)


class DrugstoreStaff(Person):
    def gen_random_resource(self):
        randint = random.randint(1, 9)
        print(self.name + " 获得随机口罩：" + randint)
        self.resource.inc_food(randint)


# NPC3 医生
class Doctor(Person):
    def gen_random_resource(self):
        # FIXME 仅可获取已研发完成的药物
        medicine_name = ""
        randint = random.randint(1, 9)
        print(self.name + " 获得随机药品：" + medicine_name + " " + randint)
        self.resource.inc_medicine(medicine_name, randint)


if __name__ == "__main__":
    person = Person(name="reymond")
    print(person.name)
