import os
import gradio as gr

from multiprocessing import Queue
from collections import defaultdict
from dataclasses import dataclass
from typing import List
from Medicine import Medicine

SYS_MSG_PREFIX = '【系统】'
DEFAULT_AGENT_IMG_DIR = "./assets/"
DEFAULT_DATA_DIR = "./data/"

COMMON_STATUS = "common_status"
COMMON_RESOURCE = "common_resource"
MEDICINE = "medicine"
RELATION = "relation"

InfectionLevel_TEXT = {
    0: "无",
    1: "轻微",
    2: "一般",
    3: "严重",
    4: "非常严重",
    5: "致死"
}
HealthLevel_TEXT = {
    5: "非常好",
    4: "好",
    3: "一般",
    2: "差",
    1: "特别差",
    0: "死亡"
}
WearingMask_TEXT = {
    True: "已佩戴",
    False: "未佩戴"
}
RelationLevel_TEXT = {
    1: "陌生",
    2: "普通",
    3: "熟悉",
    4: "亲密"
}

def init_uid_queues():
    return {
        "glb_queue_chat_msg": Queue(),
        "glb_queue_chat_input": Queue(),
    }

def init_role_status_dict():
    return {}

def init_medicine_dict():
    return {}

glb_medicine_dict = defaultdict(init_medicine_dict)
glb_uid_dict = defaultdict(init_uid_queues)
user_role_status_dict = defaultdict(init_role_status_dict)

def cycle_dots(text: str, num_dots: int = 3) -> str:
    # 计算当前句尾的点的个数
    current_dots = len(text) - len(text.rstrip('.'))
    # 计算下一个状态的点的个数
    next_dots = (current_dots + 1) % (num_dots + 1)
    if next_dots == 0:
        # 避免 '...0', 应该是 '.'
        next_dots = 1
    # 移除当前句尾的点，并添加下一个状态的点
    return text.rstrip('.') + '.' * next_dots

def check_uuid(uid):
    if not uid or uid == '':
        if os.getenv('MODELSCOPE_ENVIRONMENT') == 'studio':
            raise gr.Error('请登陆后使用! (Please login first)')
        else:
            uid = 'local_user'
    return uid

def get_medicine(uid):
    uid = check_uuid(uid=uid)
    global glb_medicine_dict
    if uid in glb_medicine_dict:
        return glb_medicine_dict[uid]
    else:
        medicine_list, _ = Medicine.builtin_medicines()
        glb_medicine_dict[uid] = medicine_list
        return medicine_list

def get_chat_msg(uid=None):
    global glb_uid_dict
    glb_queue_chat_msg = glb_uid_dict[uid]["glb_queue_chat_msg"]
    if not glb_queue_chat_msg.empty():
        line = glb_queue_chat_msg.get(block=False)
        if line is not None:
            return line
    return None

def send_chat_msg(
    msg,
    role=None,
    uid=None,
    flushing=False,
    avatar="./assets/bot.jpg",
    id=None,
):
    print("send_chat_msg:", msg)
    global glb_uid_dict
    glb_queue_chat_msg = glb_uid_dict[uid]["glb_queue_chat_msg"]

    if "💡" in msg or "📜" in msg:
        msg = f"<div style='background-color: rgba(255, 255, 0, 0.1);'" \
                f">{msg}</div>"

    if "🚫" in msg:
        msg = f"<div style='background-color: rgba(255, 0, 0, 0.1);'" \
                f">{msg}</div>"

    glb_queue_chat_msg.put(
        [
            None,
            {
                "text": msg,
                "name": role,
                "flushing": flushing,
                "avatar": avatar,
                "id": id,
            },
        ],
    )

def send_player_msg(
    msg,
    role="我",
    uid=None,
    flushing=False,
    avatar="./assets/user.jpg",
):
    print("send_player_msg:", msg)
    global glb_uid_dict
    glb_queue_chat_msg = glb_uid_dict[uid]["glb_queue_chat_msg"]
    glb_queue_chat_msg.put(
        [
            {
                "text": msg,
                "name": role,
                "flushing": flushing,
                "avatar": avatar,
            },
            None,
        ],
    )
    
def send_player_input(msg, uid=None):
    global glb_uid_dict
    glb_queue_chat_input = glb_uid_dict[uid]["glb_queue_chat_input"]
    glb_queue_chat_input.put([None, msg])
    
def get_player_input(name=None, uid=None):
    global glb_uid_dict
    print("wait queue input")
    glb_queue_chat_input = glb_uid_dict[uid]["glb_queue_chat_input"]
    content = glb_queue_chat_input.get(block=True)[1]
    print(content)
    if content == "**Reset**":
        glb_uid_dict[uid] = init_uid_queues()
        raise ResetException 
    return content

def query_answer(questions: List, key="ans", uid=None):
    return get_player_input(uid=uid)

def send_role_status(role: str, type: str, data: list[list], uid: str=None):
    uid = check_uuid(uid)
    print(f"send_role_status: role->{role}, type->{type}, data->{data}, uid->{uid}")
    global user_role_status_dict
    if uid not in user_role_status_dict:
        user_role_status_dict[uid] = {}
    if role not in user_role_status_dict[uid]:
        user_role_status_dict[uid][role] = {}
    user_role_status_dict[uid][role][type] = data

def get_role_status(role: str, type: str, uid: str=None) -> List[List]:
    uid = check_uuid(uid)
    print(f"get_role_status: role->{role}, type->{type}, uid->{uid}")
    
    global user_role_status_dict
    if uid not in user_role_status_dict:
        user_role_status_dict[uid] = {}
    if role not in user_role_status_dict[uid]:
        user_role_status_dict[uid][role] = {}
    
    if type not in user_role_status_dict[uid][role]:
        print(f"get_role_status: None")
        return [[]]
    else:
        ret = user_role_status_dict[uid][role][type]
        print(f"get_role_status: {ret}")
        return ret

def get_wiki_content(name, uid):
    uid = check_uuid(uid)
    content = ""
    unlocked = False
    medicine_list = get_medicine(uid)
    for medicine in medicine_list:
        if medicine.name == name:
            unlocked = medicine.enable == "Y"
            break
    if unlocked:
        with open(os.path.join(DEFAULT_DATA_DIR, name + ".md"), mode="r") as file:
            content = file.read()
    else:
        content = f"{name}尚没有解锁😅，请在药品研发中努力解锁吧💪"
    return content

@dataclass
class CheckpointArgs:
    load_checkpoint: str = None
    save_checkpoint: str = "./checkpoints/cp-"    

class ResetException(Exception):
    pass

if __name__ == "__main__":
    glb_uid_dict = defaultdict(init_uid_queues)
    data = [["感染程度", "无"],["健康程度", "非常好"],["精神状况", "非常好"],["佩戴口罩", "无"],]
    send_role_status("user", "common", data, uid="local")
    print(get_role_status("user", type="common", uid="local"))