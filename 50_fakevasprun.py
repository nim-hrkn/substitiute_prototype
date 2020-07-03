import random

from subs_mat import subsMaterialsDatabase, StructureNode

from fakevasprun import fakeVaspRunNode


if __name__ == "__main__":
    random.seed(10)

    subs_db = subsMaterialsDatabase()
    filter = {"purpose": "converged_ionic", "achievement": "to_relax"}
    for x in subs_db.find(filter):
        id_ = x["_id"]
        hostname = x["hostname"]
        basedir_prefix = x["basedir"]
        struc = StructureNode(basedir_prefix)
        current_dir = struc.get_currentdir()
        kind = x["kind"]
        positionfile = x["positionfile"]

        print(id_, hostname, basedir_prefix, current_dir, kind, positionfile)
        calc = fakeVaspRunNode(basedir_prefix)
        calc.place_files()
        calc.run()

        calc.run_result()
        subs_db.delete_one({"_id": id_})
        subs_db.add_files_under(basedir_prefix, StructureNode)
