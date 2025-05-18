import re
import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.append('/Users/jzz/jzz_python/z_jupyter/1_jf/z_wf_instance')
from jf_jzz import JobController, WorkflowManager

# 本地保存CONTCAR文件的目录
LOCAL_CONTACAR_DIR = Path("/Users/jzz/jzz_python/z_jupyter/1_jf/z_wf_instance/tem_contcar")

def extract_ssh_alias_from_project(project_name: str) -> str:
    """
    假设project_name为形如 wf_dr_jzz，提取最后一段作为SSH别名（即 jzz）
    """
    return project_name.strip().split('_')[-1]

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

def get_workflow_details(jc: JobController, db_id: str) -> Optional[Dict]:
    """获取工作流详细信息"""
    try:
        flow_info = jc.get_flow_info_by_job_uuid(jc.get_job_doc(db_id=db_id).uuid)
        return {
            "uuid": flow_info["uuid"],
            "state": flow_info["state"],
            "jobs": [jc.get_job_doc(job_id) for job_id in flow_info["jobs"]]
        }
    except Exception as e:
        print(f"获取工作流信息失败: {str(e)}")
        return None

def print_workflow_status(workflow: Dict):
    """打印工作流状态信息"""
    print(f"\n工作流状态报告 [UUID: {workflow['uuid']}]")
    print(f"总体状态: {workflow['state']}")
    print("作业详情:")

    status_count = {}
    for job in workflow["jobs"]:
        state = job.state.name
        status_count[state] = status_count.get(state, 0) + 1
        print(f"  - 作业ID: {job.db_id} | 名称: {job.job.name} | 状态: {state}")

    print("\n状态统计:")
    for state, count in status_count.items():
        print(f"  {state}: {count} 个作业")

def copy_failed_contcars(jc: JobController, workflow: Dict, ssh_alias: str):
    """复制失败作业的CONTCAR文件（基于~/.ssh/config配置）"""
    failed_jobs = [job for job in workflow["jobs"] if job.state.name == "FAILED"]

    if not failed_jobs:
        print("\n未发现失败作业")
        return

    print(f"\n发现 {len(failed_jobs)} 个失败作业")

    for job in failed_jobs:
        try:
            remote_path = f"{ssh_alias}:{job.run_dir}/CONTCAR"
            local_path = LOCAL_CONTACAR_DIR / f"CONTCAR_{job.db_id}"

            print(f"\n正在处理失败作业 {job.db_id}:")
            print(f"远程路径: {remote_path}")
            print(f"本地保存位置: {local_path}")

            result = subprocess.run(
                ["scp", remote_path, str(local_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("文件复制成功！")

        except subprocess.CalledProcessError as e:
            print(f"复制失败: {e.stderr.decode()}")
        except Exception as e:
            print(f"处理作业 {job.db_id} 时发生错误: {str(e)}")

if __name__ == "__main__":
    input_json = Path("/Users/jzz/jzz_python/z_jupyter/1_jf/z_wf_instance/2_adsorp/outputs/output_20250428092045_11973.json")

    # 提取工作流信息
    project_name, db_id = extract_info_from_json(input_json)
    ssh_alias = extract_ssh_alias_from_project(project_name)
    print(project_name,db_id,ssh_alias)
    if not project_name or not db_id:
        sys.exit("无法提取有效的工作流信息")

    try:
        jc = JobController.from_project_name(project_name)
    except Exception as e:
        sys.exit(f"初始化JobController失败: {str(e)}")

    workflow = get_workflow_details(jc, db_id)
    if not workflow:
        sys.exit("无法获取工作流详细信息")

    print_workflow_status(workflow)
    copy_failed_contcars(jc, workflow, ssh_alias)

    if any(job.state.name == "FAILED" for job in workflow["jobs"]):
        print("\n建议后续操作:")
        print("1. 检查复制到本地的CONTCAR文件")
        print("2. 使用WorkflowManager.handle_failures处理失败作业")
        print("3. 重新提交修正后的工作流")
