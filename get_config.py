import sys
import re
from pathlib import Path

def generate_yaml(worker_n, material, adsorbate):
    # 提取吸附分子中的指定元素（如 Na2S → S）
    element_pattern = r"([A-Z][a-z]*)\d*"
    elements = re.findall(element_pattern, adsorbate)
    specified_element = elements[-1] if elements else None  # 取最后一个元素（如 S）

    config = {
        "project": f"wf_brl_{worker_n}",
        "worker_n": worker_n,
        "input_data": f"./inputs/{material}.cif",
        "flow_identifier": f"ads_{material.lower()}",
        "maker": {
            "class": "AdsorptionMaker",
            "adsorption_maker": {
                "min_vacuum": 12.0,
                "min_slab_size": 9.0,
                "min_lw": 8.0,
                "surface_idx": None  # 用 ~ 表示 null
            },
            "molecule_file": f"./inputs/{adsorbate}.cif",
            "specified_element": specified_element,
            "relax_maker": {},
            "static_maker": {
                "task_document_kwargs": {
                    "store_volumetric_data": []
                }
            }
        },
        "base_incar": {},
        "parr_incar": {
            "KPAR": 4,
            "NCORE": 16
        },
        "maker_kwargs": {
            "inserted_element": material,
            "n_steps": 1,
            "insertions_per_step": 1
        }
    }

    # 将 None 转换为 YAML 的 ~ 符号
    yaml_content = yaml.dump(config, default_flow_style=False, sort_keys=False)
    yaml_content = yaml_content.replace("null", "~")

    with open("config.yaml", "w") as f:
        f.write(yaml_content)

if __name__ == "__main__":
    try:
        import yaml
    except ImportError:
        print("请先安装 pyyaml 库：pip install pyyaml")
        sys.exit(1)

    if len(sys.argv) != 4:
        print(f"用法：python {sys.argv[0]} <worker_n> <material> <adsorbate>")
        sys.exit(1)

    worker_n = sys.argv[1]
    material = sys.argv[2]
    adsorbate = sys.argv[3]

    generate_yaml(worker_n, material, adsorbate)
    print(f"已生成 config.yaml，使用参数：{worker_n} {material} {adsorbate}")
