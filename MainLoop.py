import time
import json
import inquirer
from SystemAgent import SystemAgent
from utils import SYS_MSG_PREFIX
from utils import send_chat_msg, query_answer
from agentscope.message import Msg


def main_loop(args) -> None:
    game_description = f"""
    {SYS_MSG_PREFIX}
    这是一款模拟消灭瘟疫的知识问答类文字冒险游戏。
    玩家扮演药物学家，通过与村民和场所互动来推进剧情。
    游戏中玩家可以进行：药品研发，收集资源，与村民聊天等。
    玩家需要通过药物来消灭病毒，并且需要使用食物保持身体健康，与此同时还要有必要的社交活动保持心理健康。
    当所有的玩家、所有村民和场所都没有被感染时，即取得游戏的胜利。
    """
    send_chat_msg(game_description, uid=args.uid)
    
    round_menu_dict = {
        "menu": ["查看状态", "研发药品", "采购物资", "与村民交谈"],
        "inspection": ["自己", "小美", "花姐", "凯哥"],
        "research": ["阿莫西林", "奥斯维他", "RNA疫苗", "强力消毒液"],
        "place": ["百货商场", "大药房", "医院"],
        "talking": ["小美", "花姐", "凯哥"]
    }
    
    systemAgent = SystemAgent(
        name="小精灵", 
        model_config_name="qwen_72b", 
        sys_prompt="你是一个游戏的系统控制角色，负责推进游戏的进行，并且生成一些相关背景。",
        round_menu_dict=round_menu_dict,
        uid=args.uid
    )
    
    msg = systemAgent.begin_new_round()
    print(msg)
    while True:
        msg = systemAgent(msg)
    