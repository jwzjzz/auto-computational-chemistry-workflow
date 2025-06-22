import json
import re
import sys
sys.path.append('/Users/jzz/jzz_python/z_jupyter/1_jf/z_wf_instance')
from jf_jzz import (
    JobController,
    WorkflowManager,
)
from pymatgen.core import Structure

# 定义失败作业的 ID
failed_job_id = "11990"
project_name = "wf_dr_gpu"
contcar = f"/Users/jzz/jzz_python/z_jupyter/1_jf/z_wf_instance/tem_contcar/CONTCAR_{failed_job_id}"
#
try:
    new_structure = Structure.from_file(contcar)
except:
    new_structure = None
#
new_incar = None
new_resources = None

# 调用 WorkflowManager 类的 handle_failures 方法处理失败作业
jc = JobController.from_project_name(project_name)
WorkflowManager.handle_failures(jc, failed_job_id, project_name, new_incar, new_structure, new_resources)
