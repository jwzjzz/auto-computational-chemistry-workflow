from jobflow_remote import JobController
from jobflow_remote import get_jobstore
from datetime import datetime
from pymatgen.phonon.bandstructure import PhononBandStructureSymmLine
from pymatgen.phonon.dos import PhononDos
from pymatgen.phonon.plotter import PhononBSPlotter, PhononDosPlotter
#
project_name = 'wf_def_sc'
db_id = '12003'
job_type = 'defect workflow' #'double relax'/'adsorption workflow'/'phonon workflow'/'electrode workflow'
# 获取作业控制器和作业存储
jc = JobController.from_project_name(project_name)
js = get_jobstore(project_name)
js.connect()

try:
    # 获取流程信息
    job_doc = jc.get_job_doc(db_id=db_id)
    flow_info = jc.get_flow_info_by_job_uuid(jc.get_job_doc(db_id=db_id).uuid)
    if flow_info.get("state") == 'COMPLETED':
        
        if job_type == 'double relax':
            # 处理双弛豫流程
            for job_id in flow_info.get('jobs', []):
                criteria = {'uuid': job_id}
                fws = js.query(criteria=criteria, load=True)
                
                for fw in fws:
                    output = fw.get('output', {})
                    calcs_reversed = output.get('calcs_reversed', [{}])
                    input_data = output.get('input', {})
                    output_data = output.get('output', {})
                                        
                    print('### task descript ###')
                    print(output.get('calc_type'))
                    print(output.get('task_label'))
                    print(calcs_reversed[0].get('vasp_version'))
                    print(output.get('completed_at'))
                    print(output.get('run_stats'))
                    
                    print('### input descript ###')
                    print(input_data.get('incar'))
                    print(input_data.get('kpoints'))
                    print(input_data.get('potcar'))
                    print(input_data.get('structure'))  # 需渲染
                    
                    print('### main output ###')
                    print(output_data.get('density'))
                    print(output_data.get('energy'))
                    print(output_data.get('forces'))
                    print(output_data.get('stress'))
                    print(output_data.get('structure')) # 需渲染
        
        elif job_type == 'adsorption workflow':
            # 处理吸附工作流
            for job_id in flow_info.get('jobs', []):
                criteria = {'uuid': job_id}
                fws = js.query(criteria=criteria, load=True)
                
                for fw in fws:
                    job_name = fw.get('name', '')
                    
                    if job_name == 'adsorption_calculations':
                        output = fw.get("output", {})
                        orig_structures = output.get("structures", []) # 需渲染
                        energies = output.get("adsorption_energies", [])
                        config_num = output.get("configuration_numbers", [])
                        
                    elif job_name.startswith('slab_static_maker__static_adsconfig'):
                        output = fw.get('output', {})
                        calcs_reversed = output.get('calcs_reversed', [{}])
                        input_data = output.get('input', {})
                        output_data = output.get('output', {})
                        
                        print('### task descript ###')
                        print(output.get('calc_type'))
                        print(output.get('task_label'))
                        print(calcs_reversed[0].get('vasp_version'))
                        print(output.get('completed_at'))
                        print(output.get('run_stats'))
                        
                        print('### input descript ###')
                        print(input_data.get('incar'))
                        print(input_data.get('kpoints'))
                        print(input_data.get('potcar'))
                        
                        print('### main output ###')
                        print(output_data.get('density'))
                        print(output_data.get('energy'))
                        print(output_data.get('forces'))
                        print(output_data.get('stress'))
                        print(output_data.get('structure')) # 需渲染 最好保存成字典与adsorption_calculations得到的结果进行对比

        elif job_type == 'phonon workflow':
            for job_id in flow_info.get('jobs', []):
                criteria = {'uuid': job_id}
                fws = js.query(criteria=criteria, load=True)
                
                for fw in fws:
                    job_name = fw.get('name', '')
                    if job_name == 'generate_frequencies_eigenvectors':
                        output = fw.get("output", {})
                        structures = output.get("structure", []) # 需渲染
                        phonon_bandstructure = output.get("phonon_bandstructure", []) # 可出图
                        phonon_dos = output.get("phonon_dos", []) # 可出图
                        temperatures = output.get("temperatures", [])
                        free_energies = output.get("free_energies", []) # 可出图
                        heat_capacities = output.get("heat_capacities", []) # 可出图
                        internal_energies = output.get("internal_energies", []) # 可出图
                        entropies = output.get("entropies", []) # 可出图
                        
                    elif job_name.startswith(('tight relax','static','phonon static','dielectric')):
                        output = fw.get('output', {})
                        calcs_reversed = output.get('calcs_reversed', [{}])
                        input_data = output.get('input', {})
                        output_data = output.get('output', {})
                        
                        print('### task descript ###')
                        print(output.get('calc_type'))
                        print(output.get('task_label'))
                        print(calcs_reversed[0].get('vasp_version'))
                        print(output.get('completed_at'))
                        print(output.get('run_stats'))
                        
                        print('### input descript ###')
                        print(input_data.get('incar'))
                        print(input_data.get('kpoints'))
                        print(input_data.get('potcar'))
                        
                        print('### main output ###')
                        print(output_data.get('density'))
                        print(output_data.get('energy'))
                        print(output_data.get('forces'))
                        print(output_data.get('stress'))
                        print(output_data.get('structure'))


        elif job_type == 'electrode workflow':
            for job_id in flow_info.get('jobs', []):
                criteria = {'uuid': job_id}
                fws = js.query(criteria=criteria, load=True)
                
                for fw in fws:
                    job_name = fw.get('name', '')
                    if job_name.startswith(('relax')):
                        output = fw.get('output', {})
                        calcs_reversed = output.get('calcs_reversed', [{}])
                        input_data = output.get('input', {})
                        output_data = output.get('output', {})
                        
                        print('### task descript ###')
                        print(output.get('calc_type'))
                        print(output.get('task_label'))
                        print(calcs_reversed[0].get('vasp_version'))
                        print(output.get('completed_at'))
                        print(output.get('run_stats'))
                        
                        print('### input descript ###')
                        print(input_data.get('incar'))
                        print(input_data.get('kpoints'))
                        print(input_data.get('potcar'))
                        
                        print('### main output ###')
                        print(output_data.get('density'))
                        print(output_data.get('energy'))
                        print(output_data.get('forces'))
                        print(output_data.get('stress'))
                        print(output_data.get('structure'))

        elif job_type == 'defect workflow':
            fw_entry = []
            for job_id in flow_info.get('jobs', []):
                criteria = {'uuid': job_id}
                fws = js.query(criteria=criteria, load=True)
                for fw in fws:
                    job_name = fw.get('name', '')
                    if job_name.startswith(('get_defect_entry')):
                        fw_entry.append(fw) # 暂时这样 还需要其它工作流数据才能可视化
                    elif job_name.startswith("bulk relax"):
                        output = fw.get('output', {})
                        calcs_reversed = output.get('calcs_reversed', [{}])
                        input_data = output.get('input', {})
                        output_data = output.get('output', {})
                        
                        print('### task descript ###')
                        print(output.get('calc_type'))
                        print(output.get('task_label'))
                        print(calcs_reversed[0].get('vasp_version'))
                        print(output.get('completed_at'))
                        print(output.get('run_stats'))
                        
                        print('### input descript ###')
                        print(input_data.get('incar'))
                        print(input_data.get('kpoints'))
                        print(input_data.get('potcar'))
                        
                        print('### main output ###')
                        print(output_data.get('density'))
                        print(output_data.get('energy'))
                        print(output_data.get('forces'))
                        print(output_data.get('stress'))
                        print(output_data.get('structure'))
                        
        else:
            print(f"The task {flow_name} analysis is pending completion.")
    else:
        print(flow_info.get("state"))

except Exception as e:
    print(f"Error: {str(e)}")

finally:
    # 确保数据库连接关闭
    js.close()
