# ========================
# 导入必要模块
# ========================
import warnings
warnings.filterwarnings("ignore")
import numpy as np
from typing import Dict, Any
#
from pymatgen.ext.matproj import MPRester
from pymatgen.analysis.adsorption import AdsorbateSiteFinder
from pymatgen.core import Element, Molecule, Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.core.surface import SlabGenerator
from pymatgen.transformations.advanced_transformations import CubicSupercellTransformation
#
from atomate2.vasp.jobs.core import RelaxMaker, StaticMaker, DielectricMaker, TightRelaxMaker
from atomate2.vasp.jobs.base import BaseVaspMaker
from atomate2.vasp.jobs.phonons import PhononDisplacementMaker
from atomate2.vasp.flows.core import *
from atomate2.vasp.flows.phonons import PhononMaker
from atomate2.vasp.flows.electrode import ElectrodeInsertionMaker
from atomate2.vasp.flows.adsorption_jzz import AdsorptionMaker #注意这个地方用的是修改的代码
from atomate2.vasp.flows.defect import FormationEnergyMaker
from atomate2.vasp.powerups import update_user_incar_settings
from atomate2.common.powerups import add_metadata_to_flow
from atomate2.vasp.sets.core import StaticSetGenerator, TightRelaxSetGenerator
#
from jobflow.utils.graph import to_mermaid
from jobflow import Flow, Job
from jobflow.managers.local import run_locally
from jobflow_remote import submit_flow
from jobflow_remote import JobController
#
import sys
sys.path.append('/Users/jzz/.jfremote')
import os
import shutil
import subprocess
import logging
import multiprocessing
import traceback
from custodian.vasp.handlers import WalltimeHandler
#
# ========================
# 配置管理模块
# ========================
class VASPConfigManager:
    @staticmethod
    def get_default_incar():
        """默认INCAR参数（移除了KPAR和NCORE）"""
        return {
            "ENCUT": 520,
            "PREC": "Normal",
            "EDIFF": 1e-5,
            "EDIFFG": -0.05,
            "ISMEAR": 0,
        }
    @staticmethod
    def get_default_incar_phonon():
        """默认INCAR参数（移除了KPAR和NCORE）"""
        return {
            "ENCUT": 520,
            "EDIFF": 1e-6,
            "EDIFFG": -0.01,
        }

    @staticmethod
    def get_cluster_config(worker_n):
        """集群资源配置"""
        configs = {
            "hfe": {
                "module": "yaml_generator_hf",
                "resources": {"nodes": 1, "ntasks": 64, "partition": "hfacexclu08"}
            },
            "sc": {
                "module": "yaml_generator_sc_hf",
                "resources": {"nodes": 1, "ntasks": 64, "partition": "dzacexclu01"}
            },
            "cm": {
                "module": "yaml_generator_cm_hf",
                "resources": {"nodes": 1, "ntasks": 64, "partition": "cpu192", "qos": "premium"}
            },
            "gpu": {
                "module": "yaml_generator_gpu_hf",
                "resources": {"nodes": 1, "ntasks_per_node": 16, "partition": "a800", "gres": "gpu:4"}
            },
            "ai": {
                "module": "yaml_generator_ai",
                "resources": {"nodes": 1, "ntasks": 4, "partition": "hfacexclu08",}
            },
            "wwy": {
                "module": "yaml_generator_wwy_hfe",
                "resources": {"nodes": 1, "ntasks": 64, "partition": "hfacnormal02",}
            },
        }
        return configs.get(worker_n, None)
#
# ========================
# 工作流提交模块
# ========================
class WorkflowSubmitter:
    @staticmethod
    def submit(flow, project=None, worker_n=None):
        """统一提交入口"""
        if project is None:
            return run_locally(flow)
        
        config = VASPConfigManager.get_cluster_config(worker_n)
        if not config:
            raise ValueError(f"不支持的集群配置: {worker_n}")

        try:
            __import__(config["module"])
            generate_yaml = sys.modules[config["module"]].generate_yaml_file
            generate_yaml(project)
            
            return submit_flow(
                flow,
                worker=f"worker_{project}",
                project=project,
                resources=config["resources"]
            )
        except Exception as e:
            print(f"提交错误: {str(e)}")
            raise
