import json
import os
import random
from pymatgen.core.structure import Structure
from pymatgen.io.vasp.sets import MITRelaxSet

from subs_mat import subsMaterialsDatabase, StructureNode

class fakeVaspRunNode(StructureNode):
    def __init__(self, basedir_prefix):
        super().__init__(basedir_prefix)

        self.result_status_file = "outcar.json"
        self.accept_ratio = 0.20

    def make_MITRelaxSet_vasp_inputfiles(self, structure, targetdir,
                                        write_all=True):
        """make VASP input files

        Parameters
        ----------
        structure: Structure
            material structure

        targetdir: string
            target dirctory

        write_all: bool = True
            flag to use pymatgen.MITRelaxSet.write_input() or not

        Returns
        -------
        boolean: always True

        """

        outputdir = targetdir

        mitset = MITRelaxSet(structure, standardize=True)

        if write_all:
            mitset.write_input(outputdir)
        else:
            kpoint = mitset.kpoints
            incar = mitset.incar
            poscar = mitset.poscar

            poscarfile = os.path.join(outputdir, "POSCAR")
            poscar.write_file(poscarfile)
            kpointfile = os.path.join(outputdir, "KPOINT")
            kpoint.write_file(kpointfile)
            incarfile = os.path.join(outputdir, "INCAR")
            incar.write_file(incarfile)
            # skip writing "POTCAR" for debug

        return True

    def place_files(self):
        """make vasp input files and place into a new directory

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        current_dir = self.get_currentdir()
        metadata_file = os.path.join(current_dir,self.metadata_file)
        with open(metadata_file) as f:
            metadata = json.loads(f.read())
        positionpath = os.path.join(current_dir, metadata["positionfile"])
        structure = Structure.from_file(positionpath)
        source_uuid = self.read_currentdir_uuid()
        self.set_new_step()
        metadata = {"purpose": "converged_ionic", "achievement": "to_relax" }
        super().place_files(structure, source_uuid = source_uuid, metadata=metadata)
        current_dir = self.get_currentdir()
        print("currentdir", current_dir)
        
        self.make_MITRelaxSet_vasp_inputfiles(structure, current_dir, 
                                              write_all=False)

    def run(self):
        """dry run
        place outcar.json file 

        Parameters
        ----------
        None

        Returns
        -------
        dic 
        """

        self.update_currentdir_metadata({"achievement": "running"})

    def run_result(self):
        """get result of dry run

        Parameters
        ----------
        None

        Returns
        -------
        dic
        """

        self.update_currentdir_metadata({"achievement": "executed"})
        i_conv = random.random() > self.accept_ratio
        e_conv = True
        dic = {"converged_electronic": e_conv, "converged_ionic": i_conv}
        print(dic)
        filename = os.path.join(self.get_currentdir(), self.result_status_file)
        with open(filename,"w") as f:
            f.write(json.dumps(dic))
        return dic  

    def check_result(self):
        """check vasp result

        Parameters
        ----------
        None

        Returns
        -------
        dict of convergence
        """
        filename = os.path.join(self.get_currentdir(), self.result_status_file)
        with open(filename) as f:
            dic = json.loads(f.read())

        i_conv = dic["converged_ionic"]
        # change metadata
        dicm = self.load_currentdir_metadata()
        if i_conv:
            if dicm["purpose"]=="converged_ionic":
                dicm["achievement"] = "completed"
        else:
            if dicm["purpose"]=="converged_ionic":
                dicm["achievement"] = "to_relax"
        self.save_currentdir_metadata(dicm)        

        return dic  


