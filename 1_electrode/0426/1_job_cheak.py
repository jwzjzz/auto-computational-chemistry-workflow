import json
import re
import sys
sys.path.append('/Users/jzz/jzz_python/z_jupyter/1_jf')
from jf_jzz_0422 import *


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
    #json_file_path = './output_20250422154940_11721.json'
    json_file_path = './output_20250422161206_11723.json'
    project_name, db_id = extract_info_from_json(json_file_path)
    print(project_name, db_id)
    workflow_states = check_workflow_states(project_name, db_id)
    if workflow_states:
        print("工作流状态信息:", workflow_states)
