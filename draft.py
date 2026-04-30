
import re
a = '711.182.01'


if re.match(r'\d+.\d+.\d+', a):
    res = a.replace('.', '', 1)
    print(res)
