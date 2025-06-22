import json
import re
import sys
import argparse
import paramiko
from paramiko.config import SSHConfig
import os

sys.path.append('/Users/jzz/jzz_python/z_jupyter/1_jf/z_wf_instance')
from jf_jzz import (
    JobController,
    WorkflowManager,
)
from pymatgen.core import Structure

# 创建参数解析器
parser = argparse.ArgumentParser(description='Handle failed jobs with command - line arguments.')
# 添加命令行参数
parser.add_argument('failed_job_id', type=str, help='ID of the failed job')
parser.add_argument('project_name', type=str, help='Name of the project')
parser.add_argument('--incar', type=str, default=None, help='JSON string representing the new INCAR dictionary')
parser.add_argument('--resource', type=str, default=None, help='JSON string representing the new resources dictionary')
parser.add_argument('--ssh_host', type=str, required=True, help='SSH host alias as defined in .ssh/config')

# 解析命令行参数
args = parser.parse_args()

failed_job_id = args.failed_job_id
project_name = args.project_name
contcar = f"/Users/jzz/jzz_python/z_jupyter/1_jf/z_wf_instance/tem_contcar/CONTCAR_{failed_job_id}"

# 尝试读取结构文件
try:
    new_structure = Structure.from_file(contcar)
except:
    new_structure = None

# 解析 incar 和 resource 参数
try:
    new_incar = json.loads(args.incar) if args.incar else None
except json.JSONDecodeError:
    print("Error: Invalid JSON format for --incar.")
    sys.exit(1)

try:
    new_resources = json.loads(args.resource) if args.resource else None
except json.JSONDecodeError:
    print("Error: Invalid JSON format for --resource.")
    sys.exit(1)

# 读取 .ssh/config 文件
ssh_config = SSHConfig()
config_path = os.path.expanduser('~/.ssh/config')
if os.path.exists(config_path):
    with open(config_path) as f:
        ssh_config.parse(f)
else:
    print(f"Error: {config_path} does not exist.")
    sys.exit(1)

# 获取指定主机的配置
host_config = ssh_config.lookup(args.ssh_host)

# 处理主机配置中的 IdentityFile
key_filename = host_config.get('identityfile')
if key_filename:
    if isinstance(key_filename, str):
        key_filename = [os.path.expanduser(key_filename)]
    else:
        key_filename = [os.path.expanduser(key) for key in key_filename]

# 创建 JobController 实例
jc = JobController.from_project_name(project_name)

# 获取远程运行目录
try:
    job_info = jc.get_job_info(db_id=failed_job_id)
    job_dir = job_info.run_dir
except AttributeError:
    print("Error: The object returned by jc.get_job_info does not have a 'run_dir' attribute.")
    sys.exit(1)
except Exception as e:
    print(f"Error getting job information: {e}")
    sys.exit(1)

# 建立 SSH 连接
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(
        hostname=host_config.get('hostname', args.ssh_host),
        port=int(host_config.get('port', 22)),
        username=host_config.get('user'),
        key_filename=key_filename
    )
    # 创建 old 文件夹
    create_old_dir_cmd = f"mkdir -p {job_dir}/old"
    stdin, stdout, stderr = ssh.exec_command(create_old_dir_cmd)
    stderr_result = stderr.read().decode()
    if stderr_result:
        print(f"Error creating old directory: {stderr_result}")
        ssh.close()
        sys.exit(1)

    # 移动数据到 old 文件夹
    move_files_cmd = f"mv {job_dir}/* {job_dir}/old/ 2>/dev/null"
    stdin, stdout, stderr = ssh.exec_command(move_files_cmd)
    stderr_result = stderr.read().decode()
    if stderr_result:
        print(f"Error moving files: {stderr_result}")
        ssh.close()
        sys.exit(1)

except paramiko.AuthenticationException:
    print("Authentication failed, please verify your credentials.")
    sys.exit(1)
except paramiko.SSHException as ssh_ex:
    print(f"SSH error occurred: {str(ssh_ex)}")
    sys.exit(1)
except Exception as ex:
    print(f"An error occurred: {str(ex)}")
    sys.exit(1)

# 关闭 SSH 连接
ssh.close()

# 调用 WorkflowManager 类的 handle_failures 方法处理失败作业
WorkflowManager.handle_failures(jc, failed_job_id, project_name, new_incar, new_structure, new_resources)
