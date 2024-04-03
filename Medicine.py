import pandas as pd
from enums import EffectLevel

PATH_MEDICINE = './data/medicine.xlsx'


class Medicine(object):
    """
    name: 药品的名称
    effect: 药品的效果等级
    price: 药品的价格(简化起见，这里就是等于多少food的交换量)
    researchCnt: 研发需要的回合（感觉这里似乎改成需要回答问题更合适） - Qin 我觉得研发需要的回合是可以的
    """

    def __init__(
        self,
        name: str,
        effect: EffectLevel,
        price: int=1,
        researchCnt: int=1,
        curCnt: int=0,
        enable: str="N",
        question: dict=None
    ) -> None:
        super().__init__()
        self.name = name
        self.effect = effect
        self.price = price
        self.researchCnt = researchCnt
        self.curCnt = curCnt
        self.enable = enable
        self.question = question

    @staticmethod
    def builtin_medicines():
        medicine_pd = pd.read_excel(PATH_MEDICINE, sheet_name="medicine")
        medicine_list = []
        medicine_name_list = []
        medicine_dict = {}

        for _, row in medicine_pd.iterrows():
            name = row['Name']
            effect = EffectLevel(row['Effect'])
            price = row['Price']
            research_cnt = row['Research_Count']
            enable = row['Enable']
            medicine_to_add = Medicine(name, effect, price, researchCnt=research_cnt, curCnt=0, enable=enable)
            medicine_to_add.question = {}

            medicine_list.append(medicine_to_add)
            medicine_name_list.append(name)
            medicine_dict[name] = medicine_to_add

        question_pd = pd.read_excel(PATH_MEDICINE, sheet_name="question")
        for _, row in question_pd.iterrows():
            name = row["Name"]
            category = row["category"]
            question = row["question"]
            
            question_dict = medicine_dict[name].question
            if category in question_dict:
                question_dict[category].append(question)
            else:
                question_list = [question]
                question_dict[category] = question_list


        return medicine_list, medicine_name_list

    def get_medicine_detail(self, name):
        medicine_list, _ = self.builtin_medicines()
        for med in medicine_list:
            if name == med.name:
                return med
        raise Exception("Medicine is not supported yet.")
    
    def inc_cur_cnt(self):
        if self.enable == "N":
            if not self.curCnt:
                self.curCnt = 0
            self.curCnt += 1
            if self.curCnt == self.researchCnt:
                self.enable = "Y"
        else:
            print(f"Medicine:{self.name}已经研发成功，无需增加研发回合。")


if __name__ == "__main__":
    medicine = Medicine(name="盘尼西林", effect=EffectLevel.POOR, price=5, researchCnt=5, enable="Y")
    print(medicine.name)
    print(medicine.effect.value)
    print(medicine.price)
    print(medicine.researchCnt)
    Medicine.builtin_medicines()
    ostw = medicine.get_medicine_detail(name="奥司他韦")
    print(ostw.enable)
    print(ostw.question)
