from enums import RelationLevel
from Person import Person

class Relation(object):
    def __init__(self, person1:Person, person2:Person, level: RelationLevel) -> None:
        super().__init__()
        self.person1 = person1
        self.person2 = person2
        self.level = level
        

if __name__ == "__main__":
    person1 = Person(name="reymond")
    relation = Relation(person1, RelationLevel.STRANGE)
    print(relation.person1.name)
    print(relation.level.value)
    