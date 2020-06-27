from subs_mat import  subs_elms_to_prefix,\
                      SubsStructure, StructureNode,\
                      subsMaterialsDatabase

from pymatgen.core.structure import Structure
import os
import shutil
import argparse


if __name__ == "__main__":

    def parse_argument():

        argparser = argparse.ArgumentParser()
        argparser.add_argument("--apply_step1",
                               default=False, action="store_true")
        args = argparser.parse_args()

        action = ["step2"]
        if args.apply_step1:
            action.append("step1")
        return action


    action = parse_argument()

    metadata = {"structuretype": "prototype"}

    if "step1" in action:

        current_step = "0"
        subs_db = subsMaterialsDatabase().\
                  initialize_with_dirs("Calc/MGI/mp-*", StructureNode)

        subs_elm_list = [[["Fe", "Cu"]]]
        subs_elm_list.append([["Ni", "Cu"]])
        subs_elm_list.append([["Cu", "Co"]])
        subs_elm_list.append([["Zn", "Cu"]])

        subs_elm_list.append([["Gd", "Y"]])
        subs_elm_list.append([["Yb", "Y"]])

        print(subs_elm_list)
        for subs_elm in subs_elm_list:

            print(subs_elm)

            subs_prefix = subs_elms_to_prefix(subs_elm)
            print(subs_prefix)

            for find in subs_db.find_subs_elems(subs_elm):
                print(find["species"])
                positionfilename = find["positionfile"]
                current_dir = find["current_dir"]
                positionfile_path = os.path.join(current_dir, positionfilename)
                uuid = find["uuid"]

                # load Structure
                structure = SubsStructure.from_file(positionfile_path)

                # make Structure
                structure2 = structure.substitute_elements(subs_elm)

                basedir = find["basedir_prefix"]
                print("basedir", basedir)
                # target apth
                basedir_prefix = ",".join([basedir, subs_prefix])
                print("basedir_prefix", basedir_prefix)

                structurenode = StructureNode(basedir_prefix)
                ret = structurenode.place_files(structure2, source_uuid=uuid,
                                                metadata=metadata)
                print(ret, basedir_prefix)

    if "step2" in action:
        subs_db = subsMaterialsDatabase().\
                  initialize_with_dirs("Calc/MGI/mp-*", StructureNode)
