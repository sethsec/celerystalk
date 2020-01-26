import os
import lib.db
from prettytable import PrettyTable


def create_default_workspace(path):
    workspace_name = "Default"
    workspace_path = os.path.join(path + "default_workspace/")
    mode = "bb"


    all_workspaces = lib.db.get_all_workspaces()
    if not all_workspaces:  # If there is not at least one workspace in the DB
        db_workspace = (workspace_name, workspace_path, mode)  # and create the workspace

        try:
            os.stat(workspace_path)
        except:
            print("[+] Output directory does not exist. Creating " + workspace_path)
            os.makedirs(workspace_path)


        # This will create a workspace, only if one does not exist with that name.
        lib.db.create_workspace(db_workspace)
        print("[+] Workspace successfully created: " + workspace_name + "\n")

        lib.db.set_initial_current_workspace((workspace_name,))


def create_workspace(workspace,arguments):
    workspaces_exist = "False"
    workspace_match = "False"
    all_workspaces = lib.db.get_all_workspaces()

    if all_workspaces:  # If if there at least one workspace in the DB
        workspaces_exist = "True"
        for db_workspace in all_workspaces:
            if db_workspace[0] == workspace:  # Is there any workspace that matches our current?
                workspace_match = "True"
                #Get the output dir for that workspace
                output_dir = lib.db.get_output_dir_for_workspace(workspace)[0][0]  # If so, grab the current output dir


    if workspace_match == "True":  # If we did find a workspace in the DB that matches the user specified workspace
        if arguments["-o"]: #and the user specified a workspace
            arg_output_dir = os.path.join(arguments["-o"], '')
            if arg_output_dir != output_dir:  # if the user specified output dir is not the same as the db output_dir, ask the user whether they want to update it or ignore the command line output_dir
                output_dir_answer = raw_input(
                    "[!] The DB shows that the output directory for the [{0}] workspace is [{1}].\n[+] Do you want to update the output directory to [{2}]? (y\N)".format(
                        workspace, output_dir, arg_output_dir))
                print("")
                if (output_dir_answer == "Y") or (
                        output_dir_answer == "y"):  # if the user wants to use the command line dir, update the celerystalk db
                    lib.db.update_workspace_output_dir(arg_output_dir, workspace)
                    print("[+] Updated output directory for [{0}] workspace to [{1}].".format(workspace,
                                                                                              arg_output_dir))
                    try:
                        os.stat(arg_output_dir)
                    except:
                        print("[+] Output directory does not exist. Creating " + arg_output_dir)
                        os.makedirs(arg_output_dir)
        #else: #if the user did not specify an output dir, do nothing
        #print("[+] Workspace already exists: " + workspace + "\n")
        current_workspace = lib.db.get_current_workspace()[0][0]
        if not current_workspace:
            db_workspace = (workspace,)
            lib.db.set_initial_current_workspace(db_workspace)
        else:
            if current_workspace == workspace:
                print("[+] Workspace: " + workspace + " already exists and is the current workspace: " + workspace + "\n")
            else:
                print("[+] Workspace: " + workspace + " already exists but it is not the current workspace\n")
                answer = raw_input("[+] Would you like to switch to this workspace? [Y\\n] ")
                if (answer == "Y") or (answer == "y") or (answer == ""):
                    lib.db.update_current_workspace(workspace)



    else: #create a new workspace
        if arguments["-o"] is None:  # and the user did not specify one at the command line, yell at the user
            print('[!] Define where you would like scan output & reports saved (Eg: -o /assessments/)\n')
            exit()
        else:
            if arguments["-m"] == "vapt":
                mode = "vapt"
            elif arguments["-m"] == "bb":
                mode = "bb"
            else:
                print("[!] You must specify the mode [ vapt | bb ].\n")
                print("  VAPT Mode:\tIn VAPT mode, IP addresses/ranges/CIDRs define scope.")
                print("\t\tSubdomains that match an in-scope IP are also added to scope.\n ")
                print("\t\tWays to define your scope:")
                print("\t\t\t./celerystalk import -S scope.txt")
                print("\t\t\t./celerysatlk import -f nmap/nessus file")
                print("\t\tHosts can be explicitly excluded:")
                print("\t\t\t./celerysatlk import -O out_of_scope.txt. \n")
                print("  BB Mode:\tIn BB mode, all subdomains found with celerystalk or manually imported are marked in scope.\n")
                print("\t\tHosts can be explicitly excluded:")
                print("\t\t\t./celerysatlk import -O out_of_scope.txt. \n")
                exit()

            # if the user did specify an output_dir (and a DB one doesnt exist), create the dir, and the workspace
            output_dir = os.path.join(arguments["-o"],'')
            try:
                os.stat(output_dir)
            except:
                print("[+] Output directory does not exist. Creating " + output_dir)
                os.makedirs(output_dir)
            db_workspace = (workspace, output_dir, mode)  # and create the workspace
            # This will create a workspace, only if one does not exist with that name.
            lib.db.create_workspace(db_workspace)
            print("[+] Workspace successfully created: " + workspace + "\n")

            #check to see if there is a currenet workspace.  if there isnt, create a record in current workspace. if there is, update it.
            db_workspace = (workspace,)
            current_workspace = lib.db.get_current_workspace()
            if not current_workspace:
                db_workspace = (workspace,)
                lib.db.set_initial_current_workspace(db_workspace)
            else:
                lib.db.update_current_workspace(workspace)

    columns = ["Workspace", "Output Directory", "Mode"]
    workspace_rows = lib.db.get_all_workspaces()
    workspaces_table = PrettyTable(columns)
    workspaces_table.align[columns[1]] = "l"
    for row in workspace_rows:
        workspaces_table.add_row(row)
    print(workspaces_table)
    print("\n")
    print("[+} Current workspace: " + workspace + "\n")

    return output_dir,workspace