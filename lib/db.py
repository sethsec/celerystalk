import sqlite3
from sqlite3 import Error

CONNECTION = sqlite3.connect("csdb.sqlite3")
CUR = CONNECTION.cursor()

#############################
#Table Creation
#############################

def create_task_table():
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """

    sql_create_tasks_table = """ CREATE TABLE IF NOT EXISTS tasks (
                                    id INTEGER PRIMARY KEY,
                                    task_id text NOT NULL,
                                    pid integer,
                                    command_name text,                                    
                                    command text NOT NULL,
                                    ip text NOT NULL,
                                    output_file,                                
                                    status text NOT NULL,
                                    workspace text NOT NULL,
                                    start_time text,
                                    run_time text                                     
                                   ); """

    try:
        CUR.execute(sql_create_tasks_table)
        CONNECTION.commit()
    except Error as e:
        print(e)


def create_workspace_table():
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """

    sql_create_workspace_table = """ CREATE TABLE IF NOT EXISTS workspace (
                                        name text PRIMARY KEY,
                                        output_dir text NOT NULL,
                                        mode text NOT NULL                                        
                                    ); """

    try:
        CUR.execute(sql_create_workspace_table)
        CONNECTION.commit()
    except Error as e:
        print(e)


def create_current_workspace_table():
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """

    sql_create_current_workspace_table = """ CREATE TABLE IF NOT EXISTS current_workspace (
                                        current_db text PRIMARY KEY                                        
                                    ); """

    try:
        CUR.execute(sql_create_current_workspace_table)
        CONNECTION.commit()
    except Error as e:
        print(e)

def create_celerystalk_table():
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """

    sql_create_celerystalk_table = """ CREATE TABLE IF NOT EXISTS celerystalk (
                                        install_path text PRIMARY KEY                                        
                                    ); """

    try:
        CUR.execute(sql_create_celerystalk_table)
        CONNECTION.commit()
    except Error as e:
        print(e)


def create_path_table():
    sql_create_paths_table = """ CREATE TABLE IF NOT EXISTS paths (
                                        id integer PRIMARY KEY,
                                        ip text NOT NULL,
                                        port int NOT NULL,
                                        path text NOT NULL UNIQUE,
                                        url_status int,
                                        submitted int,
                                        url_screenshot_filename text,                                        
                                        workspace text NOT NULL
                                    ); """

    try:
        CUR.execute(sql_create_paths_table)
        CONNECTION.commit()
    except Error as e:
        print(e)

def create_services_table():
    sql_create_services_table = """ CREATE TABLE IF NOT EXISTS services (
                                        id INTEGER PRIMARY KEY,
                                        ip text NOT NULL,
                                        port int NOT NULL,
                                        proto text NOT NULL,
                                        service text,
                                        product text,
                                        version text,
                                        extra_info text,                                        
                                        workspace text
                                    ); """
    CUR.execute(sql_create_services_table)

    try:
        CUR.execute(sql_create_services_table)
        CONNECTION.commit()
    except Error as e:
        print(e)


def create_vhosts_table():

    sql_create_vhosts_table = """ CREATE TABLE IF NOT EXISTS vhosts (
                                        id INTEGER PRIMARY KEY,
                                        ip text,
                                        vhost text NOT NULL,
                                        in_scope int,
                                        explicit_out_scope int,
                                        submitted int NOT NULL,                                                                                
                                        workspace text
                                    ); """

    try:
        CUR.execute(sql_create_vhosts_table)
        CONNECTION.commit()
    except Error as e:
        print(e)

#############################
# Table: Workspace
#############################

def create_workspace(db_workspace):
    """

    :param workspace:
    :return:
    """
    sql_create_workspace = ''' INSERT OR IGNORE INTO workspace(name,output_dir,mode)
              VALUES(?,?,?) '''
    CUR.execute(sql_create_workspace,db_workspace)
    CONNECTION.commit()

def get_output_dir_for_workspace(workspace):
    CUR.execute("SELECT output_dir FROM workspace where name = ?", (workspace,))
    workspace = CUR.fetchall()
    CONNECTION.commit()
    return workspace

def get_workspace_mode(workspace):
    CUR.execute("SELECT mode FROM workspace where name = ?", (workspace,))
    workspace = CUR.fetchall()
    CONNECTION.commit()
    return workspace

