import yaml

def generate_yaml_file(job_type):
    data = {
        'name': job_type,
        'base_dir': f'/Users/xxx/hf_worker/{job_type}',
        'tmp_dir': f'/Users/xxx/hf_worker/{job_type}/tmp',
        'log_dir': f'/Users/xxx/hf_worker/{job_type}/log',
        'daemon_dir': f'/Users/xxx/hf_worker/{job_type}/daemon',
        'log_level': 'info',
        'runner': {
            'delay_checkout': 30,
            'delay_check_run_status': 30,
            'delay_advance_status': 30,
            'delay_refresh_limited': 600,
            'delay_update_batch': 60,
            'lock_timeout': 86400,
            'delete_tmp_folder': True,
            'max_step_attempts': 5,
            'delta_retry': [30, 300, 1200]
        },
        'workers': {
            f'worker_{job_type}': {
                'type': 'remote',
                'scheduler_type': 'slurm',
                'work_dir': f'/public/home/xxx/z_works/3_all_flow_jf/works/{job_type}',
                'pre_run': '''conda init
source /public/home/xxx/bin/miniconda3/bin/activate atomate2
module purge
export MKL_DEBUG_CPU_TYPE=5
export MKL_CBWR=AVX2
export OMP_NUM_THREADS=16
module load bader-1.05-gcc7.3.1
module load lobster-5.0.0-none
module load vasp-6.4.2-intelmpi2017_ioptcell''',
                'host': 'xxx',
                'port': xxx,
                'password': 'xxx',
                'user': 'xxx',
                'key_filename': '/Users/xxx/.ssh/xxx_hfeshell.nscc-hf.cn_RsaKeyExpireTime_2025-06-16_10-06-59.txt'
            }
        },
        'queue': {
            'store': {
                'type': 'MongoStore',
                'host': 'xxx',
                'port': xxx,
                'database': 'xxx',
                'username': 'xxx',
                'password': 'xxx',
                'collection_name': f'jobs_{job_type}'
            }
        },
        'exec_config': {},
        'jobstore': {
            'docs_store': {
                'type': 'MongoStore',
                'host': 'xxx',
                'port': xxx,
                'database': 'xxx',
                'username': 'xxx',
                'password': 'xxx',
                'collection_name': f'outputs_{job_type}'
            },
            'additional_stores': {
                'data': {
                    'type': 'GridFSStore',
                    'database': 'xxx',
                    'host': 'xxx',
                    'port': xxx,
                    'username': 'xxx',
                    'password': 'xxx',
                    'collection_name': f'outputs_blobs_{job_type}'
                }
            }
        }
    }

    def str_presenter(dumper, data):
        if '\n' in data:  # 检查是否为多行字符串
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)

    yaml.add_representer(str, str_presenter)

    file_path = f'/Users/xxx/.jfremote/{job_type}.yaml'

    with open(file_path, 'w') as file:
        yaml.dump(data, file, sort_keys=False, default_flow_style=False)

    print(f"YAML 文件已成功保存到 {file_path}")
