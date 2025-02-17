import math

def calculation(cos_para, sin_para, add_para=0):
    """
    请使用calculation作为计算脚本唯一函数的函数名。
    注意：所有传入参数需要和配置文件对应，必须参数不设置默认值，非必须参数设置默认值。
    注意：所有计算脚本中需要用到的文件，请放在./data目录，并且在config.yaml中标注，以方便后续其他使用者提供文件进行计算。
    """
    with open('./data/123.cif', 'r') as f:
        a = f.read()
        a = float(a)
    with open('./data/456.cif', 'r') as f:
        b = f.read()
        b = float(b)
    return math.cos(cos_para) + math.sin(sin_para) + add_para + a + b