def get_all_workspaces():
    CUR.execute("SELECT * FROM workspace")
    workspaces = CUR.fetchall()
    CONNECTION.commit()
    return workspaces

def update_workspace_output_dir(output_dir,workspace):
    CUR.execute("UPDATE workspace SET output_dir=? WHERE name=?", (output_dir,workspace))
    CONNECTION.commit()

def update_workspace_mode(mode,workspace):
    CUR.execute("UPDATE workspace SET mode=? WHERE name=?", (mode,workspace))
    CONNECTION.commit()

#############################
# Table: Current Workspace
#############################

def set_initial_current_workspace(db_workspace):
    """

    :param workspace:
    :return:
    """
    sql_create_current_workspace = ''' INSERT OR IGNORE INTO current_workspace(current_db)
              VALUES(?) '''
    CUR.execute(sql_create_current_workspace,db_workspace)
    CONNECTION.commit()

def get_current_workspace():
    CUR.execute("SELECT current_db FROM current_workspace")
    current_workspace = CUR.fetchall()
    CONNECTION.commit()
    return current_workspace

def update_current_workspace(workspace):
    CUR.execute("UPDATE current_workspace SET current_db=?", (workspace,))
    CONNECTION.commit()


#############################
# Table: Create celerystalk
#############################

def set_install_path(db_install_path):
    """

    :param workspace:
    :return:
    """
    sql_create_celerystalk = ''' INSERT OR IGNORE INTO celerystalk(install_path)
              VALUES(?) '''
    CUR.execute(sql_create_celerystalk,db_install_path)
    CONNECTION.commit()

def get_current_install_path():
    CUR.execute("SELECT install_path FROM celerystalk")
    install_path = CUR.fetchall()
    CONNECTION.commit()
    return install_path

# def update_current_workspace(workspace):
#     CUR.execute("UPDATE celerystalk SET install_path=?", (install_path,))
#     CONNECTION.commit()

#############################
# Table: Tasks
#############################

def create_task(task):
    """

    :param workspace:
    :return:
    """
    sql = ''' INSERT INTO tasks(task_id, pid, command_name, command, ip, output_file, status, workspace)
              VALUES(?,?,?,?,?,?,?,?) '''

    CUR.execute(sql, task)
    CONNECTION.commit()

def get_all_tasks_in_workspace(workspace):
    CUR.execute("SELECT id,pid,command,status FROM tasks WHERE workspace = ?", (workspace,))
    all_tasks = CUR.fetchall()
    CONNECTION.commit()
    return all_tasks

def get_completed_task_count(workspace):
    CUR.execute("SELECT count(*) FROM tasks where status = ? AND workspace = ?", ("COMPLETED", workspace))
    completed_count = CUR.fetchall()
    CONNECTION.commit()
    return completed_count

def get_pending_task_count(workspace):
    CUR.execute("SELECT count(*) FROM tasks where status = ? AND workspace = ?", ("SUBMITTED", workspace))
    pending_count = CUR.fetchall()
    CONNECTION.commit()
    return pending_count

def get_completed_tasks(workspace):
    CUR.execute("SELECT pid,command,run_time,ip FROM tasks where status = ? AND workspace = ?", ("COMPLETED", workspace))
    completed_tasks = CUR.fetchall()
    CONNECTION.commit()
    return completed_tasks

def get_all_completed_tasks():
    CUR.execute("SELECT command,workspace FROM tasks where status = ?", ("COMPLETED"))
    all_tasks = CUR.fetchall()
    CONNECTION.commit()
    return all_tasks

def get_cancelled_tasks(workspace):
    CUR.execute("SELECT id,command FROM tasks where status = ? AND workspace = ?", ("CANCELLED", workspace))
    cancelled_tasks = CUR.fetchall()
    CONNECTION.commit()
    return cancelled_tasks

def get_paused_tasks(workspace):
    CUR.execute("SELECT id,command FROM tasks where status = ? AND workspace = ?", ("PAUSED", workspace))
    paused_tasks = CUR.fetchall()
    CONNECTION.commit()
    return paused_tasks

def get_task_id_status_pid(id):
    CUR.execute("SELECT id,task_id,status,pid FROM tasks where id = ?", (id,))
    task_id_status_pid = CUR.fetchall()
    CONNECTION.commit()
    return task_id_status_pid

