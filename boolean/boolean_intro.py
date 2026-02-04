print(10 > 9)#True
print(10 == 9)#False
print(10 < 9)#False

a = 200
b = 33

if b > a:#False 
  print("b is greater than a")
else:#True
  print("b is not greater than a")

print(bool("Hello"))#True
print(bool(15))#True

print(bool("abc"))#True
print(bool(123))#True
print(bool(["apple", "cherry", "banana"]))#True

bool(False)#False
bool(None)#False
bool(0)#False
bool("")#False
bool(())#False
bool([])#False
bool({})#False

class myclass():
  def __len__(self):
    return 0

myobj = myclass()
print(bool(myobj)) #returs False

x = 200
print(isinstance(x, int))#True. There is a function which chechs a variable is integer or not