import time
import db
import subprocess
import os


def get_terminal_width():
    """
    From: https://gist.githubusercontent.com/Steelsouls/9626112/raw/e99b6a741fa22c20c3699140d352de5a46db4ad2/terminal_width.py
    :return: the current width of the terminal
    """
    command = ['tput', 'cols']
    try:
        width = int(subprocess.check_output(command))
    except OSError as e:
        print("Invalid Command '{0}': exit status ({1})".format(
              command[0], e.errno))
    except subprocess.CalledProcessError as e:
        print("Command '{0}' returned non-zero exit status: ({1})".format(
              command, e.returncode))
    else:
        return width


def query_sqlite(workspace, target=None, repeat=None, summary=None):
    terminal_width = get_terminal_width()
    if not terminal_width:
        terminal_width = 80

    completed_count = db.get_completed_task_count(workspace)
    pending_count = db.get_pending_task_count(workspace)
    total_count = db.get_total_tasks(workspace)
    running_rows = db.get_running_tasks(workspace)
    completed_rows = db.get_completed_tasks(workspace)
    pending_rows = db.get_pending_tasks(workspace)
    cancelled_rows = db.get_cancelled_tasks(workspace)
    paused_rows = db.get_paused_tasks(workspace)

    loadavg = float("{0:.1f}".format(os.getloadavg()[0]))
    banner = "celerystalk Status | Workspace Name: {0}  | CPU Load Avg: {1}".format(workspace,loadavg)
    print("*" * terminal_width)
    print(" " * ((terminal_width / 2) - (len(banner) / 2)) + banner)
    print("\n" + " " * ((terminal_width / 2) - 40) + "Submitted: {0} | Queued: {3} | Running: {2} | Completed: {1}  | Cancelled: {4}  | Paused: {5}".format(total_count[0][0], completed_count[0][0], len(running_rows), pending_count[0][0], len(cancelled_rows), len(paused_rows)))
    print("*" * terminal_width)

    if summary:
        exit()

    if completed_rows.__len__() > 0:
        target_max_len = 0
        for completed_row in completed_rows:
            target_len = len(completed_row[3])
            if target_len > target_max_len:
                target_max_len = target_len

        if repeat:
            completed_rows_orig = completed_rows
            completed_rows = completed_rows[-5:]
            print("\n[+] Completed Tasks ({0}) (Only showing last 5 when in brief mode): \n\n  [Duration][    IP     ] command...".format(len(completed_rows_orig)))
        else:
            target_title_string = "TARGET".center(target_max_len)
            #print(target_title_string)
            print("\n[+] Completed Tasks ({0}): \n\n  [Duration][{1}] command...".format(len(completed_rows),target_title_string))
        for completed_row in completed_rows:
            command = completed_row[1]
            run_time = completed_row[2]
            run_time = time.strftime("%H:%M:%S", time.gmtime(float(run_time)))
            ip = completed_row[3]
            output_prefix = "  [" + run_time + "][" + ip.center(target_max_len) + "] "
            space_for_command = terminal_width - len(output_prefix)
            command_length = len(command)

            if command_length > space_for_command:
                print(output_prefix + command[0:space_for_command - 3] + "...")
            else:
                print(output_prefix + command)
        if repeat:
            if len(completed_rows_orig) > 5:
                print("  +{0} more rows".format(len(completed_rows_orig)-5))


    if cancelled_rows.__len__() > 0:
        nothing = ""
        if repeat:
            cancelled_rows_orig = cancelled_rows
            cancelled_rows = cancelled_rows[:5]
            print("\n[+] Cancelled Tasks ({0}) - (Only showing first 5 when in brief mode): \n".format(len(cancelled_rows_orig)))
        else:
            print("\n[+] Cancelled Tasks ({0}): \n".format(len(cancelled_rows)))
        for cancelled_row in cancelled_rows:
            id = cancelled_row[0]
            command = cancelled_row[1]

            command_length = len(command)
            if command_length > terminal_width - 11:

                print("  [" + str(id) + "]\t" + command[0:terminal_width - 11] + "...")
            else:
                print("  [" + str(id) + "]\t" + command)
        if repeat:
            if len(cancelled_rows_orig) > 5:
                print("  +{0} more rows".format(len(cancelled_rows_orig) - 5))



    if pending_rows.__len__() > 0:

        if repeat:
            pending_rows_orig = pending_rows
            pending_rows = pending_rows[:5]
            print("\n[+] Pending Tasks ({0}) - (Only showing first 5 when in brief mode): \n".format(len(pending_rows_orig)))
        else:
            print("\n[+] Pending Tasks ({0}): \n".format(len(pending_rows)))
        #pending_row_id = 0

        for pending_row in pending_rows:
            id = pending_row[0]
            command = pending_row[1]

            command_length = len(command)
            if command_length > terminal_width - 11:
                if int(id) > 999:
                    print(" [" + str(id) + "]\t" + command[0:terminal_width - 11] + "...")
                else:
                    print("  [" + str(id) + "]\t" + command[0:terminal_width - 11] + "...")
            else:
                if int(id) > 999:
                    print(" [" + str(id) + "]\t" + command)
                else:
                    print("  [" + str(id) + "]\t" + command)
            #pending_row_id = pending_row_id + 1
        if repeat:
            if len(pending_rows_orig) > 5:
                print("  +{0} more rows".format(len(pending_rows_orig) - 5))

    if paused_rows.__len__() > 0:

        print("\n[+] Paused Tasks ({0}): \n".format(len(paused_rows)))
        for paused_row in paused_rows:
            id = paused_row[0]
            command = paused_row[1]

            command_length = len(command)
            if command_length > terminal_width - 11:
                if int(id) > 999:
                    print(" [" + str(id) + "]\t" + command[0:terminal_width - 11] + "...")
                else:
                    print("  [" + str(id) + "]\t" + command[0:terminal_width - 11] + "...")
            else:
                print("  [" + str(id) + "]\t" + command)

    if running_rows.__len__() > 0:

        print("\n[+] Currently Running Tasks ({0}): \n\n  [ ID ][Run Time] command...".format(len(running_rows)))
        for running_row in running_rows:
            id = running_row[0]
            command = running_row[1]
            start_time = int(running_row[2])
            pid = running_row[3]
            curr_time = int(time.time())
            run_time = curr_time - start_time
            run_time = time.strftime("%H:%M:%S", time.gmtime(run_time))

            #run_time = time.ctime(int(curr_time - start_time))
            if len(str(id)) == 1:
                id_str = "  " + str(id) + " "
            elif len(str(id)) == 2:
                id_str = " " + str(id) + " "
            else:
                id_str = str(id) + " "
            command_length = len(command)
            if command_length > terminal_width -22:
                print("  [" + id_str + "][" + run_time + "] " + command[0:terminal_width - 22] + "...")
            else:
                print("  [" + id_str + "][" + run_time + "] " + command)
    else:
        if (len(completed_rows) > 0) and (len(pending_rows) == 0):
            if len(paused_rows) > 0:
                print("\n[+] Almost there! There are no jobs left in the queue, but you have some paused jobs.")
            else:
                print("\n[+] FIN! All submitted jobs in this workspace have finished.")
        else:
            if len(paused_rows) == 0:
                print("\n[!] There are no running tasks in this workspace. Did you want another workspace")
    print("\n")

