from Medicine import Medicine
from agentscope.agents import AgentBase
from agentscope.message import Msg
import time
import json
from random import randint
from utils import send_chat_msg, get_player_input
from agentscope.prompt import PromptType, PromptEngine


class Research(AgentBase):
    """
    medicine: 本次需要研发的药品
    cur_cnt: 完成了几个回合
    """

    def __init__(
            self,
            name: str,
            sys_prompt: str = None,
            model_config_name: str = None,
            avatar: str = "",
            uid: str = None
    ) -> None:
        super().__init__(name, sys_prompt, model_config_name)
        self.engine = PromptEngine(self.model, prompt_type=PromptType.LIST)
        self.avatar = avatar
        self.uid = uid

    def set_medicine(self, medicine: Medicine):
        self.medicine = medicine

    def ask_question(self) -> dict:
        send_chat_msg("**speak**", role=self.name, uid=self.uid, avatar=self.avatar)

        category, question = self.get_random_question()
        json_format = "{'correct_answer':'A' 'answers':[{'letter':'A', 'statement':'选项内容'}]}"
        hint=f"""请针对{self.medicine.name}的{category}方面的问题{question}。
            请生成A、B、C三个选项，其中两个错误的一个正确的，并且以以下的json的格式返回。
            {json_format}
            """
        prompt = self.engine.join(self.sys_prompt + hint)
        response = self.model(prompt, max=3)
        question_json = json.loads(self.purify_response(response_text=response.text))
        self.correct_answer = question_json["correct_answer"]
        answers = question_json["answers"]
        options = ""
        for option in answers:
            options += option["letter"] + "：" + option["statement"] + "\n"

        question_text = f"{question}\n请在以下选项中选择：\n{options}"
        send_chat_msg(question_text, role=self.name, uid=self.uid, avatar=self.avatar)
        
        content = get_player_input(uid=self.uid)

        msg = Msg(
            self.name,
            role="user",
            content=content
        )
        return msg

    def reply(self, x: dict = None) -> dict:
        content = x.get("content")
        if content == "结束":
            content="***end***"
        else:
            send_chat_msg("**speak**", role=self.name, uid=self.uid, avatar=self.avatar)

            is_correct = self.generate_jud_resp_prompt(content)
            if is_correct:
                self.medicine.inc_cur_cnt()
                if self.medicine.effect == "Y":
                    self.finish_researching()
                    content="***end***"
                else:
                    self.send_respose_msg(True)
                    return self.ask_question()
            else:
                self.send_respose_msg(False)
                content = get_player_input(uid=self.uid)

        msg = Msg(
            self.name,
            role="user",
            content=content
        )
        return msg

    # 为某一个 Medicine 生成问题，此处只返回判断答案的 Prompt. 由环境 Agent 调用, -- 可能要修改
    def generate_jud_resp_prompt(self, answer):
        if answer not in ["A", "B", "C"]:
            send_chat_msg("请在A、B、C选项中进行选择。", role=self.name, uid=self.uid, avatar=self.avatar)
            return False
        else:
            return answer == self.correct_answer
    
    def send_respose_msg(self, result):
        if result:
            hint = f"玩家的问题回答正确，说一段奖励的话，并进入下一回合研发，50字以内。"
        else:
            hint = f"玩家的问题回答错误，说一段安慰的话，并鼓励继续努力，50字以内。"
        
        prompt = self.engine.join(
            self.sys_prompt + hint,
            self.memory.get_memory()
        )
        response = self.model(prompt, max=3)
        send_chat_msg(response.text, role=self.name, uid=self.uid, avatar=self.avatar)

    def finish_researching(self):
        hint = f"药品{self.medicine.name}已经已经研发成功，请说一段奖励的话，50字以内。"
        prompt = self.engine.join(
            self.sys_prompt + hint,
            self.memory.get_memory()
        )
        response = self.model(prompt, max=3)
        send_chat_msg(response.text, role=self.name, uid=self.uid, avatar=self.avatar)

    def get_random_question(self):
        categories = []
        for key in self.medicine.question:
            categories.append(key)
        
        this_key = categories[randint(0, len(categories) - 1)]
        this_questions = self.medicine.question[this_key]
        this_question = this_questions[randint(0, len(this_questions) - 1)]
        return this_key, this_question
    
    def purify_response(self, response_text:str):
        print(f"----原始问题:{response_text}----")
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}")
        purified = response_text[start_idx : end_idx + 1]
        print(f"----净化后问题:{purified}----")
        return purified