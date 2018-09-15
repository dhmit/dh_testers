# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         testRunner.py
# Purpose:      testing suite
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2018 MIT, Digital Humanities Lab
#               Forked from music21,
#               Copyright © 2006-2016 Michael Scott Cuthbert and the music21
#               Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
The testRunner module contains the all important "main_test" function
that runs tests in a given module.
'''
import doctest
import inspect
import re
import sys
import unittest

# ALL_OUTPUT = []

###### test related functions
from . import common


def add_doc_attr_tests_to_suite(suite,
                           moduleVariableLists,
                           outerFilename=None,
                           globs=False,
                           optionflags=(doctest.ELLIPSIS
                                        | doctest.NORMALIZE_WHITESPACE
                                        )):
    '''
    takes a suite, such as a doctest.DocTestSuite and the list of variables
    in a module and adds from those classes that have a _DOC_ATTR dictionary
    (which documents the properties in the class) any doctests to the suite.
    '''
    dtp = doctest.DocTestParser()
    if globs is False:
        globs = __import__(common.source_package_name()).__dict__.copy()

    elif globs is None:
        globs = {}

    for lvk in moduleVariableLists:
        if not (inspect.isclass(lvk)):
            continue
        docattr = getattr(lvk, '_DOC_ATTR', None)
        if docattr is None:
            continue
        for dockey in docattr:
            documentation = docattr[dockey]
            # print(documentation)
            dt = dtp.get_doctest(documentation, globs, dockey, outerFilename, 0)
            if not dt.examples:
                continue
            dtc = doctest.DocTestCase(dt,
                                      optionflags=optionflags,
                                      )
            # print(dtc)
            suite.addTest(dtc)


def fixDoctests(doctestSuite):
    r'''
    Fix doctests so that adderesses are sanitized, and perhaps a few others.
    '''
    for dtc in doctestSuite: # Suite to DocTestCase -- undocumented.
        if not hasattr(dtc, '_dt_test'):
            continue

        dt = dtc._dt_test # DocTest
        for example in dt.examples: # fix Traceback exception differences Py2 to Py3
            example.want = stripAddresses(example.want, '0x...')


ADDRESS = re.compile('0x[0-9A-Fa-f]+')


def stripAddresses(textString, replacement="ADDRESS"):
    '''
    Function that changes all memory addresses (pointers) in the given
    textString with (replacement).  This is useful for testing
    that a function gives an expected result even if the result
    contains references to memory locations.  So for instance:

    >>> from dh_testers import testRunner
    >>> testRunner.stripAddresses("{0.0} <BlahBlah object at 0x02A87AD0>")
    '{0.0} <BlahBlah object at ADDRESS>'

    while this is left alone:

    >>> testRunner.stripAddresses("{0.0} <music21.humdrum.MiscTandem *>I humdrum control>")
    '{0.0} <music21.humdrum.MiscTandem *>I humdrum control>'


    For doctests, can strip to '...' to make it work fine with doctest.ELLIPSIS

    >>> testRunner.stripAddresses(
    ...     "{0.0} <BlahBlah object at 0x102a0ff10>", '0x...')
    '{0.0} <BlahBlah object at 0x...>'

    :rtype: str
    '''
    return ADDRESS.sub(replacement, textString)


# ------------------------------------------------------------------------------

def main_test(*testClasses,
              run_test=False,
              default_import=True,
              skip_doctest=False,
              verbose=False,
              module_relative=False,
              import_plus_relative=False,
              display_names=False,
              only_doctest=False,
              fail_fast=True):
    '''
    Takes as its arguments modules
    (or a string 'noDocTest' or 'verbose')
    and runs all of these modules through a unittest suite

    Unless 'noDocTest' is passed as a module, a docTest
    is also performed on `__main__`, hence the name "main_test".

    If 'moduleRelative' (a string) is passed as a module, then
    global variables are preserved.

    Run example (put at end of your modules):

    ::

        import unittest
        class Test(unittest.TestCase):
            def testHello(self):
                hello = "Hello"
                self.assertEqual("Hello", hello)

        if __name__ == '__main__':
            from dh_testers.testRunner import main_test
            main_test(Test)
    '''
    runAllTests = True

    # default -- is fail fast.
    if fail_fast:
        optionflags = (
            doctest.ELLIPSIS
            | doctest.NORMALIZE_WHITESPACE
            | doctest.REPORT_ONLY_FIRST_FAILURE
            )
    else:
        optionflags = (
            doctest.ELLIPSIS
            | doctest.NORMALIZE_WHITESPACE
            )

    globs = None
    # start with doc tests, then add unit tests
    if skip_doctest:
        # create a test suite for storage
        s1 = unittest.TestSuite()
    else:
        # create test suite derived from doc tests
        # here we use '__main__' instead of a module
        if not module_relative:
            if default_import:
                main_mod = common.import_main_module()
                if main_mod:
                    globs = main_mod.__dict__.copy()
                else:
                    globs = {}
            else:
                globs = {}
            if import_plus_relative:
                first_external = common.get_first_external_stackframe()
                if first_external is not None:
                    globs.update(first_external[0].f_globals)

        try:
            s1 = doctest.DocTestSuite(
                '__main__',
                globs=globs,
                optionflags=optionflags,
                )
        except ValueError as ve: # no docstrings
            print("Problem in docstrings [usually a missing r value before "
                  + "the quotes:] {0}".format(str(ve)))
            s1 = unittest.TestSuite()


    verbosity = 1
    if verbose:
        verbosity = 2 # this seems to hide most display

    if display_names:
        runAllTests = False

    runThisTest = None
    if len(sys.argv) == 2:
        arg = sys.argv[1].lower()
        if arg not in ('list', 'display', 'verbose', 'nodoctest'):
            # run a test directly named in this module
            runThisTest = sys.argv[1]
    if run_test:
        runThisTest = run_test

    # -f, --failfast
    if only_doctest:
        testClasses = [] # remove cases
    elif not testClasses:
        last_frame = common.get_first_external_stackframe()
        if last_frame is not None:
            last_frame_globals = last_frame[0].f_globals
            testClasses = []
            for k, v in last_frame_globals.items():
                if not inspect.isclass(v):
                    continue
                if (issubclass(v, unittest.TestCase)
                        and 'Slow' not in k
                        and 'External' not in k):
                    testClasses.append(v)

    for t in testClasses:
        if not isinstance(t, str):
            if display_names is True:
                for tName in unittest.defaultTestLoader.getTestCaseNames(t):
                    print('Unit Test Method: %s' % tName)
            if runThisTest is not None:
                tObj = t() # call class
                # search all names for case-insensitive match
                for name in dir(tObj):
                    if (name.lower() == runThisTest.lower()
                           or name.lower() == ('test' + runThisTest.lower())
                           or name.lower() == ('xtest' + runThisTest.lower())):
                        runThisTest = name
                        break
                if hasattr(tObj, runThisTest):
                    print('Running Named Test Method: %s' % runThisTest)
                    tObj.setUp()
                    getattr(tObj, runThisTest)()
                    runAllTests = False
                    break
                else:
                    print('Could not find named test method: %s, running all tests' % runThisTest)

            # normally operation collects all tests
            s2 = unittest.defaultTestLoader.loadTestsFromTestCase(t)
            s1.addTests(s2)

    ### Add _DOC_ATTR tests...
    if not skip_doctest:
        stacks = inspect.stack()
        if len(stacks) > 1:
            outerFrameTuple = stacks[1]
        else:
            outerFrameTuple = stacks[0]
        outerFrame = outerFrameTuple[0]
        outerFilename = outerFrameTuple[1]
        localVariables = list(outerFrame.f_locals.values())
        add_doc_attr_tests_to_suite(s1, localVariables, outerFilename, globs, optionflags)

    if runAllTests is True:
        fixDoctests(s1)

        runner = unittest.TextTestRunner()
        runner.verbosity = verbosity
        runner.run(s1)


if __name__ == '__main__':
    main_test()
