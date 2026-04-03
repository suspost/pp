# Multiple Inheritance
class A:
    def method_a(self):
        print("A")

class B:
    def method_b(self):
        print("B")

class C(A, B):
    pass

c = C()
c.method_a()
c.method_b()
