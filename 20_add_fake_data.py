from subsMat import subs_elms_to_prefix,\
                    SubsStructure, StructureNode,\
                    subsMaterialsDatabase

import os
import argparse
import random
import numpy as np


if __name__ == "__main__":

    random.seed(10)

    def parse_argument():
        """define argument parser
        """

        argparser = argparse.ArgumentParser()
        # argparser.add_argument("--increase_data",
        #                        default=False, action="store_true")
        args = argparser.parse_args()

        action = ["step2"]
        if True:
            action.append("step1")
        return action

    action = parse_argument()

    if "step1" in action:
        metadata = {"purpose": "prototype", "achievement": "completed"}

        subs_db = subsMaterialsDatabase().\
            initialize_with_dirs("Calc/MGI/mp-*", StructureNode)
        n = subs_db.count_documents()
        print("initial database size",n)

        subs_elm_list = [[["Fe", "Cu"]]]
        subs_elm_list.append([["Ni", "Cu"]])
        subs_elm_list.append([["Cu", "Co"]])
        subs_elm_list.append([["Zn", "Cu"]])

        subs_elm_list.append([["Gd", "Y"]])
        subs_elm_list.append([["Yb", "Y"]])


        count_list = []
        for subs_elm in subs_elm_list:

            print("subsitute elements",subs_elm)

            count = 0
            subs_prefix = subs_elms_to_prefix(subs_elm)

            for find in subs_db.find_subs_elems(subs_elm):
                basedir = find["basedir"]
                positionfilename = find["positionfile"]
                struc = StructureNode(basedir)
                current_dir = struc.get_currentdir()
                positionfile_path = os.path.join(current_dir, positionfilename)
                uuid = find["uuid"]

                # load Structure
                structure = SubsStructure.from_file(positionfile_path)

                # make Structure
                structure2 = structure.substitute_elements(subs_elm)

                # target apth
                basedir_prefix = ",".join([basedir, subs_prefix])

                structurenode = StructureNode(basedir_prefix)
                ret = structurenode.place_files(structure2, source_uuid=uuid,
                                                metadata=metadata)
                if ret:
                    count += 1

            print("{} directories are created.".format(count))
            count_list.append(count)

        count_list = np.array(count_list)
        print("total {} directories are created.".format(count_list.sum()))

    if "step2" in action:
        subs_db = subsMaterialsDatabase().\
                  initialize_with_dirs("Calc/MGI/mp-*", StructureNode)
        n = subs_db.count_documents()
        print("final database size",n)


