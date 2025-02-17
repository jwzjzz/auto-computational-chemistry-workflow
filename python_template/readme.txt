本template为自动计算流程template。第一个单元格的内容不需要修改。
介绍：
ComputationalWorkflow类为抽象类（ABC），包含抽象方法calculation_result_output，无法直接实例化，需要自行继承该类并完成calculation_result_output方法才可以调用。
该类包含以下方法：
1. __init__：初始化计算工作流类，接收配置文件、脚本文件和数据文件夹路径（load_config）。配置文件默认为config.yaml，计算脚本默认为script.py，数据文件夹路径默认为data文件夹，在继承和使用时不必修改，沿用此设置即可。在此之后，会检查依赖库的安装情况并安装（check_requirements），并检查依赖数据的存在情况（check_data_requirements）。
2. execute_calculation：执行script.py中的calculation函数，并返回该函数的计算结果。
3. calculation_result_output：记录需要的计算结果，输出为outputs.yaml，输出格式应按照示例给出，如有需要的其他输出可按照示例自行添加。如有需要以文件的形式记录的结果，则储存在output_data文件夹中。各位老师需要自行完成该函数，以记录自己工作流需要储存的信息。

自动计算流需要的三元组：

1. config.yaml：配置文件，由三个部分组成：
parameters，即script.py中计算函数calculation需要的参数，每个参数需要三个元素：name-参数名，value-参数值，is_required-是否必须，若非必须参数则需要在calculation函数中填入默认值；
requirements，即完成计算需要的库名和版本号（版本可不填），每个参数需要两个元素：name-库名，version-版本号；
data_requirements，即完成计算需要在data文件夹中准备的必要文件，每个参数需要一个元素：name-文件名。

示例：

parameters:
  - name: cos_para
    value: 0.5
    is_required: true
  - name: sin_para
    value: 0.5
    is_required: true
  - name: add_para
    value:
    is_required: false
requirements:
  - name: numpy
    version: 
  - name: math
    version: 
data_requirements:
  - name: 123.cif
  - name: 456.cif

2. script.py：计算流脚本，其中需要包括导入的包，外加一个calculation函数。
该函数有且仅有配置文件中parameters规定的参数作为传入参数。
该函数有且仅有配置文件中data_requirements规定的文件作为需要导入的文件，且导入应当在该函数中完成。
有且仅有一个calculation函数，若有多个函数请整合为一个calculation函数。

示例：

import math

def calculation(cos_para, sin_para, add_para=0):
    with open('./data/123.cif', 'r') as f:
        a = f.read()
        a = float(a)
    with open('./data/456.cif', 'r') as f:
        b = f.read()
        b = float(b)
    return math.cos(cos_para) + math.sin(sin_para) + add_para + a + b

3. data文件夹：计算所需要的额外文件，必须符合配置文件中data_requirements的规定。在其他人使用该工作流时，会根据data_requirements的规定提供data文件夹作为额外数据。