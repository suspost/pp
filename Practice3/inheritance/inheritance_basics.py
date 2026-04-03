# Inheritance Basics
class Animal:
    def speak(self):
        print("Sound")

class Dog(Animal):
    pass

d = Dog()
d.speak()
