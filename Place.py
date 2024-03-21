from enums import InfectionLevel,EffectLevel
from Resource import Resource
from Virus import Virus
from Medicine import Medicine
from Person import Person
import random

class Place(object):
    """
    infection: 场所的污染等级
    Resource: 场所存储的资源
    Virus: 场所中存在的病毒
    background: 对应的场所，有商场、药店、医院
    """

    def __init__(self, infection: InfectionLevel, resource: Resource, virus: Virus, background: str) -> None:
        super().__init__()
        self.infection = infection
        self.resource = resource
        self.virus = virus
        self.background = background

    def display_info(self):
        print(f"Infection Level: {self.infection}")
        print(f"Resource-food: {self.resource.food}")
        print(f"Resource-mask: {self.resource.mask}")
        print(f"Resource-medicine: {self.resource.medicine}")
        if self.virus is not None:
            print("Virus Info:")
            print(f"Name: {self.virus.name}")
            print(f"Description: {self.virus.description}")
        print(f"Background: {self.background}")

    def sanitize(self, medicine: Medicine):
        # 实现对 infection 的控制，根据药物的 effect 对 infection 进行减少
        reduction = {
            EffectLevel.POOR: 1,
            EffectLevel.COMMON: 2,
            EffectLevel.GOOD: 4
        }
        if self.infection.value > 0:
            self.infection -= reduction[medicine.effect]
            if self.infection < 0 :
                self.infection = 0
            return True
        else:
            print(f"The {self.background}) is clean, you don't need to use medicine to sanitize it.")
            return False

    def infect(self, person: Person):
        # 判定来到场所的人是否会感染病毒
        infection_chance = {
            InfectionLevel.CLEAN: 0,
            InfectionLevel.TINY: 0.2,
            InfectionLevel.COMMON: 0.4,
            InfectionLevel.SERIOUS: 0.6,
            InfectionLevel.CRITICAL: 0.8,
            InfectionLevel.DEAD: 1
        }
        chance = infection_chance[self.infection]
        if random.random() < chance:
            print(f"{person.name} has been infected at {self.background}")


if __name__ == "__main__":
    resource = Resource()  # 实例化 Resource 类
    virus = Virus("Corona", "It is a very terrible virus")  # 实例化 Virus 类
    place = Place(InfectionLevel.DEAD, resource, virus, "market")  # 创建 Place 实例
    place.display_info()


    # 测试 sanitize 方法
    medicine = Medicine(name="盘尼西林", effect=EffectLevel.POOR, price=5, researchCnt=5)
    print("Before sanitize: ", place.infection)
    place.sanitize(medicine)
    print("After sanitize: ", place.infection)

    # 测试 infect 方法
    person = Person(name="reymond")
    place.infect(person)