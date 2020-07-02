from subs_mat import subsMaterialsDatabase
from pymatgen.core.structure import Structure

class IterativeCalcNode(StructureNode):
    def __init__(self, basedir_prefix):
        super().__init__(basedir_prefix)

        self.metadata_file = "metadata.json"

    def place_files(self):
        """make vasp input files and place into a new directory

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        current_dir = self.get_current_dir()
        metadata_file = os.path.join(current_dir,self.metadata_file)
        with open(metadata_file) as f:
            metadata = json.loads(f.read())
        positionpath = os.path.join(current_dir, metadata["positionfile"])
        structure = Structure.from_file(positionpath)

        new_dir,new_uuid = self.next_step()


if __name__ == "__main__":
    subs_db = subsMaterialsDatabase()
    filter = {"purpose": "converged_ionic", "status": "to_relax"}
    for x in subs_db.find(filter):
        hostname = x["hostname"]
        basedir_prefix = x["basedir_prefix"]
        current_dir = x["current_dir"]
        kind = x["kind"]
        positionfile = x["positionfile"]

        print(hostname, basedir_prefix, current_dir, kind, positionfile)
