import time
import json
import inquirer

from agentscope.agents import AgentBase
from agentscope.prompt import PromptType, PromptEngine
from agentscope.message import Msg
from typing import Optional, Any
from loguru import logger
from utils import send_chat_msg, get_player_input, query_answer
from utils import SYS_MSG_PREFIX
from utils import ResetException


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
        
    def reply(self, x: dict = None) -> dict:
        if x is not None:
            self.memory.add(x)
            
        content = ""
        time.sleep(0.5)
        while True:
            try:
                print(x)
                if x == {"content": "新回合开始"} and content == "":
                    self.begin_new_round()
                    continue
                elif isinstance(x, dict):
                    if x.get("content") == "查看状态" and content == "":
                        return self.show_inspection_menu()
                    elif x.get("content") == "研发药品" and content == "":
                        return self.show_research_menu()
                    elif x.get("content") == "采购物资" and content == "":
                        return self.show_place_menu()
                    elif x.get("content") == "与村民交谈" and content == "":
                        return self.show_talk_menu()
                    elif x.get("content") == "主菜单" and content == "":
                        return self.show_main_menu()
                    elif x.get("content") == "百货商场" and content == "":
                        content = "百货商场"

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
        start_hint = "请生成一个温馨的早上的描述画面，300字以内。"
        
        prompt = self.engine.join(
            self.sys_prompt + start_hint,
            self.memory.get_memory()
        )
        
        response = self.model(prompt, max=3)
        send_chat_msg(response.text, role="小精灵", uid=self.uid, avatar="./assets/system.png")
        
        return self.show_main_menu()
        
    
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
            person = sel_person
            break
        send_chat_msg("**end_choosing**", uid=self.uid)
        
        return Msg(name="user", content=person[0])
    
    
    def show_research_menu(self) -> Msg:
        medicine_list = self.round_menu_dict["research"]
        medicine_list.append("主菜单")
        
        choose_medicine = f""" {SYS_MSG_PREFIX}请选择想要研发的药品: <select-box shape="card" 
            type="checkbox" item-width="auto" 
            options='{json.dumps(medicine_list, ensure_ascii=False)}' 
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
        
        return Msg(name="user", content=talk[0])
    
    
if __name__ == "__main__":
    round_menu_dict = {
        "menu": ["查看状态", "研发药品", "采购物资", "与村民交谈"],
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