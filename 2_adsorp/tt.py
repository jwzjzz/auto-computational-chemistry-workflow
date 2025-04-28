import json
import re
from datetime import datetime
import sys
import yaml
import os
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    AdsorptionMaker,
)


def parse_config(config_path):
    """
    解析配置文件

    Args:
        config_path (str): 配置文件路径

    Returns:
        dict: 解析后的配置参数
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        logging.error(f"未找到配置文件: {config_path}")
        raise
    except Exception as e:
        logging.error(f"读取配置文件时出错: {e}")
        raise


def build_workflow(config):
    """
    根据配置构建工作流

    Args:
        config (dict): 配置参数

    Returns:
        Flow: 构建好的工作流对象
    """
    base_incar = config.get("base_incar", VASPConfigManager.get_default_incar())
    parr_incar = config.get("parr_incar", {})
    maker_kwargs = config.get("maker_kwargs", {})
    maker_config = config.get("maker")

    if maker_config is None:
        logging.error("配置文件中缺少 maker 配置")
        raise ValueError("配置文件中缺少 maker 配置")

    adsorption_params = maker_config.get('adsorption_maker')
    specified_element = maker_config.get('specified_element')
    molecule_file = maker_config.get('molecule_file')
    input_data = config.get("input_data")

    try:
        if maker_config.get('class') == DoubleRelaxMaker.__name__:
            custom_maker = DoubleRelaxMaker()
            builder = VASPWorkflowBuilder(custom_maker)
            my_flow = builder.build_workflow(
                input_data=input_data,
                base_incar=base_incar,
                parr_incar=parr_incar,
                **maker_kwargs
            )
        elif maker_config.get('class') == ElectrodeInsertionMaker.__name__:
            relax_maker = RelaxMaker()
            static_maker = StaticMaker(
                **maker_config.get("static_maker", {})
            )
            custom_maker = ElectrodeInsertionMaker(
                relax_maker=relax_maker,
                static_maker=static_maker
            )
            builder = VASPWorkflowBuilder(custom_maker)
            my_flow = builder.build_workflow(
                input_data=input_data,
                base_incar=base_incar,
                parr_incar=parr_incar,
                **maker_kwargs
            )
        elif maker_config.get('class') == AdsorptionMaker.__name__:
            custom_maker = AdsorptionMaker(**adsorption_params)
            builder = VASPWorkflowBuilder(custom_maker)
            my_flow = builder.build_workflow_ads(
                input_data_s=input_data,
                input_data_m=molecule_file,
                specified_element=specified_element,
                base_incar=base_incar,
                parr_incar=parr_incar,
                **maker_kwargs
            )
        else:
            logging.error(f"不支持的 maker 配置: {maker_config}")
            raise ValueError(f"不支持的 maker 配置: {maker_config}")
        return my_flow
    except Exception as e:
        logging.error(f"构建工作流时出错: {e}")
        raise


def submit_workflow(my_flow, config):
    """
    提交工作流

    Args:
        my_flow (Flow): 工作流对象
        config (dict): 配置参数

    Returns:
        Any: 提交工作流的响应
    """
    try:
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
        logging.info(response)
        return response, vis_wf
    except Exception as e:
        logging.error(f"提交工作流时出错: {e}")
        raise


def save_result(output_dir, response, vis_wf, config):
    """
    保存结果到文件

    Args:
        output_dir (str): 输出目录
        response (Any): 提交工作流的响应
        vis_wf (str): 工作流的可视化表示
        config (dict): 配置参数

    Returns:
        str: 保存结果的文件路径
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        json_file_path = os.path.join(output_dir, f'output_{current_time}_{str(response[0])}.json')

        with open(json_file_path, 'w') as f:
            json.dump({
                "vis_wf": vis_wf,
                "project": config["project"],
                "flow_identifier": config["flow_identifier"],
                "response": str(response)
            }, f, indent=4)

        logging.info(f"数据已保存到 {json_file_path}")
        return json_file_path
    except Exception as e:
        logging.error(f"保存结果时出错: {e}")
        raise


def run_workflow_from_config():
    input_dir = "inputs"
    output_dir = "outputs"
    config_path = os.path.join(input_dir, "config.yaml")

    config = parse_config(config_path)
    my_flow = build_workflow(config)
    response, vis_wf = submit_workflow(my_flow, config)
    return save_result(output_dir, response, vis_wf, config)


if __name__ == "__main__":
    run_workflow_from_config()
