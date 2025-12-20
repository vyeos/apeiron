import math

for num in range(1, 1001):
    if num > 1:
        for i in range(2, int(math.sqrt(num)) + 1):
            if (num % i) == 0:
                break
        else:
            print(num)

