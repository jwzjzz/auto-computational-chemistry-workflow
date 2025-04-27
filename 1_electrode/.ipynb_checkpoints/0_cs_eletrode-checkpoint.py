import json
import re
from datetime import datetime
import sys
sys.path.append('/Users/jzz/jzz_python/z_jupyter/1_jf')
from jf_jzz_0423 import (
    VASPWorkflowBuilder,
    ElectrodeInsertionMaker,
    add_metadata_to_flow,
    WorkflowSubmitter,
    to_mermaid,
    BaseVaspMaker,
    VASPConfigManager,
)

def run_workflow_and_save_info(project, worker_n, input_data, flow_identifier, base_incar, parr_incar, inserted_element, n_steps, insertions_per_step):
    # 构建工作流
    builder = VASPWorkflowBuilder(ElectrodeInsertionMaker)
    my_flow = builder.build_workflow_insert(
        input_data=input_data,
        base_incar=base_incar,
        parr_incar=parr_incar,
        inserted_element=inserted_element,
        n_steps=n_steps, 
        insertions_per_step=insertions_per_step
    )
    my_flow = add_metadata_to_flow(my_flow, {"flow_identifier": flow_identifier}, class_filter=BaseVaspMaker)

    # 提交工作流
    submitter = WorkflowSubmitter()
    vis_wf = to_mermaid(my_flow)
    response = submitter.submit(my_flow, project=project, worker_n=worker_n)

    # 打印可视化和提交结果
    print(vis_wf)
    print(response)

    # 准备要保存的数据
    data_to_save = {
        "vis_wf": vis_wf,
        "project": project,
        "response": str(response)
    }

    # 获取当前时间的时间戳并格式化
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    json_file_path = f'output_{current_time}_{str(response[0])}.json'

    # 将数据保存到 JSON 文件
    with open(json_file_path, 'w') as f:
        json.dump(data_to_save, f, indent=4)

    print(f"数据已保存到 {json_file_path}")
    return json_file_path


if __name__ == "__main__":
    worker_n = "hfe"
    project = f"wfins_electrode_{worker_n}"
    input_data = "./kvo_old.vasp"
    flow_identifier = "wf_instance_kvo_electrode"
    base_incar = VASPConfigManager.get_default_incar()
    parr_incar = {"KPAR": 4, "NCORE": 16}
    inserted_element = 'Zn'
    n_steps = 1
    insertions_per_step = 10

    json_file = run_workflow_and_save_info(project, worker_n, input_data, flow_identifier, base_incar, parr_incar, inserted_element, n_steps, insertions_per_step)
    print(f"生成的 JSON 文件路径: {json_file}")
