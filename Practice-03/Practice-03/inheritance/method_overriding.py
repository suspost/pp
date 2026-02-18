
class Bird:
    def sound(self):
        print("Bird sound")

class Parrot(Bird):
    def sound(self):
        print("Parrot talks")

p = Parrot()
p.sound()
