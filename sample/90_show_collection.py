import argparse
from subsMat.database import SubsMaterialsDatabase


if __name__ == "__main__":

    def parse_argument():
        """define argument parser
        """
        argparser = argparse.ArgumentParser()
        argparser.add_argument("--detail",
                               choices=["to_relax",
                                        "running", "executed",
                                        "completed"])
        args = argparser.parse_args()

        return args.detail

    def make_filterdict(action):
        """make filter string

        Parameters
        ----------
        action: string

        Returns
        -------
        filter dict
        """
        if "to_relax" in action:
            filterdic = {"achievement": "to_relax"}
        elif "running" in action:
            filterdic = {"achievement": "running"}
        elif "executed" in action:
            filterdic = {"achievement": "executed"}
        elif "completed" in action:
            filterdic = {"achievement": "completed"}
        else:
            filterdic = {}
        return filterdic

    action = parse_argument()

    subs_db = SubsMaterialsDatabase()
    result = []
    for process in ["all", "to_relax", "running", "executed", "completed"]:

        filterdic = make_filterdict(process)
        n = subs_db.count_documents(filterdic)
        result.append([process, n])

    print(result)

    if action is not None:
        filterdic = make_filterdict(action)
        for doc in subs_db.find(filterdic):
            print(doc)
