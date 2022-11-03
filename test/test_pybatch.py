import unittest
import os
import subprocess
import logging
import sys

def test():
    t = '''
    --script samples/test_script.py
    --parameter p1=5
    --parameter p2=3
    --verbose
    #--infiles /disk/matthias/hokto/hokto_data/DATA/**/brain_img.nii.gz
    # quotes
    --infiles '/disk/matthias/hokto/hokto_data/DATA/**/brain_img.nii.gz'
    --infiles "/disk/matthias/hokto/hokto_data/DATA/**/brain_img.nii.gz"
    # will fail
    #--infiles /disk/matthias/hokto/hokto_data/DATA/*/brain_img.nii.gz
    # no glob
    #--infiles '/disk/matthias/hokto/hokto_data/DATA/brain_img.nii.gz'
    # fake
    #--infiles 1 2 3 4 5
    #--max_workers 1
    #--dry-run
    --sys-path /home/matthias/jupyter
    --sys-path '/home/matthias/python'
    --sys-path /home/matthias/jupyter/bia
    '''
    for line in t.splitlines():
        print(line)
        if line.replace(' ', '').startswith('#'):
            t = t.replace(line,'')
    return t


class TestStringMethods(unittest.TestCase):

    def setUp(self):
        # Changing log level to DEBUG
        loglevel = logging.DEBUG
        logging.basicConfig(level=loglevel, stream=sys.stderr)

        self.logger = logging.getLogger(__name__)
        #self.logger.setLevel(loglevel)

    def run_script(self, cmdline) -> subprocess.CompletedProcess:
        pyexe = 'python3'
        executable = 'bin/pybatch.py'
        #executable = 'ls'
        #return subprocess.Popen([pyexe, executable])
        return subprocess.run([pyexe, executable, *cmdline.split()], capture_output=True)
    # def test_upper(self):
    #     self.assertEqual('foo'.upper(), 'FOO')

    # def test_isupper(self):
    #     self.assertTrue('FOO'.isupper())
    #     self.assertFalse('Foo'.isupper())

    # def test_split(self):
    #     s = 'hello world'
    #     self.assertEqual(s.split(), ['hello', 'world'])
    #     # check that s.split fails when the separator is not a string
    #     with self.assertRaises(TypeError):
    #         s.split(2)
    def test_simple(self):

        p = self.run_script(test())
        self.assertEqual(p.returncode, 0, msg='\n'.join(str(p.stdout).split('\\n')) + '\n'.join(str(p.stderr).split('\\n')))


if __name__ == '__main__':
    unittest.main()
    # t = TestStringMethods()
    # t.setUp()
    # t.logger.error('test')
    # t.test_simple()