def get_pending_tasks(workspace,ip=None):
    if ip:
        CUR.execute("SELECT id,command FROM tasks where status = ? AND workspace = ? AND ip = ?",
                    ("SUBMITTED", workspace,ip))
    else:
        CUR.execute("SELECT id,command FROM tasks where status = ? AND workspace = ?",
                    ("SUBMITTED", workspace))
    pending_count = CUR.fetchall()
    CONNECTION.commit()
    return pending_count

def get_running_tasks(workspace,ip=None):
    if ip:
        CUR.execute("SELECT id,command,start_time,pid FROM tasks where status = ? AND workspace = ? AND ip = ?",
                    ("STARTED", workspace,ip))
    else:
        CUR.execute("SELECT id,command,start_time,pid FROM tasks where status = ? AND workspace = ?",
                    ("STARTED", workspace))
    running_rows = CUR.fetchall()
    CONNECTION.commit()
    return running_rows


def get_paused_tasks(workspace,ip=None):
    if ip:
        CUR.execute("SELECT id,command,start_time,pid FROM tasks where status = ? AND workspace = ?  AND ip = ?",
                    ("PAUSED", workspace,ip))
    else:
        CUR.execute("SELECT id,command,start_time,pid FROM tasks where status = ? AND workspace = ?",
                    ("PAUSED", workspace))
    paused_rows = CUR.fetchall()
    return paused_rows

def get_report_info_for_ip(workspace,ip):
    CUR.execute("SELECT output_file,command_name,command,status,start_time,run_time FROM tasks where ip = ? AND workspace = ? AND (status = 'COMPLETED' or status = 'STARTED')", (ip, workspace))
    report_info = CUR.fetchall()
    CONNECTION.commit()
    return report_info

def get_report_info_for_vhost(workspace,vhost):
    CUR.execute("SELECT output_file,command_name,command,status,start_time,run_time FROM tasks where vhost = ? AND workspace = ? AND (status = 'COMPLETED' or status = 'STARTED')", (vhost, workspace))
    report_info = CUR.fetchall()
    CONNECTION.commit()
    return report_info

def get_reportable_output_files_for_vhost(workspace,vhost):
    CUR.execute("SELECT DISTINCT output_file FROM tasks where ip = ? AND workspace = ? AND (status = 'COMPLETED' or status = 'STARTED')", (vhost, workspace))
    report_info = CUR.fetchall()
    CONNECTION.commit()
    return report_info

def get_tasks_for_output_file(workspace,vhost,output_file):
    CUR.execute("SELECT command_name,command,status,start_time,run_time FROM tasks where output_file = ? AND workspace = ? AND (status = 'COMPLETED' or status = 'STARTED')", (output_file, workspace))
    report_info = CUR.fetchall()
    CONNECTION.commit()
    return report_info

def get_output_file_for_command(workspace,command):
    CUR.execute("SELECT DISTINCT output_file FROM tasks where workspace = ? AND command = ? AND (status = 'COMPLETED' or status = 'STARTED')", (workspace, command))
    report_info = CUR.fetchall()
    CONNECTION.commit()
    return report_info

def get_unique_hosts_in_workspace(workspace):
    CUR.execute("SELECT DISTINCT ip,output_dir FROM tasks WHERE name=?", (workspace,))
    host_rows = CUR.fetchall()
    CONNECTION.commit()
    return host_rows

def get_unique_hosts_in_output_dir(output_dir):
    CUR.execute("SELECT DISTINCT ip,output_dir FROM tasks WHERE output_dir LIKE ?", (output_dir,))
    host_rows = CUR.fetchall()
    CONNECTION.commit()
    return host_rows

def get_total_tasks(workspace):
    CUR.execute("SELECT count(*) FROM tasks where workspace = ?", (workspace,))
    total_count = CUR.fetchall()
    CONNECTION.commit()
    return total_count

def get_unique_command_names(workspace):
    CUR.execute("SELECT DISTINCT command_name FROM tasks WHERE workspace=?", (workspace,))
    commands = CUR.fetchall()
    CONNECTION.commit()
    return commands

def get_unique_non_sim_command_names(workspace):
    CUR.execute("SELECT DISTINCT command_name FROM tasks WHERE workspace=? AND command_name NOT LIKE '#%'", (workspace,))
    commands = CUR.fetchall()
    CONNECTION.commit()
    return commands

