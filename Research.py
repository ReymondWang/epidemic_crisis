from Medicine import Medicine
from agentscope.agents import AgentBase
from agentscope.message import Msg
import time
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
        
        hint=f"帮我对这个药物生成知识问答型问题。药物名称是：{self.medicine.name}。请只生成一个问题。你生成的问题是："
        prompt = self.engine.join(
            self.sys_prompt + hint,
            self.memory.get_memory()
        )
        response = self.model(prompt, max=3)
        self.question = response.text

        # 将已经问过的问题添加到memory中
        self.memory.add(response.text)

        send_chat_msg(response.text, role=self.name, uid=self.uid, avatar=self.avatar)
        user_input = get_player_input(uid=self.uid)

        msg = Msg(
            self.name,
            role="user",
            content=user_input
        )
        return msg

    def reply(self, x: dict = None) -> dict:
        content = x.get("content")
        if content == "结束":
            content="***end***"
        else:
            send_chat_msg("**speak**", role=self.name, uid=self.uid, avatar=self.avatar)

            is_correct = self.generate_jud_resp_prompt(content)
            if is_correct == "是":
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
        print(f"----判断问题【{self.question}】的答案【{answer}】是否正确----")
        
        hint = f"已知当前的问题是{self.question}，请判断答案{answer}是否正确，你只能返回是或否。"
        prompt = self.engine.join(
            self.sys_prompt + hint,
            self.memory.get_memory()
        )
        response = self.model(prompt, max=3)
        print(f"----答案判断为{response.text}----")
        return response.text
    
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