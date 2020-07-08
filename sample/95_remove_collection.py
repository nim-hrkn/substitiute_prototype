from subsMat.database import SubsMaterialsDatabase


if __name__ == "__main__":
    subs_db = SubsMaterialsDatabase()
    subs_db.collection_remove()
    print("collection is removed")
