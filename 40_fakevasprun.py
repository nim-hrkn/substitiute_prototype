import random
from collections import Counter

from subsMat.database import SubsMaterialsDatabase
from subsMat.node import StructureNode

from subsMat.fakenode import fakeVaspRunNode


if __name__ == "__main__":

    def run_them():
        random.seed(10)
        subs_db = SubsMaterialsDatabase()
        filterstring = {"purpose": "converged_ionic", "achievement": "to_relax"}
        for x in subs_db.find(filterstring):
            id_ = x["_id"]
            hostname = x["hostname"]
            basedir_prefix = x["basedir"]
            struc = StructureNode(basedir_prefix)
            # kind = x["kind"]
            # positionfile = x["positionfile"]

            print("run", basedir_prefix)
            calc = fakeVaspRunNode(basedir_prefix)
            calc.place_files()
            calc.run()
            subs_db.delete_one({"_id": id_})
            subs_db.add_files_under(basedir_prefix, StructureNode)

        n = subs_db.count_documents({ "achievement": "running"})
        print(n,"running")

    if False:
        def get_run_result():
            random.seed(10)
            subs_db = SubsMaterialsDatabase()
            result_list = []
            filterstring = {"purpose": "converged_ionic", "achievement": "running"}
            for x in subs_db.find(filterstring):
                id_ = x["_id"]
                hostname = x["hostname"]
                basedir_prefix = x["basedir"]
                calc = fakeVaspRunNode(basedir_prefix)
                result_list.append(calc.run_result())
                subs_db.delete_one({"_id": id_})
                subs_db.add_files_under(basedir_prefix, StructureNode)

            result = [ x["converged_ionic"] for x in result_list ]
            counter = Counter(result)
            print(counter,"True if converged")
            n = subs_db.count_documents({ "achievement": "executed"})
            print(n,"executed")

    run_them()
