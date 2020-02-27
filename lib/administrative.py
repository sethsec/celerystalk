import tarfile
import lib.db
import os
import time

def backup_all_workspaces(backup_file=None):
    cs_path = lib.db.get_current_install_path()[0][0]
    timestr = time.strftime("%Y%m%d-%H%M%S")
    backup_file = os.path.join(cs_path,"cs_backup_" + timestr + ".tar.gz")
    cs_path = lib.db.get_current_install_path()[0][0]
    workspaces = lib.db.get_all_workspaces()
    backup_filename = backup_file
    with tarfile.open(backup_filename, mode='w:gz') as archive:
        archive.add(os.path.join(cs_path,'csdb.sqlite3'))
        for workspace in workspaces:
            archive.add(workspace[1], recursive=True)
    print("[+] Successfully backed up DB and [{0}] workspaces to [{1}]".format(len(workspaces),backup_filename))
    return {'Result':'Success','Workspaces':len(workspaces),'FileName':backup_filename}


def restore_all_workspaces(restore_file):
    cs_path = lib.db.get_current_install_path()[0][0]
    workspaces = lib.db.get_all_workspaces()
    if workspaces:
        print("[!] There is already a current workspace.  This will backup the currnt DB and OVERWRITE it with the new one.")
        answer = raw_input("Are you sure you want to continue? (y\N): ")
        print("")
        if (answer == "Y") or (answer == "y"):
            backup_result = backup_all_workspaces()
            os.chdir("/")
            tar = tarfile.open(restore_file)
            tar.extractall()
            tar.close()



