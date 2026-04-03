# *args and **kwargs
def demo(*args, **kwargs):
    print(args)
    print(kwargs)

demo(1,2,3, name="John")