#
# ========================
# 工作流管理模块
# ========================
class WorkflowManager:
    @staticmethod
    def check_states(jc, db_id):
        """
        检查工作流状态
        
        Args:
            jc (JobController): 作业控制器实例
            db_id: 流程数据库ID
            
        Returns:
            dict: 不同状态对应的作业ID字典
        """
        states = {}
        db = db_id
        tem_jc = jc.get_job_doc(db_id=db)
        flow_job = jc.get_flow_info_by_job_uuid(tem_jc.uuid)

        print(jc.get_job_doc(job_id=flow_job['jobs'][0]).job.function_args[0].formula)
        print(flow_job['uuid'], flow_job['state'])
        print('#')

        for job_id in flow_job['jobs']:
            tem_jcc = jc.get_job_doc(job_id)
            state_str = str(tem_jcc.state)
            states.setdefault(state_str, []).append(job_id)

            if state_str not in ['JobState.COMPLETED', 'JobState.WAITING', 'JobState.SUBMITTED']:
                print("#")
                print(tem_jcc.db_id, tem_jcc.state, tem_jcc.job.name)
                print(tem_jcc.run_dir)
                print("#")

        return states

    @staticmethod
    def update_incar(jc, db_id, incar_updates):
        """
        更新失败作业的INCAR参数
        
        Args:
            jc (JobController): 作业控制器实例
            db_id: 作业数据库ID
            incar_updates (dict): 需要更新的INCAR参数
        """
        job_doc = jc.get_job_doc(db_id=db_id)
        print(f"原始 INCAR 设置: {job_doc.job.maker.input_set_generator.user_incar_settings}")

        updated_job = update_user_incar_settings(job_doc.job, incar_updates)
        job_doc.job = updated_job

        jc._set_job_properties(job_doc.as_db_dict(), db_id=db_id)
        updated_job_doc = jc.get_job_doc(db_id=db_id)
        print(f"更新后的 INCAR 设置: {updated_job_doc.job.maker.input_set_generator.user_incar_settings}")

    @staticmethod
    def update_structure(jc, db_id, new_structure):
        """
        更新失败作业的结构参数
    
        Args:
            jc (JobController): 作业控制器实例
            db_id: 作业数据库ID
            new_structure: 新的结构对象
        """
        job_doc = jc.get_job_doc(db_id=db_id)
        if'structure' in job_doc.job.function_kwargs:
            job_doc.job.function_kwargs['structure'] = new_structure
            jc._set_job_properties(job_doc.as_db_dict(), db_id=db_id)
            print('结构更新成功')
        else:
            try:
                # 检查 job_doc.job.function_args[0] 是否是 Structure 对象且原子数与 new_structure 一样
                if isinstance(job_doc.job.function_args[0], Structure) and \
                        len(job_doc.job.function_args[0].sites) == len(new_structure.sites):
                    job_doc.job.function_args[0] = new_structure
                    jc._set_job_properties(job_doc.as_db_dict(), db_id=db_id)
                    print('结构更新成功')
                else:
                    print("job_doc.job.function_args[0] 不是有效的 Structure 对象或原子数不匹配")
            except IndexError:
                print("job_doc.job.function_args 为空，无法进行结构更新")
            except:
                print("Function args:", job_doc.job.function_args)
                print("Function kwargs:", job_doc.job.function_kwargs.keys())
                print('需要尝试备份再重置function_args')

    @staticmethod
    def update_resources(jc, db_id, resource_updates):
        """
        更新作业的计算资源配置
        
        Args:
            jc (JobController): 作业控制器实例
            db_id: 作业数据库ID
            resource_updates (dict): 新的资源配置参数
        """
        job_doc = jc.get_job_doc(db_id=db_id)
        if job_doc.resources:
            print(f"原始 resources 设置: {job_doc.resources}")
            job_doc.resources = resource_updates
            jc._set_job_properties(job_doc.as_db_dict(), db_id=db_id)
            updated_job_doc = jc.get_job_doc(db_id=db_id)
            print(f"更新后的 resource 设置: {updated_job_doc.resources}")
        else:
            print('没有找到原始resources')

    @classmethod
    def handle_failures(cls, jc, failed_job_id, project_name, 
                        new_incar=None, new_structure=None, new_resources=None):
        """
        统一处理失败作业
        
        Args:
            jc (JobController): 作业控制器实例
            failed_job_id: 失败作业ID
            project_name (str): 项目名称
            new_incar (dict): 需要更新的INCAR参数
            new_structure: 需要更新的结构对象
            new_resources (dict): 需要更新的资源配置
        """
        db_id = failed_job_id
        tem_jcc = jc.get_job_doc(db_id=db_id)
        
        try:
            if new_incar is not None:
                cls.update_incar(jc, str(db_id), new_incar)
            if new_resources is not None:
                cls.update_resources(jc, str(db_id), new_resources)
            if new_structure is not None:
                cls.update_structure(jc, str(db_id), new_structure)

            jc.rerun_job(db_id=str(db_id), force=True)
        except Exception as e:
            print(f"处理作业 {db_id} 时出错: {e}")
