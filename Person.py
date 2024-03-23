from agentscope.agents import AgentBase
from typing import Optional, Union, Any, Callable

class Person(object):
    def __init__(
        self, 
        name: str, 
    ) -> None:
        super().__init__()
        self.name = name
        print("My name is %s" % self.name)
        
if __name__ == "__main__":
    person = Person(name="reymond")
    print(person.name)