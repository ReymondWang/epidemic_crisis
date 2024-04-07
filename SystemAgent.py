import time
import json

from agentscope.agents import AgentBase
from agentscope.prompt import PromptType, PromptEngine
from agentscope.message import Msg
from typing import Optional
from random import randint
from loguru import logger
from utils import send_chat_msg, get_player_input, query_answer
from utils import SYS_MSG_PREFIX
from utils import InfectionLevel_TEXT
from utils import ResetException
from Person import Person, User, MallStaff, DrugstoreStaff, Doctor
from enums import InfectionLevel

class SystemAgent(AgentBase):
    def __init__(
        self, 
        name: str, 
        sys_prompt: str = None, 
        model_config_name: str = None, 
        round_menu_dict: Optional[dict] = None,
        uid: str = None,
    ) -> None:
        super().__init__(name, sys_prompt, model_config_name)
        self.engine = PromptEngine(self.model, prompt_type=PromptType.LIST)
        self.round_menu_dict = round_menu_dict
        self.uid = uid
        self.round_cnt = 0
    
    def set_role_list(self, user: User, person_list: list, place_list: list):
        self.user = user
        self.person_list = person_list
        self.place_list = place_list

    def set_medicine_list(self, medicine_list: list):
        self.medicine_list = medicine_list

    def rand_infection(self):
        """
        游戏开始时随机感染个人或地方
        """
        idx = randint(1, 7)
        if idx == 1:
            self.user.infection = InfectionLevel.TINY
            print("----" + self.user.name + "被感染，当前感染等级" + InfectionLevel_TEXT[InfectionLevel.TINY] + "----")
        elif idx >= 2 and idx <= 4:
            self.person_list[idx - 2].infection = InfectionLevel.TINY
            print("----" + self.person_list[idx - 2].name + "被感染，当前感染等级" + InfectionLevel_TEXT[InfectionLevel.TINY] + "----")
        else:
            self.place_list[idx - 5].infection = InfectionLevel.TINY
            print("----" + self.place_list[idx - 5].name + "被感染，当前感染等级" + InfectionLevel_TEXT[InfectionLevel.TINY] + "----")

    def reply(self, x: dict = None) -> dict:
        # if x is not None:
        #     self.memory.add(x)
            
        content = ""
        time.sleep(0.5)
        while True:
            try:
                print(x)
                if isinstance(x, dict):
                    if x.get("content") == "开始新回合" and content == "":
                        return self.begin_new_round()
                    elif x.get("content") == "查看状态" and content == "":
                        return self.show_inspection_menu()
                    elif x.get("content") == "研发药品" and content == "":
                        return self.show_research_menu()
                    elif x.get("content") == "采购物资" and content == "":
                        return self.show_place_menu()
                    elif x.get("content") == "与村民交谈" and content == "":
                        return self.show_talk_menu()
                    elif "主菜单" in x.get("content") and content == "":
                        return self.show_main_menu()
                    elif x.get("content") == "百货商场" and content == "":
                        content = "百货商场"
                    elif x.get("content") == "使用资源" and content == "":
                        return self.show_use_resource_menu()

                if not hasattr(self, "model") or len(content) == 0:
                    break

                ruler_res = self.is_content_valid(content)
                if ruler_res:
                    break

                send_chat_msg(
                    f" {SYS_MSG_PREFIX}🚫输入被规则禁止"
                    f" {ruler_res.get('reason', '未知原因')}\n"
                    f"请重试",
                    uid=self.uid,
                )
            except ResetException:
                raise
            except Exception as e:
                logger.debug(e)
                send_chat_msg(f" {SYS_MSG_PREFIX}无效输入，请重试！", uid=self.uid)
        
        msg = Msg(
            self.name,
            role="user",
            content=content
        )
        return msg
    
    def is_content_valid(self, content) -> bool:
        total_valid = ["主菜单"]
        for key in self.round_menu_dict:
            for item in self.round_menu_dict[key]:
                total_valid.append(item)
        return content in total_valid
    
    def begin_new_round(self) -> Msg:
        self.round_cnt += 1
        
        self.user.gen_random_resource()
        self.user.virus_growing()
        self.user.die()
        self.user.isWearingMask = False
        self.user.physicalHealth -= 1
        self.user.update_status()
        for person in self.person_list:
            person.gen_random_resource()
            person.eating_food()
            person.wearing_mask()
            person.eating_medicine()
            person.virus_growing()
            person.die()
            person.update_status()
        for place in self.place_list:
            place.virus_growing()

        send_chat_msg("**speak**", role="游戏精灵", uid=self.uid, avatar="./assets/system.png")

        if self.user.isDead:
            dead_hint = "主角已经死亡，请生成一段游戏失败的文字，100字以内"
            prompt = self.engine.join(
                self.sys_prompt + dead_hint,
                self.memory.get_memory()
            )
            response = self.model(prompt, max=3)
            send_chat_msg(response.text, role="游戏精灵", uid=self.uid, avatar="./assets/system.png")
            return Msg(name="user", content="***game over***")
        elif self.is_success():
            success_hint = "成功消灭了瘟疫，请生成一段游戏成功的文字，100字以内"
            prompt = self.engine.join(
                self.sys_prompt + success_hint,
                self.memory.get_memory()
            )
            response = self.model(prompt, max=3)
            send_chat_msg(response.text, role="游戏精灵", uid=self.uid, avatar="./assets/system.png")
            return Msg(name="user", content="***game over***")
        else:
            start_hint = "请生成一个温馨的早上的描述画面，100字以内。"
            prompt = self.engine.join(
                self.sys_prompt + start_hint,
                self.memory.get_memory()
            )
            response = self.model(prompt, max=3)
            send_chat_msg(response.text, role="游戏精灵", uid=self.uid, avatar="./assets/system.png")
            return self.show_main_menu()

    def is_success(self) -> bool:
        if self.round_cnt <= 1:
            return False
        
        is_user_healthy = self.user.infection == InfectionLevel.CLEAN
        is_npc_healthy = True
        for npc in self.person_list:
            if npc.infection != InfectionLevel.CLEAN:
                is_npc_healthy = False
        is_place_clean = True
        for place in self.place_list:
            if place.infection != InfectionLevel.CLEAN:
                is_place_clean = False

        return is_user_healthy & is_npc_healthy & is_place_clean

    def show_main_menu(self) -> Msg:
        choose_menu = f""" {SYS_MSG_PREFIX}请选择想要进行的事项: <select-box shape="card"
                    type="checkbox" item-width="auto"
                options='{json.dumps(self.round_menu_dict["menu"], ensure_ascii=False)}' 
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
        
        return Msg(name="user", content=menu[0])
     
    def show_inspection_menu(self) -> Msg:
        person_list = self.round_menu_dict["inspection"]
        if "主菜单" not in person_list:
            person_list.append("主菜单")
        
        choose_person = f""" {SYS_MSG_PREFIX}请选择想要查看状态的对象: <select-box shape="card" 
            type="checkbox" item-width="auto" 
            options='{json.dumps(person_list, ensure_ascii=False)}' 
            select-once></select-box>"""
            
        send_chat_msg(
            choose_person,
            flushing=False,
            uid=self.uid,
        )
        
        person = []
        while True:
            sel_person = get_player_input(uid=self.uid)
            if isinstance(sel_person, str):
                send_chat_msg(f" {SYS_MSG_PREFIX}请在列表中进行选择。", uid=self.uid)
                continue
            elif sel_person[0] not in person_list:
                send_chat_msg(f" {SYS_MSG_PREFIX}请在列表中进行选择。", uid=self.uid)
                continue
            person = sel_person
            break
        send_chat_msg("**end_choosing**", uid=self.uid)
        content = '查看状态：'+ person[0]
        return Msg(name="user", content=content)
      
    def show_research_menu(self) -> Msg:
        medicine_name_list = []
        for medicine in self.medicine_list:
            if medicine.name not in medicine_name_list and medicine.enable == "N":
                medicine_name_list.append(medicine.name)

        if "主菜单" not in medicine_name_list:
            medicine_name_list.append("主菜单")
        
        choose_medicine = f""" {SYS_MSG_PREFIX}请选择想要研发的药品: <select-box shape="card" 
            type="checkbox" item-width="auto" 
            options='{json.dumps(medicine_name_list, ensure_ascii=False)}' 
            select-once></select-box>"""
            
        send_chat_msg(
            choose_medicine,
            flushing=False,
            uid=self.uid,
        )
        
        medicine = []
        while True:
            sel_medicine = get_player_input(uid=self.uid)
            if isinstance(sel_medicine, str):
                send_chat_msg(f" {SYS_MSG_PREFIX}请在列表中进行选择。", uid=self.uid)
                continue
            medicine = sel_medicine
            break
        send_chat_msg("**end_choosing**", uid=self.uid)
        
        return Msg(name="user", content=medicine[0])
    
    def show_place_menu(self) -> Msg:
        place_list = self.round_menu_dict["place"]
        if "主菜单" not in place_list:
            place_list.append("主菜单")
        
        choose_place = f""" {SYS_MSG_PREFIX}请选择想要采购物资的场所: <select-box shape="card" 
            type="checkbox" item-width="auto" 
            options='{json.dumps(place_list, ensure_ascii=False)}' 
            select-once></select-box>"""
            
        send_chat_msg(
            choose_place,
            flushing=False,
            uid=self.uid,
        )
        
        place = []
        while True:
            sel_place = get_player_input(uid=self.uid)
            if isinstance(sel_place, str):
                send_chat_msg(f" {SYS_MSG_PREFIX}请在列表中进行选择。", uid=self.uid)
                continue
            place = sel_place
            break
        send_chat_msg("**end_choosing**", uid=self.uid)
        
        return Msg(name="user", content=place[0])
    
    def show_talk_menu(self) -> Msg:
        talk_list = self.round_menu_dict["talking"]
        if "主菜单" not in talk_list:
            talk_list.append("主菜单")
        
        choose_talk = f""" {SYS_MSG_PREFIX}请选择想要交谈的对象: <select-box shape="card" 
            type="checkbox" item-width="auto" 
            options='{json.dumps(talk_list, ensure_ascii=False)}' 
            select-once></select-box>"""
            
        send_chat_msg(
            choose_talk,
            flushing=False,
            uid=self.uid,
        )
        
        talk = []
        while True:
            sel_talk = get_player_input(uid=self.uid)
            if isinstance(sel_talk, str):
                send_chat_msg(f" {SYS_MSG_PREFIX}请在列表中进行选择。", uid=self.uid)
                continue
            talk = sel_talk
            break
        send_chat_msg("**end_choosing**", uid=self.uid)
        content = '交谈：' +  talk[0]
        return Msg(name="user", content=content)

    def show_use_resource_menu(self) -> Msg:
        use_resource_list = self.round_menu_dict["using_resource"]
        if "主菜单" not in use_resource_list:
            use_resource_list.append("主菜单")

        choose_resource = f""" {SYS_MSG_PREFIX}请选择想要使用的资源: <select-box shape="card" 
            type="checkbox" item-width="auto" 
            options='{json.dumps(use_resource_list, ensure_ascii=False)}' 
            select-once></select-box>"""

        send_chat_msg(
            choose_resource,
            flushing=False,
            uid=self.uid,
        )

        use_resource = []
        while True:
            sel_use_resource = get_player_input(uid=self.uid)
            if isinstance(sel_use_resource, str):
                send_chat_msg(f" {SYS_MSG_PREFIX}请在列表中进行选择。", uid=self.uid)
                continue
            use_resource = sel_use_resource
            break
        send_chat_msg("**end_choosing**", uid=self.uid)
        return Msg(name="user", content=use_resource[0])
    
if __name__ == "__main__":
    round_menu_dict = {
        "menu": ["研发药品", "采购物资", "与村民交谈"],
        "inspection": ["自己", "小美", "花姐", "凯哥"],
        "research": ["盘尼西林", "奥斯维他", "RNA疫苗", "强力消毒液"],
        "place": ["百货商场", "大药房", "医院"],
        "talking": ["小美", "花姐", "凯哥"]
    }
    
    total_valid = ["主菜单"]
    for key in round_menu_dict:
        for item in round_menu_dict[key]:
            total_valid.append(item)
            
    content = "百货商场"
    val = content in total_valid
    print(val)