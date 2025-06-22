from jobflow_remote import JobController
from jobflow_remote import get_jobstore
from pymatgen.phonon.bandstructure import PhononBandStructureSymmLine
from pymatgen.phonon.dos import PhononDos
from pymatgen.phonon.plotter import PhononBSPlotter, PhononDosPlotter
import matplotlib.pyplot as plt
#
project_name = 'zcxphon_gpu'
db_id = '12253'
job_type = 'phonon workflow' #'double relax'/'adsorption workflow'/'phonon workflow'
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
                    
        else:
            print(f"The task {flow_name} analysis is pending completion.")
    else:
        print(flow_info.get("state"))

except Exception as e:
    print(f"Error: {str(e)}")

finally:
    # 确保数据库连接关闭
    js.close()

#
def plot_phonon_data(ph_bs, ph_dos, dos_label="phonon dos", save_path=None):
    """
    绘制 phonon 的能带结构和态密度图。

    参数:
        ph_bs (PhononBandStructureSymmLine): phonon 能带结构对象
        ph_dos (PhononDos): phonon 态密度对象
        dos_label (str): DOS 曲线标签
        save_path (str or Path): 如果提供，则将图像保存到指定路径

    返回:
        None: 直接显示图像或保存图像到文件。
    """
    # 绘制 DOS
    dos_plot = PhononDosPlotter()
    dos_plot.add_dos(label=dos_label, dos=ph_dos)
    dos_fig = dos_plot.get_plot()
    if save_path:
        dos_plot.save_plot(f"{save_path}_dos.png", fmt="png", dpi=300)
    plt.show()

    # 绘制 Band Structure
    bs_plot = PhononBSPlotter(bs=ph_bs)
    bs_fig = bs_plot.get_plot()
    if save_path:
        bs_plot.save_plot(f"{save_path}_bs.png", fmt="png", dpi=300)
    plt.show()

def plot_thermodynamic_properties(
    temperatures,
    free_energies,
    heat_capacities,
    internal_energies,
    entropies,
    title="Thermodynamic Properties vs Temperature",
    save_path=None,
    font_size=10,
    fig_size=(12, 8)
):
    """
    绘制温度相关的热力学性质曲线：自由能、热容、内能、熵。

    参数:
        temperatures (list or array): 温度值 (K)
        free_energies (list or array): 自由能 (J/mol/f.u.)
        heat_capacities (list or array): 热容 (J/(K·mol)/f.u.)
        internal_energies (list or array): 内能 (J/mol/f.u.)
        entropies (list or array): 熵 (J/(K·mol)/f.u.)
        title (str): 图表主标题
        save_path (str or Path): 如果提供，则将图像保存到指定路径
        font_size (int): 字体大小
        fig_size (tuple): 图像尺寸 (width, height)

    返回:
        None: 直接显示或保存图像。
    """
    # 设置全局字体大小
    plt.rcParams.update({'font.size': font_size})

    # 创建 2x2 子图
    fig, axs = plt.subplots(2, 2, figsize=fig_size)
    if title:
        fig.suptitle(title, y=1.02)

    # 自由能子图（左上）
    axs[0, 0].plot(temperatures, free_energies, 'b-', linewidth=2)
    axs[0, 0].set_title('Vibrational Free Energy')
    axs[0, 0].set_xlabel('Temperature (K)')
    axs[0, 0].set_ylabel('Free Energy (J/mol/f.u.)')
    axs[0, 0].grid(True, linestyle='--', alpha=0.6)

    # 热容子图（右上）
    axs[0, 1].plot(temperatures, heat_capacities, 'r-', linewidth=2)
    axs[0, 1].set_title('Heat Capacity')
    axs[0, 1].set_xlabel('Temperature (K)')
    axs[0, 1].set_ylabel('Cv (J/(K·mol)/f.u.)')
    axs[0, 1].grid(True, linestyle='--', alpha=0.6)

    # 内能子图（左下）
    axs[1, 0].plot(temperatures, internal_energies, 'g-', linewidth=2)
    axs[1, 0].set_title('Internal Energy')
    axs[1, 0].set_xlabel('Temperature (K)')
    axs[1, 0].set_ylabel('E (J/mol/f.u.)')
    axs[1, 0].grid(True, linestyle='--', alpha=0.6)

    # 熵变子图（右下）
    axs[1, 1].plot(temperatures, entropies, 'm-', linewidth=2)
    axs[1, 1].set_title('Entropy')
    axs[1, 1].set_xlabel('Temperature (K)')
    axs[1, 1].set_ylabel('S (J/(K·mol)/f.u.)')
    axs[1, 1].grid(True, linestyle='--', alpha=0.6)

    # 自动调整子图间距
    plt.tight_layout()

    # 保存图像
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    # 显示图像
    plt.show()
