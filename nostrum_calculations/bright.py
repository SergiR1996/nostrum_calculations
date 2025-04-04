import os


def jobArrays(
    jobs,
    script_name=None,
    job_name=None,
    ntasks=1,
    gpus=1,
    mem_per_cpu=None,
    partition="standard-gpu",
    cpus_per_task=None,
    output=None,
    mail=None,
    time=None,
    module_purge=False,
    modules=None,
    conda_env=None,
    unload_modules=None,
    program=None,
    jobs_range=None,
    group_jobs_by=None,
    pythonpath=None,
    local_libraries=False,
    msd_version=None,
    mpi=False,
    pathMN=None,
    extras=[],
    exports=None,
):
    """
    Set up job array scripts for marenostrum slurm job manager.

    Parameters
    ==========
    jobs : list
        List of jobs. Each job is a string representing the command to execute.
    script_name : str
        Name of the SLURM submission script.
    jobs_range : (list, tuple)
        The range of job IDs to be included in the job array (one-based numbering).
        This restart the indexing of the slurm array IDs, so keep count of the original
        job IDs based on the supplied jobs list. Also, the range includes the last job ID.
        Useful when large IDs cannot enter the queue.
    group_jobs_by : int
        Group jobs to enter in the same job array (useful for launching many short
        jobs when there are a max_job_allowed limit per user.
    local_libraries : bool
        Add local libraries (e.g., prepare_proteins) to PYTHONPATH?
    """

    # Check input
    if isinstance(jobs, str):
        jobs = [jobs]

    if jobs_range != None:
        if (
            not isinstance(jobs_range, (list, tuple))
            or len(jobs_range) != 2
            or not all([isinstance(x, int) for x in jobs_range])
        ):
            raise ValueError(
                "The given jobs_range must be a tuple or a list of 2-integers"
            )

    # Group jobs to enter in the same job array (useful for launching many short
    # jobs when there are a max_job_allowed limit per user.)
    if isinstance(group_jobs_by, int):
        grouped_jobs = []
        gj = ""
        for i, j in enumerate(jobs):
            gj += j
            if (i + 1) % group_jobs_by == 0:
                grouped_jobs.append(gj)
                gj = ""
        if gj != "":
            grouped_jobs.append(gj)
        jobs = grouped_jobs

    elif not isinstance(group_jobs_by, type(None)):
        raise ValueError("You must give an integer to group jobs by this number.")

    # Check PYTHONPATH variable
    if pythonpath == None:
        pythonpath = []

    if pathMN == None:
        pathMN = []

    #! Programs
    available_programs = ["gromacs", "alphafold", "hmmer", "asitedesign", "blast", "pyrosetta", "openmm","Q6",
                          "bioml", "rosetta", 'bioemu','PLACER']

    if program != None:
        if program not in available_programs:
            raise ValueError(
                "Program not found. Available programs: "
                + " ,".join(available_programs)
            )

    if program == "gromacs":
        if modules == None:
            modules = ["cuda", "nvidia-hpc-sdk/23.11", "gromacs/2023.3"]
        else:
            modules += ["cuda", "nvidia-hpc-sdk/23.11", "gromacs/2023.3"]
        extras = [
            "export SLURM_CPU_BIND=none",
            "export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK",
            "export GMX_ENABLE_DIRECT_GPU_COMM=1",
            "export GMX_GPU_PME_DECOMPOSITION=1",
            'GMXBIN="mpirun --bind-to none -report-bindings gmx_mpi"',
        ]

        if cpus_per_task > 1:
            warning_message = """
            ----------------------------------------------------------------------------------------------
            |                                          WARNING                                           |
            ----------------------------------------------------------------------------------------------

            With cpus_per_task != 1 you might encounter the following
            GROMACS error:

            | Fatal error:
            | There is no domain decomposition for {cpus_per_task} ranks that is
            | compatible with the given box and a minimum cell size of
            | ___ nm
            | Change the number of ranks or mdrun option -rcon or -dds or
            | your LINCS settings. Look in the log file for details on the
            | domain decomposition
            """
            print(warning_message)

        # Update mpi and omp options to match cpu and gpus
        gromacs_jobs = []
        for job in jobs:
            gromacs_jobs.append(job.replace('mdrun', f'mdrun -pin on -pinoffset 0'))
        jobs = gromacs_jobs

    if program == 'openmm':
        openmm_modules = ["anaconda", "cuda/11.8"]
        if modules == None:
            modules = openmm_modules
        else:
            modules += openmm_modules

        conda_env = "/gpfs/projects/bsc72/conda_envs/openmm_cuda"


    if program == 'bioml':
        bioml_modules = ["anaconda", "perl/5.38.2"]
        module_purge = True
        if modules == None:
            modules = bioml_modules
        else:
            modules += bioml_modules

        conda_env = "/gpfs/projects/bsc72/conda_envs/bioml"


    if program == "alphafold":
        if modules == None:
            modules = ["singularity", "alphafold/2.3.2", "cuda"]
        else:
            modules += ["singularity", "alphafold/2.3.2", "cuda"]

    if program == 'blast':
        if modules == None:
            modules = ["blast"]
        else:
            modules += ["blast"]

    if program == 'pyrosetta':
        pyrosetta_modules = []
        if modules == None:
            modules = pyrosetta_modules
        else:
            modules += pyrosetta_modules
        if mpi:
            conda_env = "/gpfs/projects/bsc72/conda_envs/mood"
        else:
            conda_env = "/gpfs/projects/bsc72/MN4/bsc72/conda_envs/pyrosetta"

    if program == "hmmer":
        hmmer_modules = ["anaconda"]
        if modules == None:
            modules = hmmer_modules
        else:
            modules += hmmer_modules
        conda_env = "/gpfs/projects/bsc72/conda_envs/hmm"

    if program == 'Q6':
        q6_modules = ['oneapi','q6']
        if modules == None:
            modules = q6_modules
        else:
            modules += q6_modules

        extras = ['source /home/bsc/bsc072181/programs/qtools/bin/qtools/qtools_init.sh']

    if program == "asitedesign":
        if modules == None:
            modules = ["anaconda", "intel", "openmpi", "mkl", "gcc", "bsc"]
        else:
            modules += ["anaconda", "intel", "openmpi", "mkl", "gcc", "bsc"]
        pythonpath.append("/gpfs/projects/bsc72/Repos/AsiteDesign")
        pathMN.append("/gpfs/projects/bsc72/Repos/AsiteDesign")
        conda_env = "/gpfs/projects/bsc72/conda_envs/asite"

    if program == 'rosetta':
        rosetta_modules = ['gcc/12.3.0', 'rosetta/3.14']
        if modules == None:
            modules = rosetta_modules
        else:
            modules += rosetta_modules

    if program == 'bioemu':
        if modules == None:
            modules = ["Miniconda3"]
        else:
            modules += ["Miniconda3"]
        conda_env = '/home/sroda/.conda/envs/BioEmu'
        if exports == None:
            exports = []
        exports += ['COLABFOLD_DIR=/home/sroda/.bioemu_colabfold/']

    if program == 'PLACER':
        if modules == None:
            modules = ["Miniconda3"]
        else:
            modules += ["Miniconda3"]
        extras = ["source activate /home/sroda/.conda/envs/PLACER"]

    #! Partitions
    available_partitions = ["short", "gpu_short", "standard-gpu", "standard-cpu"]

    if job_name == None:
        raise ValueError("job_name == None. You need to specify a name for the job")
    if output == None:
        output = job_name
    if partition not in available_partitions:
        raise ValueError(
            "Wrong partition selected. Available partitions are:"
            + ", ".join(available_partitions)
        )

    if script_name == None:
        script_name = "slurm_array.sh"
    elif not script_name.endswith(".sh"):
        script_name += ".sh"

    if modules != None:
        if isinstance(modules, str):
            modules = [modules]
        if not isinstance(modules, list):
            raise ValueError(
                "Modules to load must be given as a list or as a string (for loading one module only)"
            )
    if unload_modules != None:
        if isinstance(unload_modules, str):
            unload_modules = [unload_modules]
        if not isinstance(unload_modules, list):
            raise ValueError(
                "Modules to unload must be given as a list or as a string (for unloading one module only)"
            )
    if conda_env != None:
        if not isinstance(conda_env, str):
            raise ValueError("The conda environment must be given as a string")

    if time != None:
        time = time
    elif "short" == partition and time == None:
        time = 2
    elif "gpu_short" == partition and time == None:
        time = 8
    else:
        if time > 48:
            print(
                "Setting time at maximum allowed for the bsc_ls partition (48 hours)."
            )
            time = 48

    # Slice jobs if a range is given
    if jobs_range != None:
        jobs = jobs[jobs_range[0] - 1 : jobs_range[1]]

    # Write jobs as array
    with open(script_name, "w") as sf:
        sf.write("#!/bin/bash\n")
        sf.write("#SBATCH --job-name=" + job_name + "\n")
        if partition in ["short", "gpu_short"]:
            sf.write("#SBATCH --qos=" + partition + "\n")
        else:
            sf.write("#SBATCH --qos=normal" + "\n")
        sf.write("#SBATCH --partition=" + partition + "\n")
        sf.write("#SBATCH --time=" + str(time) + ":00:00\n")
        sf.write("#SBATCH --ntasks " + str(ntasks) + "\n")
        if "gpu" in partition:
            sf.write("#SBATCH --gres gpu:" + str(gpus) + "\n")
            sf.write("#SBATCH --constraint=gpu " + "\n")
            cpus = gpus * 8
            sf.write("#SBATCH --cpus-per-task " + str(cpus) +  "\n")
        if mem_per_cpu != None:
            sf.write("#SBATCH --mem-per-cpu " + str(mem_per_cpu) + "\n")
        if cpus_per_task != None:
            sf.write("#SBATCH --cpus-per-task " + str(cpus_per_task) + "\n")
        sf.write("#SBATCH --array=1-" + str(len(jobs)) + "\n")
        sf.write("#SBATCH --output=" + output + "_%a_%A.out\n")
        sf.write("#SBATCH --error=" + output + "_%a_%A.err\n")
        if mail != None:
            sf.write("#SBATCH --mail-user=" + mail + "\n")
            sf.write("#SBATCH --mail-type=END,FAIL\n")
        sf.write("\n")

        if module_purge:
            sf.write("module purge\n")
        if unload_modules != None:
            for module in unload_modules:
                sf.write("module unload " + module + "\n")
            sf.write("\n")
        if modules != None:
            for module in modules:
                sf.write("module load " + module + "\n")
            sf.write("\n")
        if conda_env != None:
            sf.write("source activate " + conda_env + "\n")
            sf.write("\n")

        if exports != None:
            for export in exports:
                sf.write(f"export {export}\n")
            sf.write("\n")

        if cpus_per_task != None:
            sf.write("export SRUN_CPUS_PER_TASK=${SLURM_CPUS_PER_TASK}" + "\n")

        for pp in pythonpath:
            sf.write("export PYTHONPATH=$PYTHONPATH:" + pp + "\n")
            sf.write("\n")

        for pp in pathMN:
            sf.write("export PATH=$PATH:" + pp + "\n")
            sf.write("\n")

        for extra in extras:
            sf.write(extra + "\n")

    for i in range(len(jobs)):
        with open(script_name, "a") as sf:
            sf.write("if [[ $SLURM_ARRAY_TASK_ID = " + str(i + 1) + " ]]; then\n")
            sf.write(jobs[i])
            if jobs[i].endswith("\n"):
                sf.write("fi\n")
            else:
                sf.write("\nfi\n")
            sf.write("\n")

    if conda_env != None:
        with open(script_name, "a") as sf:
            sf.write("conda deactivate \n")
            sf.write("\n")


