import json
import re
from datetime import datetime
import sys
import yaml
import os
import logging
from pymatgen.analysis.diffraction.xrd import XRDCalculator
import numpy as np
from pymatgen.core.structure import Structure
from pymatgen.analysis.defects.generators import VacancyGenerator

sys.path.append('/Users/jzz/jzz_python/z_jupyter/1_jf/z_wf_instance')
from jf_jzz import (
    VASPWorkflowBuilder,
    WorkflowSubmitter,
    VASPConfigManager,
    add_metadata_to_flow,
    to_mermaid,
    BaseVaspMaker,
    DoubleRelaxMaker,
    ElectrodeInsertionMaker,
    RelaxMaker,
    StaticMaker,
    AdsorptionMaker,
    Flow,
    FormationEnergyMaker,
    MultiMDMaker,    
)


def get_max_intensity_hkl(structure):
    # 初始化 XRDCalculator
    xrd_calculator = XRDCalculator(wavelength="CuKa")
    # 计算 XRD 图谱
    xrd_pattern = xrd_calculator.get_pattern(structure)
    # 找出强度最大的峰的索引
    max_intensity_index = np.argmax(xrd_pattern.y)
    # 找出最大强度峰对应的 hkl
    max_intensity_hkl = xrd_pattern.hkls[max_intensity_index]
    hkl = max_intensity_hkl[0]['hkl']
    # 如果是六方晶系的格式（四个指数），转换为三方晶系的格式（三个指数）
    if len(hkl) == 4:
        h, k, i, l = hkl
        new_h = h
        new_k = k
        new_l = l
        hkl = (new_h, new_k, new_l)
    return hkl


def run_workflow_from_config():
    # 固定输入输出路径（当前目录下的 inputs/outputs）
    input_dir = "inputs"
    output_dir = "outputs"
    config_path = os.path.join(input_dir, "config.yaml")  # 配置文件路径固定为 inputs/config.yaml

    # 检查输入文件是否存在
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"未找到配置文件: {config_path}")

    try:
        # 1. 读取 YAML 配置文件
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"读取配置文件时出错: {e}")
        return

    # 解析配置参数
    base_incar = config.get("base_incar", VASPConfigManager.get_default_incar())
    parr_incar = config.get("parr_incar", {})
    input_data = config.get("input_data")
    maker_config = config.get("maker")
    #
    maker_kwargs_ins = config.get("ins_maker_kwargs", {})  # 提取 Maker.make() 专属参数
    #
    maker_kwargs_ads = config.get("ads_maker_kwargs", {})  # 提取 Maker.make() 专属参数
    adsorption_params = maker_config.get('adsorption_maker')
    molecule_file = maker_config.get('molecule_file')
    #
    specified_element = maker_config.get('specified_element')
    defect_generator = maker_config.get("defect_generator")
    defect_params = maker_config.get('defect_maker')
    #
    md_params = maker_config.get('md_maker', {})
    md_params = maker_config.get('md_maker')
    md_ref = config.get("md_ref")  
    #
    try:
        if maker_config.get('class') == DoubleRelaxMaker.__name__:
            custom_maker = DoubleRelaxMaker()
            builder = VASPWorkflowBuilder(custom_maker)
            my_flow = builder.build_workflow(
                input_data=input_data,
                base_incar=base_incar,
                parr_incar=parr_incar,
            )
        elif maker_config.get('class') == ElectrodeInsertionMaker.__name__:
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
                input_data=input_data,
                base_incar=base_incar,
                parr_incar=parr_incar,
                **maker_kwargs_ins  # 动态传递 Maker 专属参数（如插层参数）
            )
        elif maker_config.get('class') == AdsorptionMaker.__name__:
            # 处理 surface_idx 参数
            if adsorption_params and'surface_idx' in adsorption_params:
                surface_idx = adsorption_params['surface_idx']
                if surface_idx is not None:
                    if isinstance(surface_idx, str):
                        surface_idx = tuple(int(x) for x in surface_idx.strip('()').split(','))
                        adsorption_params['surface_idx'] = surface_idx
                        logging.info(f"转换 surface_idx 为: {surface_idx}")
                else:
                    structure = Structure.from_file(input_data)
                    new_surface_idx = get_max_intensity_hkl(structure)
                    adsorption_params['surface_idx'] = new_surface_idx
                    logging.info(f"计算得到的 surface_idx 为: {new_surface_idx}")
            #
            custom_maker = AdsorptionMaker(**adsorption_params)
            builder = VASPWorkflowBuilder(custom_maker)
            my_flow = builder.build_workflow_ads(
                input_data_s=input_data,
                input_data_m=molecule_file,
                specified_element=specified_element,
                base_incar=base_incar,
                parr_incar=parr_incar,
            )
        elif maker_config.get('class') == FormationEnergyMaker.__name__:
            structure = Structure.from_file(input_data)
            if defect_generator == "VacancyGenerator":
                defect_ty = VacancyGenerator()
                defects = list(defect_ty.get_defects(structure, rm_species=specified_element))
            else:
                print(f"不支持的 generator: {defect_generator}")
                return
            #
            custom_maker = FormationEnergyMaker(**defect_params)
            builder = VASPWorkflowBuilder(custom_maker)
            my_flow = builder.build_workflow_def(
                defects=defects,
                base_incar=base_incar,
                parr_incar=parr_incar,
            )
        elif maker_config.get('class') == MultiMDMaker.__name__:
            custom_maker = MultiMDMaker.from_parameters(**md_params)
            builder = VASPWorkflowBuilder(custom_maker)
            if md_ref is None:
                # 使用 make 方法构建工作流
                my_flow = builder.build_workflow_md(
                    input_data=input_data,
                    base_incar=base_incar,
                    parr_incar=parr_incar
                )
            else:
                # 使用 restart_from_uuid 方法重启工作流
                my_flow = builder.restart_from_uuid(md_ref)
        else:
            print(f"不支持的 maker 配置: {maker_config}")
            return
        my_flow = builder.build_workflow(
            input_data=input_data,
            base_incar=base_incar,
            parr_incar=parr_incar,
            **maker_kwargs  # 动态传递 Maker 专属参数
        )
    except Exception as e:
        print(f"构建工作流时出错: {e}")
        return

    # 3. 添加元数据（使用配置中的 flow_identifier)，提交工作流（通用逻辑）
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
        print(response)
    except Exception as e:
        print(f"提交工作流时出错: {e}")
        return

    # 4. 保存结果到 outputs 目录（关键修改：固定输出目录）
    try:
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
    except Exception as e:
        print(f"保存结果时出错: {e}")
        return


if __name__ == "__main__":
    run_workflow_from_config()
