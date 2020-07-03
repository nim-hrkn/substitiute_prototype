import argparse
from subs_mat import subsMaterialsDatabase


if __name__ == "__main__":

    def parse_argument():

        argparser = argparse.ArgumentParser()
        argparser.add_argument("--to_relax",
                               default=False, action="store_true")
        argparser.add_argument("--executed",
                               default=False, action="store_true")
        argparser.add_argument("--completed",
                               default=False, action="store_true")

        argparser.add_argument("--count",
                               default=False, action="store_true")
        args = argparser.parse_args()

        action = []
        if args.to_relax:
            action.append("to_relax")
        elif args.executed:
            action.append("executed")
        elif args.completed:
            action.append("completed")
        else:
            action.append("all")
        if args.count:
            action.append("count")
        return action

    action = parse_argument()

    subs_db = subsMaterialsDatabase()
    # collection = subs_db.collection

    if "to_relax" in action:
        filterstring = {"achievement": "to_relax"}
    elif "executed" in action:
        filterstring = {"achievement": "executed"}
    elif "completed" in action:
        filterstring = {"achievement": "completed"}

    if "all" in action:
        filterstring = {}

    if "count" in action:
        n = subs_db.count_documents(filterstring)
        print(n)
    else:
        for x in subs_db.find(filterstring):
            print(x)
