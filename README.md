"""
基于atomate2+jobflow-remote的自动材料计算——调试分支
当前工作流以“User-Workstation”模式进行创建提交
要求在User端和Workstation端安装配置相同的atomate2+jobflow-remote环境
且要求User端能ssh访问所有Workstation以及mongdb数据库所在
"""

# jf_jzz.py
  # 封装了不同工作流创建的公共部分
# cs_jf.py
  # 包含不同工作流的具体实例化方法：
  ## 当前调试完成的工作流包含：    
    if maker_config.get('class') == DoubleRelaxMaker.__name__:
    elif maker_config.get('class') == ElectrodeInsertionMaker.__name__:
    elif maker_config.get('class') == AdsorptionMaker.__name__:
    elif maker_config.get('class') == FormationEnergyMaker.__name__:
  ## 该脚本执行过程中会读取指定inputs文件夹的输入文件创建并提交工作流
    ## 工作流创建/提交所需参数均在inputs/config.yaml中指定
    ## 相关记录保存在outputs文件夹下面
# check_jf.py
  # 用于检查指定工作流执行状态
# fix_jf.py
  # 用于手动解决修复失败的工作流---主要用于vasp本身因为输入不合理导致的错误
# 其他代码：
 # 生成对应工作流项目文件的配置模版,需先创建mongbd账号然后根据个人数据库配置个性化配置 --- 详细见jobflow-remote官方说明
 /Users/jzz/.jfremote/yaml_generator_cm_hf.py	/Users/jzz/.jfremote/yaml_generator_hf.py
 /Users/jzz/.jfremote/yaml_generator_gpu_hf.py	/Users/jzz/.jfremote/yaml_generator_sc_hf.py