def get_unique_non_sim_command_names_for_vhost(vhost,workspace):
    CUR.execute("SELECT DISTINCT command_name FROM tasks WHERE workspace=? AND ip=? AND command_name NOT LIKE '#%'", (workspace,vhost))
    commands = CUR.fetchall()
    CONNECTION.commit()
    return commands

def get_unique_command_names(workspace):
    CUR.execute("SELECT DISTINCT command_name FROM tasks WHERE workspace=?", (workspace,))
    commands = CUR.fetchall()
    CONNECTION.commit()
    return commands


def update_task_status_started(status,task_id,pid,start_time):
    CUR.execute("UPDATE tasks SET status=?,pid=?,start_time=? WHERE task_id=?", (status,pid,start_time,task_id))
    CONNECTION.commit()


def update_task_status_completed(status,task_id,run_time):
    CUR.execute("UPDATE tasks SET status=?,run_time=? WHERE task_id=?", (status, run_time, task_id))
    CONNECTION.commit()


def update_task_status_cancelled(task_id):
    CUR.execute("UPDATE tasks SET status=? WHERE task_id=?", ("CANCELLED",task_id))
    CONNECTION.commit()


def update_task_status_paused(task_id):
    CUR.execute("UPDATE tasks SET status=? WHERE task_id=?", ("PAUSED",task_id))
    CONNECTION.commit()


def update_task_status_resumed(task_id):
    CUR.execute("UPDATE tasks SET status=? WHERE task_id=?", ("STARTED",task_id))
    CONNECTION.commit()

def update_task_status_error(task_id):
    CUR.execute("UPDATE tasks SET status=? WHERE task_id=?", ("ERROR",task_id))
    CONNECTION.commit()


#############################
# Table: Services
#############################

def create_service(db_service):
    """

    :param workspace:
    :return:
    """
    sql = ''' INSERT INTO services(ip,port,proto,service,product,version,extra_info,workspace)
              VALUES(?,?,?,?,?,?,?,?) '''
    CUR.execute(sql, db_service)
    CONNECTION.commit()

def get_service(ip,port,protocol,workspace):
    CUR.execute("SELECT * FROM services WHERE ip=? AND port=? and proto=? and workspace=?", (ip,port,protocol,workspace))
    service_row = CUR.fetchall()
    CONNECTION.commit()
    return service_row

def get_all_services(workspace):
    CUR.execute("SELECT ip,port,proto,service,product,version,extra_info FROM services WHERE workspace=? ORDER BY ip,port", (workspace,))
    service_rows = CUR.fetchall()
    CONNECTION.commit()
    return service_rows

def get_all_services_for_ip(ip,workspace):
    CUR.execute("SELECT ip,port,proto,service,product,version,extra_info FROM services WHERE ip=? AND workspace=?", (ip,workspace))
    service_rows = CUR.fetchall()
    CONNECTION.commit()
    return service_rows

def get_unique_hosts(workspace):
    CUR.execute("SELECT DISTINCT ip FROM services WHERE workspace=?", (workspace,))
    host_rows = CUR.fetchall()
    CONNECTION.commit()
    return host_rows

def update_service(ip,port,proto,service,workspace):
    CUR.execute("UPDATE services SET service=? WHERE ip=? AND port=? AND proto=? AND workspace=?", (service,ip,port,proto,workspace))
    CONNECTION.commit()


#############################
# Table: Vhosts
#############################

def create_vhost(db_vhost):
    """

    :param workspace:
    :return:
    """
    sql = ''' INSERT OR IGNORE INTO vhosts(ip,vhost,in_scope,explicit_out_scope,submitted,workspace)
              VALUES(?,?,?,?,?,?) '''
    CUR.execute(sql, db_vhost)
    CONNECTION.commit()


def get_host_by_ip(ip,workspace):
    CUR.execute("SELECT ip FROM vhosts WHERE ip=? AND workspace=?", (ip,workspace))
    vhost_rows = CUR.fetchall()
    CONNECTION.commit()
    return vhost_rows

def is_vhost_in_db(vhost,workspace):
    CUR.execute("SELECT vhost FROM vhosts WHERE vhost=? AND workspace=?", (vhost,workspace))
    vhost_rows = CUR.fetchall()
    CONNECTION.commit()
    return vhost_rows

