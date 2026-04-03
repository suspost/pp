# Class vs Instance Variables
class Car:
    wheels = 4

    def __init__(self, brand):
        self.brand = brand

c = Car("BMW")
print(c.wheels, c.brand)
