from enums import RelationLevel
from Person import Person

class Relation(object):
    def __init__(self, person: Person, level: RelationLevel) -> None:
        super().__init__()
        self.person = person
        self.level = level
        

if __name__ == "__main__":
    person = Person(name="reymond")
    relation = Relation(person, RelationLevel.STRANGE)
    print(relation.person.name)
    print(relation.level.value)
    