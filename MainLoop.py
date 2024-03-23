from utils import SYS_MSG_PREFIX
from utils import send_chat_msg

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