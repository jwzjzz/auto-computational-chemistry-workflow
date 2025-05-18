import json
import re
import sys
sys.path.append('/Users/jzz/jzz_python/z_jupyter/1_jf/z_wf_instance')
from jf_jzz import (
    JobController,
    WorkflowManager,
)

# 实例化 JobController
jc = JobController()

# 定义失败作业的 ID
failed_job_id = "your_failed_job_id"
project_name = "your_project_name"

# 定义需要更新的参数
new_incar = {
    "EDIFF": 1e-5,
    "IBRION": 2
}

new_structure = None  # 如果不需要更新结构，可以设为 None
new_resources = None

# 调用 WorkflowManager 类的 handle_failures 方法处理失败作业
WorkflowManager.handle_failures(jc, failed_job_id, project_name, new_incar, new_structure, new_resources)
