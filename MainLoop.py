import time
import json
import inquirer
import sys
from random import randint, random
from SystemAgent import SystemAgent
from Resource import Resource
from Virus import Virus
from Place import Place
from Medicine import Medicine
from Person import Person, MallStaff, DrugstoreStaff, Doctor, User
from enums import InfectionLevel, EffectLevel, RelationLevel
from utils import SYS_MSG_PREFIX
from utils import InfectionLevel_TEXT
from utils import send_chat_msg, send_player_msg, send_player_input, get_player_input
from agentscope.message import Msg
from Relation import Relation

#----定义药品相关的信息 start----
medicine_status = {
    "盘尼西林": "Y",
    "奥司他韦": "Y",
    "RNA疫苗": "Y",
    "强力消毒液": "Y"
}

penicillin = Medicine(
    name="盘尼西林",
    effect=EffectLevel.POOR,
    price=2,
    researchCnt=2
)

osweita = Medicine(
    name="奥司他韦",
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

disinfection = Medicine(
    name="强力消毒液",
    effect=EffectLevel.GOOD,
    price=6,
    researchCnt=6
)

medicine_dic = {
    "盘尼西林": penicillin,
    "奥司他韦": osweita,
    "RNA疫苗": rna,
    "强力消毒液": disinfection,
}

#----定义药品相关的信息 end----

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

#----定义主要环节的互动方法 start----

def infect(obj1: any, obj2: any):
    source = None
    target = None

    infection1 = obj1.infection
    infection2 = obj2.infection
    if infection1 != InfectionLevel.CLEAN and infection2 == InfectionLevel.CLEAN:
        source = obj1
        target = obj2
    elif infection1 == InfectionLevel.CLEAN and infection2 != InfectionLevel.CLEAN:
        source = obj2
        target = obj1
    
    if source != None and target != None:
        infection_chance = {
            InfectionLevel.CLEAN: 0,
            InfectionLevel.TINY: 0.2,
            InfectionLevel.COMMON: 0.4,
            InfectionLevel.SERIOUS: 0.6,
            InfectionLevel.CRITICAL: 0.8,
            InfectionLevel.DEAD: 1
        }
        chance = infection_chance[source.infection]
        if random() < chance:
            print(f"----{target.name}被{source.name}感染了病毒，当前的感染等级为{InfectionLevel_TEXT[InfectionLevel.TINY]}----")
            target.infection = InfectionLevel.TINY
    

def place_loop(place: Place, user: Person, uid):
    """
    针对场所的主要循环，负责用户和各个场所的互动。
    """
    place.welcome()
    infect(place, user)
    
    msg = place.show_main_menu()
    while True:
        msg = place(msg)
        if msg.get("content") == "***kill_virus***":
            medicine_name = show_available_medicine(uid)
            if user.resource.get_medicine(medicine_name) > 0:
                san_res = place.sanitize(medicine_dic[medicine_name])
                if san_res:
                    user.resource.dec_medicine(medicine_name, cnt=1)
            else:
                send_chat_msg(f" {SYS_MSG_PREFIX}您没有要使用的药物。", uid=uid)
            break
        elif msg.get("content") == "***end***":
            break
        elif isinstance(msg.get("content"), dict):
            item_dict = msg.get("content")
            print("----判断数量结果----")
            print(item_dict)
            if "Y" == item_dict.get("success"):
                item = item_dict.get("content")
                msg = user.add_resource(item)
                user.update_status()
                print("----增加资源返回结果----")
                print(msg)
    return Msg(
            name=place.name,
            role="user",
            content="主菜单"
        )


def inspection_loop(person: Person, uid, SystemAgent):
    """
    针对人员查看状态的主要循环，负责用户查看各个角色的状态信息。
    """
    person.self_introduction()
    return SystemAgent.show_main_menu()


def talk_loop(person: Person, user: Person, uid, SystemAgent):
    """
    针对人员对话的主要循环，负责用户与各个角色，并根据对话结果提升亲密度。
    """
    msg = person.welcome()
    infect(person, user)
    Assistance_Msg = f"""
                    {SYS_MSG_PREFIX}您当前与{person.name}的关系为：{person.relations[0].level.name}\n
                    如果您想结束当前对话请输入：结束对话
                    """
    send_chat_msg(Assistance_Msg, uid=uid)
    while True:
        msg = Msg(name='user',content=get_player_input(uid=user.uid))
        if msg.get("content") == '结束对话' :
            break
        else:
            msg = person(msg)
    relation_hint = f"""
                    请根据你和玩家的对话记忆，判断目前你和玩家的关系的亲密程度，亲密程度包含四个等级，四个等级的亲密程度是依次递增的，
                    分别是"STRANGE,COMMON,FAMILIAR,INTIMATE"，
                    你需要告诉我的内容是"STRANGE,COMMON,FAMILIAR,INTIMATE"其中的一个，不要包含其他无关的信息。
                    """
    prompt = person.engine.join(
            relation_hint,
        person.memory.get_memory()
    )
    response = person.model(prompt, max=3)
    if response.text in ["STRANGE", "COMMON", "FAMILIAR", "INTIMATE"]:
        person.relations[0].level = RelationLevel[response.text]
        for relation in user.relations:
            if relation.person2.name == person.name:
                relation.level = RelationLevel[response.text]
        person.update_status()
    return SystemAgent.show_main_menu()


def show_available_medicine(uid):
    """
    显示用户当前可以使用的药品
    """
    medicine_list = []
    for key in medicine_status:
        if medicine_status[key] == "Y":
            medicine_list.append(key)
    choose_medicine = f""" {SYS_MSG_PREFIX}请选择要使用: <select-box shape="card" 
        type="checkbox" item-width="auto" 
        options='{json.dumps(medicine_list, ensure_ascii=False)}' 
        select-once></select-box>"""
    send_chat_msg(
        choose_medicine,
        flushing=False,
        uid=uid,
    )
    medicine = []
    while True:
        sel_medicine = get_player_input(uid=uid)
        if isinstance(sel_medicine, str):
            send_chat_msg(f" {SYS_MSG_PREFIX}请在列表中进行选择。", uid=uid)
            continue
        medicine = sel_medicine
        break
    send_chat_msg("**end_choosing**", uid=uid)
    send_player_msg(msg=medicine[0], uid=uid)
    
    return medicine[0]
            
#----定义主要环节的互动方法 start----

def main_loop(args) -> None:
    """
    游戏的主要循环，负责推进整体的游戏进程。
    """
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
        "menu": ["研发药品", "采购物资", "与村民交谈", "开始新回合"],
        "inspection": ["自己", "小美", "花姐", "凯哥"],
        "research": ["盘尼西林", "奥司他韦", "RNA疫苗", "强力消毒液"],
        "place": ["百货商场", "大药房", "医院"],
        "talking": ["小美", "花姐", "凯哥"]
    }
    
    #----系统Agent start----
    systemAgent = SystemAgent(
        name="小精灵", 
        model_config_name="qwen-max", 
        sys_prompt="你是一个游戏的系统控制角色，负责推进游戏的进行，并且生成一些相关背景。",
        round_menu_dict=round_menu_dict,
        uid=args.uid
    )
    #----系统Agent end----
    
    #----场所Agent start----
    place_menu_dict = {
        "mall": ["采购食物", "病毒消杀", "结束"],
        "pharmacy": ["采购口罩", "病毒消杀", "结束"],
        "hospital": ["采购药品", "病毒消杀", "结束"],
    }
    
    mall = Place(
        name="百货商场",
        model_config_name="qwen-max",
        sys_prompt="你是一个百货商场的经营人员，商场主要售卖各种食物，总是热情的欢迎所有客人。",
        menu_list=place_menu_dict["mall"],
        resource=Resource(food=sys.maxsize),
        virus=place_virus,
        avatar="./assets/mall.jpg",
        uid=args.uid
    )
    
    pharmacy = Place(
        name="大药房",
        model_config_name="qwen-max",
        sys_prompt="你是一个药店的经营人员，药店主要售卖各种口罩，总是热情的欢迎所有来买药的人。",
        menu_list=place_menu_dict["pharmacy"],
        resource=Resource(mask=sys.maxsize),
        virus=place_virus,
        avatar="./assets/pharmacy.jpg",
        uid=args.uid
    )
    
    hospital = Place(
        name="医院",
        model_config_name="qwen-max",
        sys_prompt="你是一个医院的导诊台护士，医院里可以买到各类药品，总是非常耐心的解答所有病人的问题。",
        menu_list=place_menu_dict["hospital"],
        resource=Resource(),
        virus=place_virus,
        avatar="./assets/hospital.jpg",
        uid=args.uid
    )
    
    hospital.gen_resource(medicine_status)
    
    place_dic = {
        "百货商场": mall,
        "大药房": pharmacy,
        "医院": hospital,
    }
    place_list = [mall, pharmacy, hospital]
    #----场所Agent end----
    
    #----人员Agent start----
    beauty = MallStaff(
        name="小美",
        model_config_name="qwen-max",
        sys_prompt="你是一个心地善良的女生，性格活泼开朗，曾经在百货商场上过一段时间班。",
        resource=Resource(),
        virus=people_virus,
        avatar="./assets/npc1.jpg",
        uid=args.uid
    )
    
    flower = DrugstoreStaff(
        name="花姐",
        model_config_name="qwen-max",
        sys_prompt="你是一个中年女性，随让脾气有些刻板，但是生活很幸福，曾经在大药房上过一段时间班。",
        resource=Resource(),
        virus=people_virus,
        avatar="./assets/npc2.jpg",
        uid=args.uid
    )
    
    king = Doctor(
        name="凯哥",
        model_config_name="qwen-max",
        sys_prompt="你是一个中年男性，是一个竟然非常丰富的内科医生，曾经有一个女儿，但是很不幸两年前离婚了，女儿跟着妈妈走了。",
        resource=Resource(),
        virus=people_virus,
        avatar="./assets/npc3.jpg",
        uid=args.uid
    )
    king.set_medicine_status(medicine_status)
    
    npc_dict = {
        "小美": beauty,
        "花姐": flower,
        "凯哥": king
    }
    
    person_list = [beauty, flower, king]
    user = User(
        name="玩家",
        model_config_name="qwen-max",
        sys_prompt="你是游戏玩家在该游戏里的化身，是一名科学家，能够研发出新的药品对付病毒。",
        resource=Resource(),
        virus=people_virus,
        avatar="./assets/user.jpg",
        uid=args.uid
    )
    user.set_medicine_status(medicine_status)
    
    for person in person_list :
        person.relations = [Relation(person, user, RelationLevel.STRANGE)]
        user.relations.append(Relation(user, person, RelationLevel.STRANGE))
    #----人员Agent end----
    
    #------游戏开始------
    systemAgent.set_role_list(user = user, person_list = person_list, place_list = place_list)
    systemAgent.rand_infection()
    msg = systemAgent.begin_new_round()
    while True:
        msg = systemAgent(msg)
        content = msg.get("content")
        if content == "***game over***":
            break
        if content in place_dic:
            msg = place_loop(place_dic[content], user, uid=args.uid)
        if '查看状态' in content:
            if content[5:] in npc_dict :
                msg = inspection_loop(npc_dict[content[5:]], uid=args.uid, SystemAgent=systemAgent)
            if content[5:] == '自己' :
                msg = inspection_loop(user, uid=args.uid, SystemAgent=systemAgent)
        if '交谈' in content:
            if content[3:] in npc_dict :
                msg = talk_loop(npc_dict[content[3:]], user, uid=args.uid, SystemAgent=systemAgent)