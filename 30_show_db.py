import argparse
from subs_mat import subsMaterialsDatabase


if __name__ == "__main__":

    def parse_argument():

        argparser = argparse.ArgumentParser()
        argparser.add_argument("--only_relax",
                               default=False, action="store_true")
        argparser.add_argument("--count",
                               default=False, action="store_true")
        args = argparser.parse_args()

        action = []
        if args.only_relax:
            action.append("only_relax")
        else:
            action.append("all")
        if args.count:
            action.append("count")
        return action


    action = parse_argument()

    subs_db = subsMaterialsDatabase()
    # collection = subs_db.collection

    if "only_relax" in action:
        filter = {"structuretype": "to_relax"}
    if "all" in action:
        filter = {}

    if "count" in action:
        n = subs_db.count_documents(filter)
        print(n)
    else:
        for x in subs_db.find(filter):
            print(x)

 
