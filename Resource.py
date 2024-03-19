class Resource(object):
    def __init__(self) -> None:
        super().__init__()
        self.food = 0
        self.mask = 0
        self.medicine = {}
    
    def inc_food(self, cnt):
        self.food += cnt
        
    def dec_food(self, cnt=1):
        if self.food >= cnt:
            self.food -= cnt
        else:
            raise Exception("Food is not enough.")
        
    def get_food(self):
        return self.food
    
    def inc_mask(self, cnt):
        self.mask += cnt
        
    def dec_mask(self, cnt=1):
        if self.mask >= cnt:
            self.mask -= cnt
        else:
            raise Exception("Mask is not enough.")
        
    def get_mask(self):
        return self.mask
    
    def inc_medicine(self, med_name, cnt):
        if med_name not in self.medicine:
            self.medicine[med_name] = cnt
        else:
            self.medicine[med_name] += cnt
            
    def dec_medicine(self, med_name, cnt=1):
        if med_name not in self.medicine:
            raise Exception("Medicine[" + med_name + "] is not in the dict .")
        elif self.medicine[med_name] < cnt:
            raise Exception("Medicine[" + med_name + "] is not enough.")
        else:
            self.medicine[med_name] -= cnt
    
    def get_medicine(self, med_name):
        if med_name not in self.medicine:
            return 0
        else:
            return self.medicine[med_name]
        
if __name__ == "__main__":
    resource = Resource()
    
    # resource.inc_food(1)
    # print(resource.get_food())
    # resource.dec_food()
    # print(resource.get_food())
    
    # resource.inc_mask(2)
    # print(resource.get_mask())
    # resource.dec_mask()
    # print(resource.get_mask())
    
    resource.inc_medicine("penicillin", 1)
    print(resource.get_medicine("penicillin"))
    resource.dec_medicine("penicillin")
    print(resource.get_medicine("penicillin"))