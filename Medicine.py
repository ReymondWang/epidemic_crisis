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
        price: int,
        researchCnt: int
    ) -> None:
        super().__init__()
        self.name = name
        self.effect = effect
        self.price = price
        self.researchCnt = researchCnt

    @staticmethod
    def builtin_medicines():
        medicine_pd = pd.read_excel(PATH_MEDICINE)
        medicine_list = []

        for index, row in medicine_pd.iterrows():
            name = row['Name']
            effect = row['Effect']
            price = row['Price']
            research_cnt = row['Research_Count']
            medicine_to_add = Medicine(name, effect, price, researchCnt=research_cnt)
            medicine_list.append(medicine_to_add)

        return medicine_list

    def get_medicine_detail(self, name):
        medicine_list = self.builtin_medicines()
        for med in medicine_list:
            if name == med.name:
                return med
        raise Exception("Medicine is not supported yet.")


if __name__ == "__main__":
    medicine = Medicine(name="盘尼西林", effect=EffectLevel.POOR, price=5, researchCnt=5)
    print(medicine.name)
    print(medicine.effect.value)
    print(medicine.price)
    print(medicine.researchCnt)
    print(medicine.get_medicine_detail("盘尼西林A").name)
