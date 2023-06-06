"""Simple cell example test class"""

import sys
import os

SIMPLECELL_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    '../../examples/simplecell'))

# sys.path.insert(0, SIMPLECELL_PATH)


class TestSimpleCellClass(object):

    """Simple cell example test class for NEURON"""

    def setup(self):
        """Setup"""
        self.old_cwd = os.getcwd()
        self.old_stdout = sys.stdout

        os.chdir(SIMPLECELL_PATH)
        sys.stdout = open(os.devnull, 'w')

    @staticmethod
    def test_exec():
        """Simplecell NEURON: test execution"""
        # When using import instead of execfile this doesn't work
        # Probably because multiprocessing doesn't work correctly during
        # import
        with open('simplecell.py') as sc_file:
            exec(compile(sc_file.read(), 'simplecell.py', 'exec'))  # NOQA

    def teardown(self):
        """Tear down"""

        sys.stdout = self.old_stdout
        os.chdir(self.old_cwd)


class TestSimpleCellArborClass(object):

    """Simple cell example test class for Arbor"""

    def setup(self):
        """Setup"""
        self.old_cwd = os.getcwd()
        self.old_stdout = sys.stdout

        os.chdir(SIMPLECELL_PATH)
        sys.stdout = open(os.devnull, 'w')

    @staticmethod
    def test_exec():
        """Simplecell Arbor: test execution"""
        # When using import instead of execfile this doesn't work
        # Probably because multiprocessing doesn't work correctly during
        # import
        with open('simplecell_arbor.py') as sc_file:
            exec(compile(sc_file.read(),
                'simplecell_arbor.py', 'exec'))  # NOQA

    def teardown(self):
        """Tear down"""

        sys.stdout = self.old_stdout
        os.chdir(self.old_cwd)