#
# ========================
# 工作流构建模块
# ========================
class VASPWorkflowBuilder:
    SPECIAL_JOBS = ['dielectric', 'hse band structure', 'polarization', 'hse static']

    def __init__(self, maker_instance: BaseVaspMaker):
        """初始化时传入具体的 Maker 实例"""
        self.maker_instance = maker_instance

    def _get_structure(self, input_data: str):
        """根据输入路径或材料 ID 加载结构（保持不变）"""
        if input_data.endswith((".cif", ".vasp")):
            return Structure.from_file(input_data)
        elif input_data.startswith("mp-"):
            with MPRester() as mpr:
                return mpr.get_structure_by_material_id(input_data)
        else:
            raise ValueError("输入数据必须是文件路径或材料ID")
    
    def _compute_supercell_atom_count(
        self,
        structure,
        min_length=5.0,
        max_length=None,
        prefer_90_degrees=True,
        timeout=500
    ):
        """带超时机制的并行超胞计算"""
        def calculation_worker(result_queue):
            try:
                sga = SpacegroupAnalyzer(structure, symprec=0.01)
                conventional = sga.get_conventional_standard_structure()
                transformer = CubicSupercellTransformation(
                    min_length=min_length,
                    max_length=max_length,
                    force_90_degrees=prefer_90_degrees
                )
                supercell = transformer.apply_transformation(conventional)
                result_queue.put(len(supercell))
            except Exception as e:
                result_queue.put(e)
    
        result_queue = multiprocessing.Queue()
        process = multiprocessing.Process(target=calculation_worker, args=(result_queue,))
        process.start()
        process.join(timeout=timeout)
    
        if process.is_alive():
            process.terminate()
            process.join()
            return None
    
        try:
            result = result_queue.get_nowait()
            return result if isinstance(result, int) else None
        except queue.Empty:
            return None
    
    def _get_molecule(self, input_file):
        """
        获取分子结构，可以是文件路径
        :param input_file: 文件路径
        :return: pymatgen Molecule 对象
        """
        if input_file.endswith(".cif"):
            return Molecule.from_sites(Structure.from_file(input_file).sites)
        elif input_file.endswith(".xyz"):
            return Molecule.from_file(input_file)
        else:
            raise ValueError("输入数据必须是文件路径") 

    def _align_molecule_s(self, input_file, specified_element):
        mol = self._get_molecule(input_file)
    
        specified_atom_positions = []
        other_atom_positions = []
        for site in mol:
            if site.specie.symbol == specified_element:
                specified_atom_positions.append(site.coords)
            else:
                other_atom_positions.append(site.coords)
    
        specified_centroid = np.mean(specified_atom_positions, axis=0)
        other_centroid = np.mean(other_atom_positions, axis=0)
    
        vector = other_centroid - specified_centroid
    
        z_axis = np.array([0, 0, 1])
        rotation_axis = np.cross(vector, z_axis)
        rotation_axis_norm = np.linalg.norm(rotation_axis)
        if rotation_axis_norm < 1e-8:
            rotation_angle = 0
        else:
            rotation_axis /= rotation_axis_norm
            cos_angle = np.dot(vector, z_axis) / (np.linalg.norm(vector) * np.linalg.norm(z_axis))
            rotation_angle = np.arccos(cos_angle)
    
        # Antisymmetric matrix for rotation
        rotation_axis_antisymmetric_matrix = np.array([
            [0, -rotation_axis[2], rotation_axis[1]],
            [rotation_axis[2], 0, -rotation_axis[0]],
            [-rotation_axis[1], rotation_axis[0], 0]
        ])
        rotation_matrix = (
            np.eye(3) 
            + np.sin(rotation_angle) * rotation_axis_antisymmetric_matrix 
            + (1 - np.cos(rotation_angle)) * np.dot(rotation_axis_antisymmetric_matrix, rotation_axis_antisymmetric_matrix)
        )
    
        # Introduce an additional small rotation of 5 degrees around the Z-axis
        offset_angle = np.radians(5)  # Convert 5 degrees to radians
        offset_rotation_matrix = np.array([
                [1, 0, 0],
                [0, np.cos(offset_angle), -np.sin(offset_angle)],
                [0, np.sin(offset_angle), np.cos(offset_angle)]
            ])
    
        # Combine the original rotation matrix with the offset rotation matrix
        final_rotation_matrix = np.dot(offset_rotation_matrix, rotation_matrix)
    
        new_coords = []
        for site in mol:
            new_coord = np.dot(final_rotation_matrix, site.coords - specified_centroid) + specified_centroid
            new_coords.append(new_coord)
    
        new_mol = Molecule(mol.species, new_coords)
    
        new_specified_centroid = np.mean(
            [new_mol[i].coords for i, site in enumerate(mol) if site.specie.symbol == specified_element], axis=0
        )
        new_other_centroid = np.mean(
            [new_mol[i].coords for i, site in enumerate(mol) if site.specie.symbol != specified_element], axis=0
        )
        if new_specified_centroid[2] > new_other_centroid[2]:
            flip_matrix = np.array([
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, -1]
            ])
            new_coords = []
            for site in new_mol:
                new_coord = np.dot(flip_matrix, site.coords - specified_centroid) + specified_centroid
                new_coords.append(new_coord)
            new_mol = Molecule(mol.species, new_coords)
    
        return new_mol
    
    def build_workflow(self, input_data: str, base_incar: Dict[str, Any] = None, parr_incar: Dict[str, Any] = None, **maker_kwargs):
        """
        支持大多数 Maker 
        :param input_data: 结构输入（文件路径或材料ID）
        :param base_incar: 基础 INCAR 参数
        :param parr_incar: 并行/通用 INCAR 参数
        :param maker_kwargs: 传递给 Maker.make() 的专属参数（如插层参数、 phonon 参数等）
        """
        structure = self._get_structure(input_data)
        #print(structure)
        base_incar = base_incar or VASPConfigManager.get_default_incar()
        parr_incar = parr_incar or {}

        # 调用 Maker 的 make 方法，传递专属参数
        flow = self.maker_instance.make(structure, **maker_kwargs)
        flow = update_user_incar_settings(flow, base_incar)  # 应用基础 INCAR 参数，所有动态job都可以继承

        # 统一处理 Job 到 Flow 的转换
        if isinstance(flow, Job):
            flow = Flow([flow])

        return self._update_incar_settings(flow, parr_incar)
    
    def build_workflow_def(self, defects, base_incar: Dict[str, Any] = None, parr_incar: Dict[str, Any] = None, **maker_kwargs):
        """
        支持FormationEnergyMaker 
        :param base_incar: 基础 INCAR 参数
        :param parr_incar: 并行/通用 INCAR 参数
        :param maker_kwargs: 传递给 Maker.make() 的专属参数（如插层参数、 phonon 参数等）
        """
        base_incar = base_incar or VASPConfigManager.get_default_incar()
        parr_incar = parr_incar or {}

        flows = []
        for index, defect in enumerate(defects):
            flow_i = self.maker_instance.make(defect,defect_index=index)
            flow_i = update_user_incar_settings(flow_i, base_incar)  # 应用基础 INCAR 参数，所有动态job都可以继承
            flow_i = self._update_incar_settings(flow_i, parr_incar)
            flows.append(flow_i)
        flow = Flow(flows)

        return flow
    
    def build_workflow_ads(self, input_data_s: str, input_data_m: str, specified_element: str = None, base_incar: Dict[str, Any] = None, parr_incar: Dict[str, Any] = None, **maker_kwargs):
        """
        用于AdsorptionMaker
        :param input_data_s: 结构输入（文件路径或材料ID）
        :param input_data_m: 分子输入（文件路径）
        :param specified_element: 用于对齐分子的指定元素
        :param base_incar: 基础 INCAR 参数
        :param parr_incar: 并行/通用 INCAR 参数
        :param maker_kwargs: 传递给 Maker.make() 的专属参数（如插层参数、 phonon 参数等）
        """
        try:
            structure = self._get_structure(input_data_s)
        except ValueError as e:
            print(f"获取结构时出错: {e}")
            return None

        try:
            if specified_element is None:
                molecular = self._get_molecule(input_data_m)
            else:
                molecular = self._align_molecule_s(input_data_m, specified_element)
        except ValueError as e:
            print(f"获取分子时出错: {e}")
            return None

        base_incar = base_incar or VASPConfigManager.get_default_incar()
        parr_incar = parr_incar or {}

        # 调用 Maker 的 make 方法，传递专属参数
        try:
            flow = self.maker_instance.make(molecular,structure, **maker_kwargs)
        except Exception as e:
            print(f"调用 Maker.make 方法时出错: {e}")
            return None

        flow = update_user_incar_settings(flow, base_incar)  # 应用基础 INCAR 参数，所有动态job都可以继承

        # 统一处理 Job 到 Flow 的转换
        if isinstance(flow, Job):
            flow = Flow([flow])

        return self._update_incar_settings(flow, parr_incar)    

    def build_workflow_phonon(self, input_data: str, base_incar: Dict[str, Any] = None, parr_incar: Dict[str, Any] = None, **maker_kwargs):
        """
        用于PhononMaker
        :param maker_kwargs: 传递给 Maker.make() 的专属参数（如插层参数等）
        """
        try:
            structure = self._get_structure(input_data)
        except ValueError as e:
            print(f"获取结构时出错: {e}")
            return None

        base_incar = base_incar or VASPConfigManager.get_default_incar_phonon()
        parr_incar = parr_incar or {}

        # 调用 Maker 的 make 方法，传递专属参数
        try:
            flow = self.maker_instance.make(structure, **maker_kwargs)
        except Exception as e:
            print(f"调用 Maker.make 方法时出错: {e}")
            return None

        flow = update_user_incar_settings(flow, base_incar)  # 应用基础 INCAR 参数，所有动态job都可以继承

        # 统一处理 Job 到 Flow 的转换
        if isinstance(flow, Job):
            flow = Flow([flow])

        return self._update_incar_settings(flow, parr_incar)    

    def _update_incar_settings(self, flow, parr_incar: Dict[str, Any]):
        """更新 INCAR 参数，注意该方式不能处理动态生成的job"""
        for job in flow.jobs:
            if job.name not in self.SPECIAL_JOBS:
                incar_updates = {**parr_incar} 
                flow = update_user_incar_settings(
                    flow=flow,
                    incar_updates=incar_updates,
                    name_filter=job.name,
                )
        return flow
