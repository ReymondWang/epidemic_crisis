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
            medicine: Medicine,
            cur_cnt: int,
            name: str,
            sys_prompt: str = None,
            model_config_name: str = None,
            avatar: str = "",
            uid: str = None
    ) -> None:
        super().__init__(name, sys_prompt, model_config_name)
        self.engine = PromptEngine(self.model, prompt_type=PromptType.LIST)
        self.medicine = medicine
        self.cur_cnt = cur_cnt
        self.avatar = avatar
        self.uid = uid

    def reply(self, x: dict = None) -> dict:
        if x is not None:
            self.memory.add(x)

        content = x.get("content")
        time.sleep(0.5)

        _, name_list = Medicine.builtin_medicines()
        while True:
            if content == "研发药物":
                content = self.send_chat(
                    hint=f"你有很多药物，我要研发这些药物。请说一句欢迎的话，并让我从一些药物中选择我要研发的药物。50字以内。可供研发的药物：{name_list}")
            elif content in name_list:
                content = self.send_chat(
                    hint=f"帮我对这个药物生成知识问答型问题。药物名称是：{content}。你生成的问题是：")
            elif content == "结束":
                content = "***end***"
            break

        msg = Msg(
            self.name,
            role="user",
            content=content
        )
        return msg

    def send_chat(self, hint):
        prompt = self.engine.join(
            self.sys_prompt + hint,
            self.memory.get_memory()
        )
        response = self.model(prompt, max=3)
        send_chat_msg(response.text, role=self.name, uid=self.uid, avatar=self.avatar)
        user_input = get_player_input(uid=self.uid)
        return user_input

    # 为某一个 Medicine 生成问题，此处只返回判断答案的 Prompt. 由环境 Agent 调用
    def generate_jud_resp_prompt(self, question, resp):
        medicine = self.medicine
        prompt = f"我会给你一个问题和一个答案，他们应该都是和一个药品相关的。帮我判断这个答案是否回答了这个问题。药品是：{medicine.name}，问题是：{question}, 答案是：{resp}。请回答："
        return prompt

    # 只有当回答了本轮的问题，才会增加一个回合数。固定是一个回合
    def inc_cur_cnt_one(self):
        self.cur_cnt += 1

    def finish_researching(self):
        medicine = self.medicine
        cur_cnt = self.cur_cnt

        if cur_cnt < medicine.researchCnt:
            return False
        else:
            if cur_cnt == medicine.researchCnt:
                return True
            else:
                raise Exception("Service Internal Error. Error Code: 1001")
