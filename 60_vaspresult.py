
import random

from subs_mat import subsMaterialsDatabase, StructureNode

from fakevasprun import fakeVaspRunNode

if __name__ == "__main__":
    random.seed(10)
    subs_db = subsMaterialsDatabase()
    filter = {"purpose": "converged_ionic", "achievement": "executed"}
    for x in subs_db.find(filter):
        id_ = x["_id"]
        hostname = x["hostname"]
        basedir_prefix = x["basedir"]
        current_dir = StructureNode(basedir_prefix).get_currentdir()
        kind = x["kind"]
        positionfile = x["positionfile"]

        print(id_,  basedir_prefix)
        calc = fakeVaspRunNode(basedir_prefix)
        result = calc.check_result()

        print(result)

        subs_db.delete_one({"_id": id})
        subs_db.add_files_under(basedir_prefix, StructureNode)