def get_unique_inscope_vhosts_for_ip(ip,workspace):
    CUR.execute("SELECT vhost FROM vhosts WHERE ip=? AND workspace=? AND in_scope=?", (ip,workspace,1))
    vhost_rows = CUR.fetchall()
    CONNECTION.commit()
    return vhost_rows

def get_unique_inscope_vhosts(workspace):
    CUR.execute("SELECT vhost FROM vhosts WHERE workspace=? AND in_scope=?", (workspace,1))
    vhost_rows = CUR.fetchall()
    CONNECTION.commit()
    return vhost_rows

def get_unique_submitted_vhosts(workspace):
    CUR.execute("SELECT vhost FROM vhosts WHERE workspace=? AND submitted=?", (workspace,1))
    vhost_rows = CUR.fetchall()
    CONNECTION.commit()
    return vhost_rows


def get_unique_out_of_scope_vhosts(workspace):
    CUR.execute("SELECT vhost FROM vhosts WHERE workspace=? AND in_scope=?", (workspace,0))
    vhost_rows = CUR.fetchall()
    CONNECTION.commit()
    return vhost_rows

def get_unique_inscope_ips(workspace):
    CUR.execute("SELECT DISTINCT ip FROM vhosts WHERE workspace=? AND in_scope=?", (workspace,1))
    host_rows = CUR.fetchall()
    CONNECTION.commit()
    return host_rows

def get_in_scope_ip(ip,workspace):
    CUR.execute("SELECT ip FROM vhosts WHERE ip=? AND workspace=? AND in_scope=?", (ip,workspace,1))
    host_rows = CUR.fetchall()
    CONNECTION.commit()
    return host_rows

def is_vhost_submitted(vhost,workspace):
    CUR.execute("SELECT vhost FROM vhosts WHERE vhost=? AND workspace=? AND submitted=?", (vhost,workspace,1))
    host_rows = CUR.fetchall()
    CONNECTION.commit()
    return host_rows

def get_unique_out_of_scope_ips(workspace):
    CUR.execute("SELECT DISTINCT ip FROM vhosts WHERE workspace=? AND in_scope=?", (workspace,0))
    host_rows = CUR.fetchall()
    CONNECTION.commit()
    return host_rows

def get_unique_explicit_out_of_scope_vhosts(workspace):
    CUR.execute("SELECT DISTINCT vhost FROM vhosts WHERE workspace=? AND explicit_out_scope=?", (workspace,1))
    host_rows = CUR.fetchall()
    CONNECTION.commit()
    return host_rows

def get_unique_hosts_not_explicitly_out_of_scope_vhosts(workspace):
    CUR.execute("SELECT DISTINCT vhost FROM vhosts WHERE workspace=? AND explicit_out_scope=?", (workspace,0))
    host_rows = CUR.fetchall()
    CONNECTION.commit()
    return host_rows


def is_vhost_explicitly_out_of_scope(vhost,workspace):
    CUR.execute("SELECT vhost FROM vhosts WHERE vhost=? AND workspace=? AND explicit_out_scope=?", (vhost,workspace,1))
    host_rows = CUR.fetchall()
    CONNECTION.commit()
    return host_rows


def get_inscope_unsubmitted_vhosts(workspace):
    CUR.execute("SELECT vhost FROM vhosts WHERE in_scope=? AND submitted=? AND workspace=?", (1,0,workspace))
    scannable_vhosts = CUR.fetchall()
    CONNECTION.commit()
    return scannable_vhosts


def get_inscope_submitted_vhosts_for_ip(ip,workspace):
    CUR.execute("SELECT vhost FROM vhosts WHERE in_scope=? AND submitted=? AND workspace=? AND ip=?", (1,1,workspace,ip))
    vhost_rows = CUR.fetchall()
    CONNECTION.commit()
    return vhost_rows

def get_inscope_submitted_vhosts(workspace):
    CUR.execute("SELECT vhost FROM vhosts WHERE in_scope=? AND submitted=? AND workspace=?", (1,1,workspace))
    vhost_rows = CUR.fetchall()
    CONNECTION.commit()
    return vhost_rows

def get_vhost_ip(scannable_vhost,workspace):
    CUR.execute("SELECT ip FROM vhosts WHERE vhost=? AND workspace=?", (scannable_vhost,workspace))
    ip = CUR.fetchall()
    CONNECTION.commit()
    return ip

