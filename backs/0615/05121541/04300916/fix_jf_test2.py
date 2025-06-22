import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.append('/Users/jzz/jzz_python/z_jupyter/1_jf/z_wf_instance')
from jf_jzz import JobController, WorkflowManager

# 本地保存CONTCAR文件的目录
LOCAL_CONTACAR_DIR = Path("/Users/jzz/jzz_python/z_jupyter/1_jf/z_wf_instance/tem_contcar")

def extract_info_from_json(json_file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """从JSON文件提取项目名称和db_id"""
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)

        response = data.get("response", [])
        db_id = str(response[0]) if isinstance(response, list) and response else None
        return data.get("project"), db_id

    except Exception as e:
        print(f"解析JSON文件失败: {str(e)}")
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

def copy_failed_contcars(jc: JobController, workflow: Dict):
    """复制失败作业的CONTCAR文件（基于~/.ssh/config配置）"""
    failed_jobs = [job for job in workflow["jobs"] if job.state.name == "FAILED"]

    if not failed_jobs:
        print("\n未发现失败作业")
        return

    print(f"\n发现 {len(failed_jobs)} 个失败作业")

    for job in failed_jobs:
        try:
            remote_path = f"{job.run_dir}/CONTCAR"
            local_path = LOCAL_CONTACAR_DIR / f"CONTCAR_{job.db_id}"

            print(f"\n正在处理失败作业 {job.db_id}:")
            print(f"远程路径: {remote_path}")
            print(f"本地保存位置: {local_path}")

            subprocess.run(
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
    input_json = Path("./2_adsorp/outputs/output_20250428092045_11973.json")

    # 提取工作流信息
    project_name, db_id = extract_info_from_json(input_json)
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
    copy_failed_contcars(jc, workflow)

    if any(job.state.name == "FAILED" for job in workflow["jobs"]):
        print("\n建议后续操作:")
        print("1. 检查复制到本地的CONTCAR文件")
        print("2. 使用WorkflowManager.handle_failures处理失败作业")
        print("3. 重新提交修正后的工作流")
