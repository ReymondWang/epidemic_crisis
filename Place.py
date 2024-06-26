from agentscope.agents import AgentBase
from agentscope.prompt import PromptType, PromptEngine
from agentscope.message import Msg

from typing import Optional
from enums import InfectionLevel, EffectLevel
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
from utils import InfectionLevel_TEXT


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

    def set_medicine_list(self, medicine_list:list):
        self.medicine_list = medicine_list

    def reply(self, x: dict = None) -> dict:
        # if x is not None:
        #     self.memory.add(x)

        content = x.get("content")
        print("----Place收到的消息----")
        print(x)
        time.sleep(0.5)
        while True:
            if "采购" in content:
                self.purchase_item_name = content[2:4]
                if self.name == "医院":
                    medicine_name_list = []
                    for medicine in self.medicine_list:
                        if medicine.enable == "Y":
                            medicine_name_list.append(medicine.name)
                    medicine_name = ", ".join(medicine_name_list)    
                    send_chat_msg(f" {SYS_MSG_PREFIX}你可以输入购买xx个{self.purchase_item_name}，现在可用药品有{medicine_name}。结束购物请输入“结束”", uid=self.uid)
                else:
                    send_chat_msg(f" {SYS_MSG_PREFIX}你可以输入购买xx个{self.purchase_item_name}。结束购物请输入“结束”", uid=self.uid)
                content = self.send_chat(hint= f"请说一句欢迎{content}的话，并询问客人要买多少，50字以内")
            elif content == "病毒消杀":
                content = "***kill_virus***"
            elif content == "结束":
                content = "***end***"
            elif content == "***success***":
                content = self.send_chat(hint= f"请说一句采购{self.purchase_item_name}成功，感谢惠顾的话，50字以内")
            elif content == "未知物品":
                content = self.send_chat(hint= f"请说一句你没有客人要购买的物品的话，并告诉客人你卖的是{self.purchase_item_name}，请客人重新购买，50字以内")
            else:
                res = self.get_number(content)
                if res["success"] == "Y":
                    content = res
                else:
                    send_chat_msg(res["content"], role=self.name, uid=self.uid, avatar=self.avatar)
                    content = get_player_input(uid=self.uid)
            break

        msg = Msg(
            self.name,
            role="user",
            content=content
        )
        return msg

    def send_chat(self, hint):
        print(f"----send_chat, hit:{hint}----")
        send_chat_msg("**speak**", role=self.name, uid=self.uid, avatar=self.avatar)
        
        prompt = self.engine.join(self.sys_prompt + hint)
        response = self.model(prompt, max=3)
        send_chat_msg(response.text, role=self.name, uid=self.uid, avatar=self.avatar)
        user_input = get_player_input(uid=self.uid)
        return user_input
    
    def send_chat_no_reply(self, hint):
        send_chat_msg("**speak**", role=self.name, uid=self.uid, avatar=self.avatar)

        prompt = self.engine.join(
            self.sys_prompt + hint,
            self.memory.get_memory()
        )
        response = self.model(prompt, max=3)
        send_chat_msg(response.text, role=self.name, uid=self.uid, avatar=self.avatar)
    
    def get_number(self, content) -> dict:
        send_chat_msg("**speak**", role=self.name, uid=self.uid, avatar=self.avatar)
        
        hint = f"""现在需要从一句话中获取用户想要购买东西的数量。
        例子1
        我要购买10个食物
        食物:10
        例子2
        我要购买10个苹果
        苹果:10
        例子3
        我要购买5个口罩
        口罩:5
        例子4
        我要购买2个N95口罩
        口罩:2
        例子4
        我要购买5盒盘尼西林
        盘尼西林:5
        请用以下格式返回
        名称:数量
        """
        prompt = self.engine.join(
            hint + "\n" + content
        )
        response = self.model(prompt, max=3)
        res_str = response.text
        print("------判断数量------" + response.text)
        try:
            if res_str.startswith("名称"):
                res_copy = res_str
                res_copy_arr = res_copy.split(",")
                name = res_copy_arr[0].split(":")[1]
                count = res_copy_arr[1].split(":")[1]
                res_str = name + ":" + count
        except Exception:
            res_str = "未知物品"
        res = {}
        if ":" in res_str:
            item_name = res_str.split(":")[0]
            item_number = res_str.split(":")[1]
            category, is_correct = self.get_resource_type(item_name)
            if is_correct:
                res["success"] = "Y"
                res["content"] = category + ":" + item_number
            else:
                res["success"] = "N"
                res["content"] = category
        else:
            res["success"] = "N"
            res["content"] = res_str
        
        return res

    def get_resource_type(self, item_name):
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
        请在食物, 口罩, 盘尼西林, 奥司他韦, RNA疫苗, 强力消毒液这六个类别内返回，并且只返回类别名称。
        """

        medicine_name_list = []
        if self.name == "医院":
            for medicine in self.medicine_list:
                if medicine.enable == "Y":
                    medicine_name_list.append(medicine.name)

        prompt = self.engine.join(
            hint + "\n" + item_name
        )
        response = self.model(prompt, max=3)
        res_str = response.text

        print("------判断物资类型------" + res_str)

        if self.name == "百货商场":
            if res_str == "食物":
                return res_str, True
            else:
                return "对不起，我们只销售食物。", False
        if self.name == "大药房":
            if res_str == "口罩":
                return res_str, True
            else:
                return "对不起，我们只销售口罩。", False
        if self.name == "医院":
            if res_str in medicine_name_list:
                return res_str, True
            else:
                medicine_str = ", ".join(medicine_name_list)
                return f"对不起，我们只销售{medicine_str}.", False

    def welcome(self) -> Msg:
        send_chat_msg("**speak**", role=self.name, uid=self.uid, avatar=self.avatar)
        
        start_hint = "请根据生成一段欢迎词，要稍微体现出场所的感染程度" + InfectionLevel_TEXT[self.infection] + "，100字以内。"

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

    def sanitize(self, medicine: Medicine) -> Msg:
        # 实现对 infection 的控制，根据药物的 effect 对 infection 进行减少
        if medicine.name not in ["强力消毒液"]:
            self.send_chat_no_reply(hint= f"解释一下，场所消杀不能使用人吃的药物，50字以内。")
            return False
        
        reduction = {
            EffectLevel.POOR: 1,
            EffectLevel.COMMON: 2,
            EffectLevel.GOOD: 4
        }
        res = False
        if self.infection.value > 0:
            self.infection -= reduction[medicine.effect]
            if self.infection < 0:
                self.infection = 0
            res = True
        if res:
            self.send_chat_no_reply(hint= f"你的感染的到了缓解，说一句感谢的话，50字以内。")
        else:
            self.send_chat_no_reply(hint= f"强调你并没有被感染，不需要病毒消杀，50字以内。")
        return res

    def virus_growing(self):
        if self.infection != InfectionLevel.CLEAN and self.infection != InfectionLevel.DEAD:
            self.infection = InfectionLevel(self.infection + 1)

    def gen_resource(self, medicine_list: list):
        resource = Resource()
        medicine = {}
        for med in medicine_list:
            if med.enable == "Y":
                medicine[med.name] = sys.maxsize
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
