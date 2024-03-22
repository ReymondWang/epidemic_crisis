import time
import json
import inquirer
import sys
from SystemAgent import SystemAgent
from Resource import Resource
from Virus import Virus
from Place import Place
from Medicine import Medicine
from Person import Person
from enums import InfectionLevel, EffectLevel
from utils import SYS_MSG_PREFIX
from utils import send_chat_msg, send_player_msg, send_player_input
from agentscope.message import Msg

def place_loop(place: Place, uid):
    place.welcome()
    msg = place.show_main_menu()
    while True:
        msg = place(msg)
        if msg.get("content") == "***end***":
            break
    return Msg(
            role="user",
            content="主菜单"
        )
    

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
        "research": ["盘尼西林", "奥斯维他", "RNA疫苗", "强力消毒液"],
        "place": ["百货商场", "大药房", "医院"],
        "talking": ["小美", "花姐", "凯哥"]
    }
    
    #----定义病毒相关的信息 start----
    place_infection_feature = {
        InfectionLevel.CLEAN: "无任何病毒，零污染。",
        InfectionLevel.TINY: "存在少量新冠病毒污染，无明显特征。",
        InfectionLevel.COMMON: "存在病毒，有少量人员出现发热、干咳、乏力、肌肉或关节疼痛、喉咙痛、失去嗅觉或味觉。",
        InfectionLevel.SERIOUS: "存在较多病毒，有较多人员出现发热、干咳等症状，有少量人员症状严重。",
        InfectionLevel.CRITICAL: "存在大量病毒，有很多症状严重的人员，甚至有人死亡。",
        InfectionLevel.DEAD: "大量人员死亡，简直是人间地域。"
    }
    people_infection_feature = {
        InfectionLevel.CLEAN: "完全没有感染，非常健康。",
        InfectionLevel.TINY: "病毒潜伏期，没有明显症状或有非常轻微的症状，包括轻微乏力、肌肉酸痛、轻微的消化道症状（如恶心、腹泻）或者极轻微的发热等",
        InfectionLevel.COMMON: "症状初发期，体温升高，通常是38℃以上，干咳，乏力或身体不适。",
        InfectionLevel.SERIOUS: "症状严重期，呼吸困难，表现为呼吸急促、喘息、氧气饱和度下降等， 肺炎症状：胸痛、咳嗽加重，咳出黄绿色痰液，肺部影像学检查显示有肺炎样病变。",
        InfectionLevel.CRITICAL: "症状非常严重，有多器官功能损害，包概括心肌损伤、肾功能异常、肝脏随让，神经系统并发症，并伴有休克、血压急剧降低、循环衰竭等。",
        InfectionLevel.DEAD: "患者死亡"
    }
    virus_descption = f"""
        新冠病毒（SARS-CoV-2），即导致COVID-19疾病的病毒，主要具有以下特征：
        1、传播性强：新冠病毒具有高度传染性，能够在人际间快速传播，尤其在密闭、人员聚集的空间内传播风险更高。
        传播途径包括但不限于呼吸道飞沫传播、接触传播（接触被病毒污染的物体表面再触摸口鼻眼）、以及可能存在的气溶胶传播。
        2、潜伏期较长：感染后的潜伏期一般为1-14天，平均约为3-7天，有些病例潜伏期可能会更长，在潜伏期内就有可能传染给他人。
        3、传染人群广泛：几乎所有年龄段的人都易感，尽管老年人和有基础疾病的人群更易发展为重症，但任何人都可能成为感染者。
        随着疫苗接种的推进，已接种疫苗的人群即使感染，通常症状较轻或者无症状。
        4、临床症状多样性：新冠病毒感染的症状可以从轻微到严重，轻症患者可能仅有轻微发热、乏力、干咳、喉咙痛、肌肉或关节疼痛、头痛、味觉或嗅觉丧失等。
        而重症患者可能出现呼吸急促、低氧血症、肺炎、急性呼吸窘迫综合症、多器官功能障碍，甚至死亡。
        """
    
    place_virus = Virus(
        name="新冠病毒",
        description=virus_descption,
        feature_dict=place_infection_feature
    )
    people_virus = Virus(
        name="新冠病毒",
        description=virus_descption,
        feature_dict=people_infection_feature
    )
    #----定义病毒相关的信息 end----
    
    #----定义药品相关的信息 start----
    medicine_status = {
        "penicillin": "Y",
        "osweita": "N",
        "rna": "N",
        "disinfectant": "N"
    }
    
    penicillin = Medicine(
        name="盘尼西林",
        effect=EffectLevel.POOR,
        price=2,
        researchCnt=2
    )
    osweita = Medicine(
        name="奥斯维他",
        effect=EffectLevel.COMMON,
        price=4,
        researchCnt=4
    )
    rna = Medicine(
        name="RNA疫苗",
        effect=EffectLevel.GOOD,
        price=6,
        researchCnt=6
    )
    medicine_dic = {
        "penicillin": penicillin,
        "osweita": osweita,
        "rna": rna
    }
    
    #----定义药品相关的信息 end----
    
    #----系统Agent start----
    systemAgent = SystemAgent(
        name="小精灵", 
        model_config_name="qwen_72b", 
        sys_prompt="你是一个游戏的系统控制角色，负责推进游戏的进行，并且生成一些相关背景。",
        round_menu_dict=round_menu_dict,
        uid=args.uid
    )
    #----系统Agent end----
    
    #----场所Agent start----
    mall = Place(
        name="百货商场",
        model_config_name="qwen_72b",
        sys_prompt="你是一个百货商场的经营人员，总是热情的欢迎所有客人。",
        menu=["采购食物", "病毒消杀"],
        resource=Resource(food=sys.maxsize),
        virus=place_virus,
        avatar="./assets/mall.jpg",
        uid=args.uid
    )
    pharmacy = Place(
        name="大药房",
        model_config_name="qwen_72b",
        sys_prompt="你是一个药店的经营人员，总是热情的欢迎所有来买药的人。",
        menu=["采购口罩", "病毒消杀"],
        resource=Resource(mask=sys.maxsize),
        virus=place_virus,
        avatar="./assets/pharacy.jpg",
        uid=args.uid
    )
    hospital = Place(
        name="医院",
        model_config_name="qwen_72b",
        sys_prompt="你是一个医院的导诊台护士，总是非常耐心的解答所有病人的问题。",
        menu=["采购药品", "病毒消杀"],
        resource=Resource(),
        virus=place_virus,
        avatar="./assets/pharacy.jpg",
        uid=args.uid
    )
    hospital.gen_resource(medicine_status)
    
    place_dic = {
        "mall": mall,
        "pharmacy": pharmacy,
        "hospital": hospital,
    }
    #----场所Agent end----
    
    #----人员Agent start----
    beauty = Person(
        name="小美",
        model_config_name="qwen_72b",
        sys_prompt="你是一个心地善良的女生，性格活泼开朗，曾经在百货商场上过一段时间班。",
        resource=Resource(),
        virus=people_virus,
        avatar="./assets/npc1.jpg",
        uid=args.uid
    )
    
    flower = Person(
        name="花姐",
        model_config_name="qwen_72b",
        sys_prompt="你是一个中年女性，随让脾气有些刻板，但是生活很幸福，曾经在大药房上过一段时间班。",
        resource=Resource(),
        virus=people_virus,
        avatar="./assets/npc2.jpg",
        uid=args.uid
    )
    
    king = Person(
        name="凯哥",
        model_config_name="qwen_72b",
        sys_prompt="你是一个中年男性，是一个竟然非常丰富的内科医生，曾经有一个女儿，但是很不幸两年前离婚了，女儿跟着妈妈走了。",
        resource=Resource(),
        virus=people_virus,
        avatar="./assets/npc3.jpg",
        uid=args.uid
    )
    
    npc_dict = {
        "beauty": beauty,
        "flower": flower,
        "king": king
    }
    #----人员Agent end----
    
    msg = systemAgent.begin_new_round()
    while True:
        msg = systemAgent(msg)
        content = msg.get("content")
        if content in place_dic:
            msg = place_loop(place_dic[content], uid=args.uid)
            
    