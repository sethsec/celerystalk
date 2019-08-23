from cmd import Cmd
import lib.db
import os
from prettytable import PrettyTable
import csv
from docopt import docopt

class MyPrompt(Cmd):

    def help_db(self):
        print(getattr(self, 'do_db').__doc__)
        print('')
        print('Usage: db [workspaces|hosts|vhosts|paths|export]')
        print('')

    def do_quit(self, args):
        """Quits the program."""
        print("Quitting.")
        raise SystemExit

    def do_db(self,args):
        """
db workspaces
db services
db hosts
db paths
db export
"""
        if not args:
            self.help_db()
            return
        args = args.split()
        arg = args.pop(0).lower()

        try:
            workspace = lib.db.get_current_workspace()[0][0]
            output_dir = lib.db.get_output_dir_for_workspace(workspace)[0][0]
        except:
            print(
                "[!] Looks like are no workspaces. Create one with: \n\n./celerystalk workspace create -o [output_dir] and then run your command again.\n")
            exit()

        if arg == 'workspaces':
            if workspace:
                columns = ["Workspace", "Output Directory"]
                workspace_rows = lib.db.get_all_workspaces()
                workspaces_table = PrettyTable(columns)
                for row in workspace_rows:
                    workspaces_table.add_row(row)
                print(workspaces_table)
                print("\n\n")
        elif arg == 'hosts':
            print("[+] Showing hosts for the [{0}] workspace\n".format(workspace))
            columns = ["IP", "Vhost", "In Scope", "Submitted"]
            host_rows = lib.db.get_vhosts_table(workspace)
            hosts_table = PrettyTable(columns)
            hosts_table.align[columns[0]] = "l"
            hosts_table.align[columns[1]] = "l"
            for row in host_rows:
                hosts_table.add_row(row)
            print(hosts_table)
            print("\n\n")
        elif arg == 'vhosts':
            print("[+] Showing vhosts for the [{0}] workspace\n".format(workspace))
            columns = ["IP", "Vhost", "In Scope", "Submitted"]
            host_rows = lib.db.get_vhosts_table(workspace)
            hosts_table = PrettyTable(columns)
            hosts_table.align[columns[0]] = "l"
            hosts_table.align[columns[1]] = "l"
            for row in host_rows:
                if row[0] != row[1]:
                    hosts_table.add_row(row)
            print(hosts_table)
            print("\n\n")
        elif arg == 'services':
            print("[+] Showing services for the [{0}] workspace\n".format(workspace))
            columns = ["IP", "Port", "Protocol", "Service", "Product", "Version", "Extra Info"]
            services_rows = lib.db.get_all_services(workspace)
            services_table = PrettyTable(columns)
            services_table.align[columns[0]] = "l"
            services_table.align[columns[1]] = "l"
            services_table.align[columns[3]] = "l"
            for row in services_rows:
                services_table.add_row(row[1:5])
            print(services_table)
            print("\n\n")
        elif arg == 'paths':
            print("[+] Showing paths for the [{0}] workspace\n".format(workspace))
            columns = ["IP", "Port", "Path"]
            paths_rows = lib.db.get_all_paths(workspace)
            paths_table = PrettyTable(columns)
            paths_table.align[columns[0]] = "l"
            paths_table.align[columns[1]] = "l"
            paths_table.align[columns[2]] = "l"
            for row in paths_rows:
                paths_table.add_row(row[1:4])
            print(paths_table)
            print("\n\n")
        elif arg == "export":
            output_dir = lib.db.get_output_dir_for_workspace(workspace)[0][0]
            # hosts
            host_rows = lib.db.get_vhosts_table(workspace)
            hosts_filename = workspace + "_hosts.csv"
            hosts_output_file = os.path.join(output_dir, hosts_filename)
            with open(hosts_output_file, 'wb') as f:
                writer = csv.writer(f)
                writer.writerow(["IP", "vhost", "in_scope"])
                writer.writerows(host_rows)
            print("[+] Saved all hosts in the [{0}] workspace to {1}".format(workspace, hosts_output_file))

            # services
            services_rows = lib.db.get_all_services(workspace)
            services_filename = workspace + "_services.csv"
            services_output_file = os.path.join(output_dir, services_filename)
            with open(services_output_file, 'wb') as f:
                writer = csv.writer(f)
                writer.writerow(["IP", "Port", "Protocol", "Service", "Product", "Version", "Extra Info"])
                writer.writerows(services_rows)
            print("[+] Saved all ports in the [{0}] workspace to {1}".format(workspace, services_output_file))

            # paths
            paths_rows = lib.db.get_all_paths(workspace)
            paths_filename = workspace + "_paths.csv"
            paths_output_file = os.path.join(output_dir, paths_filename)
            with open(paths_output_file, 'wb') as f:
                writer = csv.writer(f)
                writer.writerow(["IP", "Port", "Path"])
                writer.writerows(paths_rows)
            print("[+] Saved all paths in the [{0}] workspace to {1}.\n".format(workspace, paths_output_file))


    def do_workspace(self, args):
        """
        workspace create
        :param args:
        :return:
        """
        if not args:
            self.help_workspace()
            return
        arg = args.lower()
        if args.split()[0] == 'create':
            if len(arg.split()) > 1:
                workspace = ' '.join(arg.split()[1:])
            else:
                workspace = 'Default'
            db_workspace = (workspace,)
            output_dir, workspace = lib.workspace.create_workspace(workspace, arguments)
            current_workspace = lib.db.get_current_workspace()
            if not current_workspace:
                db_workspace = (workspace,)
                lib.db.set_initial_current_workspace(db_workspace)
            else:
                lib.db.update_current_workspace(workspace)
        elif arguments["<workspace_name>"]:
            if arguments["<workspace_name>"]:
                workspace = arguments["<workspace_name>"]
            else:
                workspace = 'Default'
            db_workspace = (workspace,)
            current_workspace = lib.db.get_current_workspace()
            if not current_workspace:
                db_workspace = (workspace,)
                lib.db.set_initial_current_workspace(db_workspace)
            else:
                lib.db.update_current_workspace(workspace)
        else:
            current_workspace = lib.db.get_current_workspace()[0][0]
            print("[+} Current workspace: " + current_workspace + "\n")



        # i = dbPrompt()
        # i.prompt = self.prompt[:-1] + '[db]'
        # i.cmdloop()
        # print(args)






# class dbPrompt(MyPrompt):
#
#     def do_workspaces(self, args):
#
#
#         print(args)
#         try:
#             workspace = lib.db.get_current_workspace()[0][0]
#             output_dir = lib.db.get_output_dir_for_workspace(workspace)[0][0]
#         except:
#             print("[!] Looks like are no workspaces. Create one with: \n\n./celerystalk workspace create -o [output_dir] and then run your command again.\n")
#             exit()
#
#         if workspace:
#             columns = ["Workspace", "Output Directory"]
#             workspace_rows = lib.db.get_all_workspaces()
#             workspaces_table = PrettyTable(columns)
#             for row in workspace_rows:
#                 workspaces_table.add_row(row)
#             print(workspaces_table)
#             print("\n\n")
#
#
#     def do_services(self,args):
