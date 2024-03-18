from enums import EffectLevel

class Medicine(object):
    """
    name: 药品的名称
    effect: 药品的效果等级
    price: 药品的价格(简化起见，这里就是等于多少food的交换量)
    researchCnt: 研发需要的回合（感觉这里似乎改成需要回答问题更合适）
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
        
if __name__ == "__main__":
    medicine = Medicine(name="盘尼西林", effect=EffectLevel.POOR, price=5, researchCnt=5)
    print(medicine.name)
    print(medicine.effect.value)
    print(medicine.price)
    print(medicine.researchCnt)
        