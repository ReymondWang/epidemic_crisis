from enums import InfectionLevel

class Virus(object):
    def __init__(
        self,
        name: str,
        description: str
    ) -> None:
        super().__init__()
        self.name = name
        self.description = description
        self.feature_dict = {}
        
    def set_feature(self, level: InfectionLevel, feature: str):
        self.feature_dict[level] = feature
        
    def get_feature(self, level: InfectionLevel):
        if level in self.feature_dict:
            return self.feature_dict[level]
        else:
            raise Exception("Virus [" + self.name + "] don't have " + level + "'s feature.")
        
if __name__ == "__main__":
    virus = Virus("Corona", "It is a very terrible virus.")
    print(virus.name)
    print(virus.description)
    
    virus.set_feature(InfectionLevel.CLEAN, "None")
    print(virus.get_feature(InfectionLevel.CLEAN))