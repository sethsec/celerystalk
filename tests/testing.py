from lib.utils import get_terminal_width
from lib.administrative import backup_all_workspaces
from lib.config_parser import read_config_ini
from parsers.generic_urlextract import extract_in_scope_urls_from_task_output
import lib.db
import lib.csimport
import os
import unittest
import time

class ServicesTest(unittest.TestCase):
    def setUp(self):
        print("Starting Services")
        config_file = 'config.ini'
        lib.utils.start_services(config_file)

    def test_backup(self):
        backup_result = backup_all_workspaces()
        #print(backup_result)
        self.assertEqual(backup_result['Result'],'Success')

    def test_config_read(self):
        config,supported_services = read_config_ini('config.ini')
        #print(supported_services)
        self.assertEqual(supported_services[0],"http")


    def test_import_scope(self):
        scope_file = os.path.join(os.path.dirname(__file__), 'data','scope.txt')
        workspace = lib.db.get_current_workspace()[0][0]
        lib.csimport.import_vhosts(scope_file,workspace)
        in_scope_vhosts = lib.db.get_unique_inscope_vhosts(workspace)
        self.assertEqual(len(in_scope_vhosts),4)
        time.sleep(3)

        with open(os.path.join(os.path.dirname(__file__), 'data','urls.txt'),'r') as file:
            tool_output = file.read()
            result = extract_in_scope_urls_from_task_output(tool_output)
            print(result)
            self.assertEqual(result,7)
            workspace = lib.db.get_current_workspace()
            paths = lib.db.get_all_paths(workspace[0][0])
            self.assertEqual(len(paths),7)
            paths = lib.db.get_all_paths_exclude_404(workspace[0][0])
            self.assertEqual(len(paths), 5)


if __name__ == '__main__':
    unittest.main()