def setUpPELEForBright(
    jobs,
    general_script="pele_slurm.sh",
    scripts_folder="pele_slurm_scripts",
    print_name=False,
    partition='standard-cpu',
    **kwargs
):
    """
    Creates submission scripts for Bright for each PELE job inside the jobs variable.

     Parameters
    ==========
    jobs : list
        Commands for run PELE. This is the output of the setUpPELECalculation() function.
    general_script : str
        Name of the script file to be created.
    scripts_folder : str
        Name of the folder where the scripts will be saved.
    print_name : bool
        Print the name of the job in the submission script.
    ntasks: int
        Number of tasks. For PELE is equivalent at number of CPUs.
    time: int
        Maximum time per job, default 35 hours.
    nodes: str
        Name of the node to use. node005 has different architecture, if node005 is use with another node no output will be written. Default node005
    """

    if not os.path.exists(scripts_folder):
        os.mkdir(scripts_folder)

    if not general_script.endswith(".sh"):
        general_script += ".sh"

    zfill = len(str(len(jobs)))
    with open(general_script, "w") as ps:
        for i, job in enumerate(jobs):
            job_name = str(i + 1).zfill(zfill) + "_" + job.split("\n")[0].split("/")[1]
            singleJob(
                job,
                job_name=job_name,
                script_name=scripts_folder + "/" + job_name + ".sh",
                program="pele",
                partition=partition,
                **kwargs
            )
            if print_name:
                ps.write("echo Launching job " + job_name + "\n")
            ps.write("sbatch " + scripts_folder + "/" + job_name + ".sh\n")


