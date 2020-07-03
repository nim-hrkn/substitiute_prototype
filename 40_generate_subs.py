import os
import random
from subs_mat import subsMaterialsDatabase,\
                        subs_elms_to_prefix,\
                        SubsStructure, StructureNode
from pymatgen.core.structure import Structure
from pymatgen.analysis.structure_matcher import StructureMatcher


if __name__ == "__main__":

    random.seed(10)

    subs_db = subsMaterialsDatabase()

    subs_elm_list = [[["Cu", "Fe"]]]
    subs_elm_list.append([["Cu", "Ni"]])
    subs_elm_list.append([["Cu", "Co"]])

    for subs_elm in subs_elm_list:
        print("substitute", subs_elm)

        for x in subs_db.find_subs_elems(subs_elm):
            basedir = x["basedir"]
            positionfilename = x["positionfile"]
            struc = StructureNode(basedir)
            current_dir = struc.get_currentdir()
            position_path = os.path.join(current_dir, positionfilename)
            source_uuid = x["uuid"]
            struc = SubsStructure.from_file(position_path)
            new_struc = struc.substitute_elements(subs_elm)
            new_basedir = ",".join([x["basedir"],
                                   subs_elms_to_prefix(subs_elm)])
            species = new_struc.element_list()
            nspecies = len(species)

            # make new structure if not matched (not already existed)

            struc_matched = False

            find_comp = subs_db.find({"nspecies": nspecies,
                                      "species": species})
            for y in find_comp:
                basedir_comp = x["basedir"]
                positionfilename_comp = y["positionfile"]
                struc_comp = StructureNode(basedir_comp)
                current_dir_comp = struc_comp.get_currentdir()
                filename_comp = os.path.join(current_dir_comp,
                                             positionfilename_comp)
                struc_comp = Structure.from_file(filename_comp)
                struc_matcher = StructureMatcher()
                match = struc_matcher.fit(new_struc, struc_comp)
                if match:
                    struc_matched = True

            if not struc_matched:
                print("execute new struc")
                print("on new_basedir", new_basedir)
                metadata = {"purpose": "converged_ionic",
                            "achievement": "to_relax"}
                structurenode = StructureNode(new_basedir)
                structurenode.place_files(new_struc, source_uuid=source_uuid,
                                          metadata=metadata)
                subs_db.add_files_under(new_basedir, StructureNode)
