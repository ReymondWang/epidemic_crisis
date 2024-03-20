from Medicine import Medicine


class Research(object):
    """
    medicine: 本次需要研发的药品
    cur_cnt: 完成了几个回合
    """

    def __init__(
            self,
            medicine: Medicine,
            cur_cnt: int
    ) -> None:
        super().__init__()
        self.medicine = medicine
        self.cur_cnt = cur_cnt

    # 为某一个 Medicine 生成问题，此处只返回问题 Prompt. 由环境 Agent 调用
    def generate_question_prompt(self):
        medicine = self.medicine
        prompt = f"我会给你一个药物，帮我对这个药物生成知识问答型问题。药物名称是：{medicine.name}。你生成的问题是："
        return prompt

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
