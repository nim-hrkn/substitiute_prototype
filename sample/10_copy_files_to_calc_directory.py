
import glob
import os
import random
from subsMat.structure import SubsStructure
from subsMat.node import StructureNode


def copy_files_to_calc_directory(souce_prefix, target_base, metadata):
    """create basedir_prefix directory
    copy OUTCAR,POSCAR,*cif to basedir_prefix/

    Parameters
    ----------
    source_prefix: string
        directory name to pass glob

    basedir_prefix: string
        base directory name to write

    metadata: dict
        metadata to save

    Returns
    -------
    None

    """

    filelist = list(glob.glob(souce_prefix))

    count = 0

    for filepath in filelist:
        filepath_ce_list = list(glob.glob(os.path.join(filepath, "[CE]_*")))
        if len(filepath_ce_list) > 1:
            print(">1", filepath_ce_list)
            continue
        if len(filepath_ce_list) == 0:
            print("no files", filepath_ce_list)
            raise
        filepath_ce = glob.glob(os.path.join(filepath, "[CE]_*"))[0]
        dirsplits = filepath_ce.split("/")
        basedir_prefix = os.path.join(target_base, dirsplits[3])

        structure_file = glob.glob(os.path.join(filepath_ce, "*.cif"))[0]
        structure = SubsStructure.from_file(structure_file)

        structure2 = structure.randomize_structure()

        structurenode = StructureNode(basedir_prefix)
        ret = structurenode.place_files(structure2, metadata=metadata)
        if ret:
            count += 1

    return count


if __name__ == "__main__":
    random.seed(10)
    metadata = {"purpose": "prototype", "achievement": "completed"}
    n = copy_files_to_calc_directory("../Pham-RT/rt_stage5/RUN.00?/mp-*",
                                     "Calc/MGI", metadata)
    print("{} directories created.".format(n))
