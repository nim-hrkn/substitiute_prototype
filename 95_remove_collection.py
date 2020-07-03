import argparse
from subsMat import subsMaterialsDatabase


if __name__ == "__main__":
    subs_db = subsMaterialsDatabase()
    subs_db.collection_remove()
    print("collection is removed")
