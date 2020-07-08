
import random
from collections import Counter

from subsMat.database import SubsMaterialsDatabase
from subsMat.node import StructureNode

from subsMat.fakenode import fakeVaspRunNode

if __name__ == "__main__":
    random.seed(10)
    subs_db = SubsMaterialsDatabase()
    filter = {"purpose": "converged_ionic", "achievement": "executed"}

    result_list = []
    for x in subs_db.find(filter):
        id_ = x["_id"]
        hostname = x["hostname"]
        basedir_prefix = x["basedir"]
        # current_dir = StructureNode(basedir_prefix).get_currentdir()
        # kind = x["kind"]
        # positionfile = x["positionfile"]

        calc = fakeVaspRunNode(basedir_prefix)
        result = calc.check_result()
        result_list.append(result)

        subs_db.delete_one({"_id": id_})
        subs_db.add_files_under(basedir_prefix, StructureNode)

    print(len(result_list), "data processed.")
    result = [x["achievement"] for x in result_list]
    counter = Counter(result)
    print(counter)
