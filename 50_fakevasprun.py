import json
import os
import random
from pymatgen.core.structure import Structure
from pymatgen.io.vasp.sets import MITRelaxSet

from subs_mat import subsMaterialsDatabase, StructureNode

class fakeVaspRunNode(StructureNode):
    def __init__(self, basedir_prefix):
        super().__init__(basedir_prefix)

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
        metadata = {"purpose": "converged_ionic", "status": "to_relax" }
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


        i_conv = random.random()> 0.3
        e_conv = True
        dic = {"converged_electronic": e_conv, "converged_ionic": i_conv}
        print(dic)
        filename = os.path.join(self.get_currentdir(), "outcar.json")
        with open(filename,"w") as f:
            f.write(json.dumps(dic))
        return dic  



if __name__ == "__main__":
    subs_db = subsMaterialsDatabase()
    filter = {"purpose": "converged_ionic", "status": "to_relax"}
    for x in subs_db.find(filter):
        id_ = x["_id"]
        hostname = x["hostname"]
        basedir_prefix = x["basedir_prefix"]
        current_dir = x["current_dir"]
        kind = x["kind"]
        positionfile = x["positionfile"]

        print(id_, hostname, basedir_prefix, current_dir, kind, positionfile)
        calc = fakeVaspRunNode(basedir_prefix)
        calc.place_files()
        subs_db.delete_one({"_id":id_})
        subs_db.add_files_under(basedir_prefix, StructureNode)
        calc.run()

