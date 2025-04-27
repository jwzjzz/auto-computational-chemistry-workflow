import json
import re
from datetime import datetime
import sys
import yaml
import os

sys.path.append('/Users/jzz/jzz_python/z_jupyter/1_jf/z_wf_instance')
from jf_jzz import (
    VASPWorkflowBuilder,
    add_metadata_to_flow,
    WorkflowSubmitter,
    to_mermaid,
    BaseVaspMaker,
    VASPConfigManager,
    DoubleRelaxMaker,
    ElectrodeInsertionMaker,
    RelaxMaker,
    StaticMaker,
)

def run_workflow_from_config():
    # 固定输入输出路径（当前目录下的 inputs/outputs）
    input_dir = "inputs"
    output_dir = "outputs"
    config_path = os.path.join(input_dir, "config.yaml")  # 配置文件路径固定为 inputs/config.yaml

    # 检查输入文件是否存在
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"未找到配置文件: {config_path}")

    # 1. 读取 YAML 配置文件
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # 2. 解析 Maker 实例化参数
    base_incar = config.get("base_incar", VASPConfigManager.get_default_incar())
    parr_incar = config.get("parr_incar", {})
    maker_kwargs = config.get("maker_kwargs", {})  # 提取 Maker.make() 专属参数
    maker_config = config["maker"]
    if maker_config == str(DoubleRelaxMaker):
    	custom_maker = DoubleRelaxMaker()
        builder = VASPWorkflowBuilder(custom_maker)
        my_flow = builder.build_workflow_base(
            input_data=config["input_data"],
            base_incar=base_incar,
            parr_incar=parr_incar,
        )
    elif maker_config == str(ElectrodeInsertionMaker):
        relax_maker = RelaxMaker()  # RelaxMaker 无额外参数，直接实例化
        static_maker = StaticMaker(
            **maker_config.get("static_maker", {})  # 解包 StaticMaker 专属参数
        )
	custom_maker = ElectrodeInsertionMaker(
        relax_maker=relax_maker,
        static_maker=static_maker
        )
        builder = VASPWorkflowBuilder(custom_maker)
        my_flow = builder.build_workflow(
            input_data=config["input_data"],
            base_incar=base_incar,
            parr_incar=parr_incar,
            **maker_kwargs  # 动态传递 Maker 专属参数（如插层参数）
        )
    # 3. 添加元数据（使用配置中的 flow_identifier)，提交工作流（通用逻辑）
    my_flow = add_metadata_to_flow(
        my_flow,
        {"flow_identifier": config["flow_identifier"]},
        class_filter=BaseVaspMaker
    )
    submitter = WorkflowSubmitter()
    vis_wf = to_mermaid(my_flow)
    response = submitter.submit(
        my_flow,
        project=config["project"],
        worker_n=config["worker_n"]
    )

    # 4. 保存结果到 outputs 目录（关键修改：固定输出目录）
    os.makedirs(output_dir, exist_ok=True)  # 自动创建 outputs 目录（若不存在）
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    json_file_path = os.path.join(output_dir, f'output_{current_time}_{str(response[0])}.json')

    with open(json_file_path, 'w') as f:
        json.dump({
            "vis_wf": vis_wf,
            "project": config["project"],
            "flow_identifier": config["flow_identifier"],
            "response": str(response)
        }, f, indent=4)

    print(f"数据已保存到 {json_file_path}")
    return json_file_path

if __name__ == "__main__":
    run_workflow_from_config()