def get_vhosts_table(workspace):
    CUR.execute("SELECT ip,vhost,in_scope,explicit_out_scope,submitted FROM vhosts WHERE workspace=? ORDER BY explicit_out_scope ASC, in_scope DESC,ip,vhost", (workspace,))
    vhost_rows = CUR.fetchall()
    CONNECTION.commit()
    return vhost_rows

def update_vhost_ip(ip,vhost,workspace):
    CUR.execute("UPDATE vhosts SET ip=? WHERE vhost=? AND workspace=?", (ip,vhost,workspace))
    CONNECTION.commit()

def update_vhosts_submitted(ip,vhost,workspace,submitted):
    CUR.execute("UPDATE vhosts SET submitted=? WHERE ip=? AND vhost=? AND workspace=?", (submitted,ip,vhost,workspace))
    CONNECTION.commit()

def update_vhosts_in_scope(ip,vhost,workspace,in_scope):
    CUR.execute("UPDATE vhosts SET in_scope=? WHERE ip=? AND vhost=? AND workspace=?", (in_scope,ip,vhost,workspace))
    CONNECTION.commit()

def update_vhosts_explicit_out_of_scope(vhost,workspace,in_scope,explicit_out_scope):
    CUR.execute("UPDATE vhosts SET in_scope=?,explicit_out_scope=? WHERE vhost=? AND workspace=?", (in_scope,explicit_out_scope,vhost,workspace))
    CONNECTION.commit()




#############################
# Table: Paths
#############################

def insert_new_path(db_path):
    """

    :param db_path:
    :return:
    """
    sql = '''INSERT OR IGNORE INTO paths(ip,port,path,url_status,submitted,url_screenshot_filename,workspace)
              VALUES(?,?,?,?,?,?,?)  '''
    CUR.execute(sql, db_path)
    CONNECTION.commit()

def get_all_paths(workspace):
    CUR.execute("SELECT * FROM paths WHERE workspace = ? ORDER BY ip,port,path,url_status", (workspace,))
    all_paths = CUR.fetchall()
    CONNECTION.commit()
    return all_paths

def get_all_paths_exclude_404(workspace):
    CUR.execute("SELECT * FROM paths WHERE workspace = ? AND url_status != 404 ORDER BY ip,port,path,url_status", (workspace,))
    all_paths = CUR.fetchall()
    CONNECTION.commit()
    return all_paths

def get_all_paths_for_host_exclude_404(ip):
    CUR.execute("SELECT ip,port,path,url_screenshot_filename,workspace FROM paths WHERE ip = ? AND url_status != 404 ORDER BY port,path", (ip,))
    all_paths_for_host = CUR.fetchall()
    CONNECTION.commit()
    return all_paths_for_host

def get_all_paths_for_host_path_only(ip,workspace):
    CUR.execute("SELECT path FROM paths WHERE ip = ? AND workspace = ? AND url_status != 404", (ip,workspace))
    all_paths_for_host = CUR.fetchall()
    CONNECTION.commit()
    return all_paths_for_host

def get_x_paths_for_host_path_only(ip,workspace,config_max):
    CUR.execute("SELECT path FROM paths WHERE ip = ? AND workspace = ? AND url_status != 404 LIMIT ?", (ip,workspace,config_max))
    all_paths_for_host = CUR.fetchall()
    CONNECTION.commit()
    return all_paths_for_host

def get_path(path,workspace):
    CUR.execute("SELECT * FROM paths WHERE workspace = ? AND path = ?", (workspace,path))
    path = CUR.fetchall()
    CONNECTION.commit()
    return path

def get_unique_hosts_with_paths(workspace):
    CUR.execute("SELECT DISTINCT ip FROM paths WHERE workspace=?", (workspace,))
    host_rows = CUR.fetchall()
    CONNECTION.commit()
    return host_rows

def update_path(path,submitted,workspace):
    CUR.execute("UPDATE paths SET submitted=? WHERE path=? AND workspace=?", (submitted,path,workspace))
    CONNECTION.commit()

def update_path_with_filename(path,filename,workspace):
    CUR.execute("UPDATE paths SET url_screenshot_filename=? WHERE path=? AND workspace=?", (filename,path,workspace))
    CONNECTION.commit()