def singleJob(
    job,
    script_name=None,
    job_name=None,
    ntasks=1,
    cpus_per_task=None,
    gpus=1,
    mem_per_cpu=None,
    partition=None,
    threads=None,
    output=None,
    mail=None,
    time=None,
    pythonpath=None,
    modules=None,
    conda_env=None,
    unload_modules=None,
    program=None,
    pathMN=None,
    exports=None,
    nodes=None
):

    # Check PYTHONPATH variable
    if pythonpath == None:
        pythonpath = []

    if pathMN == None:
        pathMN = []

    available_programs = ["pele"]
    if program != None:
        if program not in available_programs:
            raise ValueError(
                "Program not found. Available progams: " + " ,".join(available_programs)
            )
    available_nodes = ["node001","node002", "node003","node004","node005"]
    if nodes != None:
        if nodes not in available_nodes:
            raise ValueError(
                "Node ot found. Use one of the available nodes: " + " ,".join(available_nodes)
            )
        
    if program == "pele":
        if modules == None:
            modules = []
        modules += modules + [
            "PELE/1.8.1",
            "Miniconda3/4.9.2",
            "Schrodinger"
        ]
        conda_env = "/home/sroda/.conda/envs/pele_platform_2025"
        #I think these are not needed
        exports = ['PELE="/eb/x86_64/software/PELE/1.8.1/"',
                   'PELE_EXEC="/eb/x86_64/software/PELE/1.8.1/bin/PELE_mpi"',
                   'PELE_LICENSE="/shared/work/NBD_Utilities/PELE/licenses"',
                   'SRUN=1']

    available_partitions = ["short", "gpu_short", "standard-gpu", "standard-cpu"]
    if job_name == None:
        raise ValueError("job_name == None. You need to specify a name for the job")
    if output == None:
        output = job_name
    if partition == None:
        raise ValueError(
            "You must select a partion. Available partitions are:"
            + ", ".join(available_partitions)
        )
    if partition not in available_partitions:
        raise ValueError(
            "Wrong partition selected. Available partitions are:"
            + ", ".join(available_partitions)
        )
    if script_name == None:
        script_name = "slurm_job.sh"
    if modules != None:
        if isinstance(modules, str):
            modules = [modules]
        if not isinstance(modules, list):
            raise ValueError(
                "Modules to load must be given as a list or as a string (for loading one module only)"
            )
    if unload_modules != None:
        if isinstance(unload_modules, str):
            unload_modules = [unload_modules]
        if not isinstance(unload_modules, list):
            raise ValueError(
                "Modules to unload must be given as a list or as a string (for unloading one module only)"
            )
    if conda_env != None:
        if not isinstance(conda_env, str):
            raise ValueError("The conda environment must be given as a string")

    if exports != None:
        if isinstance(exports, str):
            exports = [exports]
        if not isinstance(exports, list):
            raise ValueError(
                "Exports to load must be given as a list or as a string (for loading one export only)"
            )

    if isinstance(time, int):
        time = (time, 0)
    if partition in ["short", "gpu_short"] and time == None:
        time = (2, 0)
    elif partition in ["short", "gpu_short"] and time != None:
        if time[0] * 60 + time[1] > 120:
            print("Setting time at maximum allowed for the debug partition (2 hours).")
            time = (2, 0)
    elif partition in ["standard-cpu", "standard-gpu"] and time == None:
        time = (48, 0)
    elif partition in ["standard-cpu", "standard-gpu"] and time != None:
        if time[0] * 60 + time[1] > 2880:
            print(
                "Setting time at maximum allowed for the bsc_ls partition (48 hours)."
            )
            time = (48, 0)

    # Write jobs as array
    with open(script_name, "w") as sf:
        sf.write("#!/bin/bash\n")
        sf.write("#SBATCH --job-name=" + job_name + "\n")
        if partition in ["short", "gpu_short"]:
            sf.write("#SBATCH --qos=" + partition + "\n")
        else:
            sf.write("#SBATCH --qos=normal" + "\n")
        sf.write("#SBATCH --partition=" + partition + "\n")
        sf.write("#SBATCH --time=" + str(time[0]) + ":" + str(time[1]) + ":00\n")
        sf.write("#SBATCH --ntasks " + str(ntasks) + "\n")
        if cpus_per_task != None:
            sf.write("#SBATCH --cpus-per-task " + str(cpus_per_task) + "\n")
        if "gpu" in partition:
            sf.write("#SBATCH --gres gpu:" + str(gpus) + "\n")
            cpus = gpus*8
            sf.write("#SBATCH --cpus-per-task" + str(cpus) + "\n")
        if mem_per_cpu != None:
            sf.write("#SBATCH --mem-per-cpu " + str(mem_per_cpu) + "\n")
        if threads != None:
            sf.write("#SBATCH -c " + str(threads) + "\n")
        if nodes != None:
            sf.write("#SBATCH --nodelist=" + str(nodes) +"\n")
            sf.write("#SBATCH --nodes=1" + "\n")
        else:
            sf.write("#SBATCH --nodelist=node005 " +"\n")
            sf.write("#SBATCH --nodes=1" + "\n")
        sf.write("#SBATCH --output=" + output + "_%a_%A.out\n")
        sf.write("#SBATCH --error=" + output + "_%a_%A.err\n")
        if mail != None:
            sf.write("#SBATCH --mail-user=" + mail + "\n")
            sf.write("#SBATCH --mail-type=END,FAIL\n")
        sf.write("\n")
        # ---

        if unload_modules != None:
            for module in unload_modules:
                sf.write("module unload " + module + "\n")
            sf.write("\n")
        if modules != None:
            if program != "pele":
                sf.write("module purge \n")
            for module in modules:
                sf.write("module load " + module + "\n")
            sf.write("\n")
        if conda_env != None:
            sf.write("source activate " + conda_env + "\n")
            sf.write("\n")

        if exports != None:
            for export in exports:
                sf.write(f"export {export}\n")
            sf.write("\n")

        for pp in pythonpath:
            sf.write("export PYTHONPATH=$PYTHONPATH:" + pp + "\n")
            sf.write("\n")

        for pp in pathMN:
            sf.write("export PATH=$PATH:" + pp + "\n")
            sf.write("\n")

    with open(script_name, "a") as sf:
        sf.write(job)
        if not job.endswith("\n"):
            sf.write("\n\n")
        else:
            sf.write("\n")

    if conda_env != None:
        with open(script_name, "a") as sf:
            sf.write("conda deactivate \n")
            sf.write("\n")