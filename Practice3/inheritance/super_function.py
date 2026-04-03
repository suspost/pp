# super() usage
class Person:
    def __init__(self, name):
        self.name = name

class Student(Person):
    def __init__(self, name, age):
        super().__init__(name)
        self.age = age

s = Student("John", 20)
print(s.name, s.age)
