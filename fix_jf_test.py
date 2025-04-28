import json
import re
import sys
sys.path.append('/Users/jzz/jzz_python/z_jupyter/1_jf/z_wf_instance')
from jf_jzz import (
    JobController,
    WorkflowManager,
)

# 假设 WorkflowManager 类定义在 workflow_manager.py 文件中
from workflow_manager import WorkflowManager
from your_module import JobController  # 替换为实际的 JobController 导入路径

# 实例化 JobController
jc = JobController()

# 定义失败作业的 ID
failed_job_id = "your_failed_job_id"

# 定义项目名称
project_name = "your_project_name"

# 定义需要更新的参数
new_incar = {
    "EDIFF": 1e-5,
    "IBRION": 2
}

new_structure = None  # 如果不需要更新结构，可以设为 None
new_resources = {
    "nprocs": 4,
    "memory": "8GB"
}

# 调用 WorkflowManager 类的 handle_failures 方法处理失败作业
WorkflowManager.handle_failures(jc, failed_job_id, project_name, new_incar, new_structure, new_resources)


def extract_info_from_json(json_file_path):
    try:
        # 从 JSON 文件中读取数据
        with open(json_file_path, 'r') as f:
            data = json.load(f)

        response_str = str(data.get("response", ""))
        project_name = str(data.get("project", ""))

        # 提取 db_id
        db_id_pattern = r'\[\'(\d+)\''
        db_id_match = re.search(db_id_pattern, response_str)
        if db_id_match:
            db_id = db_id_match.group(1)
        else:
            db_id = None

        return project_name, db_id

    except FileNotFoundError:
        print(f"文件 {json_file_path} 不存在，请检查文件名和路径。")
    except json.JSONDecodeError:
        print(f"文件 {json_file_path} 不是有效的 JSON 格式，请检查文件内容。")

    return None, None


def check_workflow_states(project_name, db_id):
    if project_name and db_id:
        jc = JobController.from_project_name(project_name)
        sta_wf = WorkflowManager.check_states(jc, db_id)
        return sta_wf
    return None


if __name__ == "__main__":
    json_file_path = './2_adsorp/outputs/output_20250428092045_11973.json'
    project_name, db_id = extract_info_from_json(json_file_path)
    print(project_name, db_id)
    workflow_states = check_workflow_states(project_name, db_id)
    if workflow_states:
        print("工作流状态信息:", workflow_states)
