import os
from abc import ABC, abstractmethod
import yaml
import importlib.util
import importlib.metadata
import pip
import logging


class FileNotFoundErrorCustom(Exception):
    def __init__(self, file_name):
        # 初始化异常信息
        self.message = "文件未找到： " + file_name
        super().__init__(self.message)
        

class ComputationalWorkflow(ABC):
    def __init__(
        self, 
        config_file = 'config.yaml', 
        script_file = 'script.py', 
        data_folder = './data'
    ):
        """
        初始化计算工作流类，接收配置文件、脚本文件和数据文件夹路径。
        
        :param config_file: .xml 配置文件路径，包含参数和需求
        :param script_file: .py 脚本文件路径，包含计算过程
        :param data_folder: 数据文件夹路径，包含计算所需的数据
        """

        self.config_file = config_file
        self.script_file = script_file
        self.data_folder = data_folder
        
        self.parameters = {}
        self.requirements = []
        self.data_requirements = []
        
        # 加载配置文件
        self.load_config()
        self.check_data_requirements()
        self.check_requirements()

    def check_data_requirements(self):
        for data in self.data_requirements:
            if not os.path.exists(os.path.join(self.data_folder, data['name'])):
                raise FileNotFoundErrorCustom(data['name'])
            print('检查通过，存在{}文件'.format(data['name']))

    def load_config(self):
        """
        加载配置文件，并解析出参数、值以及依赖的软件库。
        """
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"配置文件 {self.config_file} 未找到")
        
        with open(self.config_file, 'r') as file:
            config_data = yaml.safe_load(file)
        
        params = config_data.get('parameters', {})
        for param in params:
            if param['is_required'] is False and param['value'] is None:
                continue
            self.parameters[param['name']]=param['value']
            
        self.requirements = config_data.get('requirements', [])
        self.data_requirements = config_data.get('data_requirements', [])

    @staticmethod
    def is_package_installed(package_name, version=None):
        """
        检查一个包是否存在，以及版本是否满足条件
        """
        package_spec = importlib.util.find_spec(package_name)
        if package_spec is None:
            return False
        if version is None:
            return True
        try:
            installed_version = importlib.metadata.version(package_name)
            if version == installed_version:
                return True
            else:
                return False
        except importlib.metadata.PackageNotFoundError:
            return False

    @staticmethod
    def install_package(package_name, version=None):
        if version is not None:
            pip.main(['install', f'{package_name}=={version}'])
        else:
            pip.main(['install', f'{package_name}=={version}'])

    def execute_calculation(self):
        """
        要求在子类中实现计算过程。
        这里提供了一种默认的实现方法。对于特殊的实现方法，请改写本函数。
        """
        with open(self.script_file, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            
        with open(self.script_file, 'r', encoding=encoding) as file:
            script_code = file.read()

        exec(script_code, globals())

        return calculation(**self.parameters)

    def check_requirements(self):
        """
        检查是否满足所需的库和工具并安装
        """
        for req in self.requirements:
            print(f"检查依赖: {req}")
            # 这里可以添加库的安装检查代码，或者通过某些方法验证软件是否可用
            # 举例：检查是否安装某些库
            if not self.is_package_installed(req['name'], req['version']):
                if req['version'] is None:
                    print(f"未安装必需的库: {req['name']}, 安装中")  # todo: 可以使用logging记录为日志
                else:
                    print(f"未安装必需的库: {req['name']}, 版本：{req['version']}, 安装中")
                self.install_package(req['name'], req['version'])
            else:
                print(f"已安装必须的库: {req['name']}")

    # def prepare_data(self):
    """
    准备计算所需的数据。(不需要)
    请注意：请在自己的计算代码script.py中处理计算所需数据，不需要在本工作流中处理数据。
    请注意：请将所需的数据打包进入一个data文件夹，并在script.py代码中从该文件夹处理。
    """

    @abstractmethod
    def calculation_result_output(self):
        """
        将计算结果打包，输出为一个.yaml配置文件和data文件夹内的数据文件，以供工作流进行下一步处理。
        请各位老师自行从self.execute_calculation()方法的结果中提取，储存为一个字典和列表结合的数据结构，输出为outputs.yaml。
        示例：
        with open('outputs.yaml', 'w') as file:
            yaml.dump(data, file, default_flow_style=False)
        如果有需要储存的计算结果，也应当在这个函数中储存至output_data文件夹中。
        """
        raise NotImplementError
        
# 用法示例

class MyWorkflow(ComputationalWorkflow):
    
    def calculation_result_output(self):
        output = {
            'name': 'calculation result',
            'value': self.execute_calculation()
        }
        data = {'outputs': [output]}
        with open('output.yaml', 'w') as file:
            yaml.dump(data, file, default_flow_style=False)

config_file = "config.yaml"
script_file = "script.py"
data_folder = "data"

workflow = MyWorkflow(config_file, script_file, data_folder)

workflow.calculation_result_output()