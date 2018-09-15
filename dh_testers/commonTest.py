# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         commonTest.py
# Purpose:      Things common to testing
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-18 MIT DH Lab, Michael Scott Cuthbert
#               Forked from music21, Michael Scott Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Things that are common to testing...
'''
import doctest
import inspect
import os
import pathlib
import types
import warnings

import importlib
import unittest.runner
from unittest.signals import registerResult

from . import common


def default_doctest_suite(module_name=None, globs=None):
    if globs is True:
        globs = __import__(common.source_package_name()).__dict__.copy()
    elif globs in (False, None):
        globs = {}

    docTestOptions = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    kwArgs = {
              'globs': globs,
              'optionflags': docTestOptions,
              }
    # in case there are any tests here, get a suite to load up later
    if module_name is not None:
        s1 = doctest.DocTestSuite(module_name, **kwArgs)
    else:
        s1 = doctest.DocTestSuite(**kwArgs)
    return s1


# from testRunner...
# more silent type...
class ProjectTestRunner(unittest.runner.TextTestRunner):
    def run(self, test):
        "Run the given test case or test suite."
        result = self._makeResult()
        registerResult(result)
        result.failfast = self.failfast
        result.buffer = self.buffer
        with warnings.catch_warnings():
            if hasattr(self, 'warnings') and self.warnings:
                # if self.warnings is set, use it to filter all the warnings
                warnings.simplefilter(self.warnings)
                # if the filter is 'default' or 'always', special-case the
                # warnings from the deprecated unittest methods to show them
                # no more than once per module, because they can be fairly
                # noisy.  The -Wd and -Wa flags can be used to bypass this
                # only when self.warnings is None.
                if self.warnings in ['default', 'always']:
                    warnings.filterwarnings('module',
                            category=DeprecationWarning,
                            message=r'Please use assert\w+ instead.')
            # startTime = time.time()
            startTestRun = getattr(result, 'startTestRun', None)
            if startTestRun is not None:
                startTestRun()
            try:
                test(result)
            finally:
                stopTestRun = getattr(result, 'stopTestRun', None)
                if stopTestRun is not None:
                    stopTestRun()
            # stopTime = time.time()
        # timeTaken = stopTime - startTime
        result.printErrors()

        expectedFails = unexpectedSuccesses = skipped = 0
        try:
            results = map(len, (result.expectedFailures,
                                result.unexpectedSuccesses,
                                result.skipped))
        except AttributeError:
            pass
        else:
            expectedFails, unexpectedSuccesses, skipped = results

        infos = []
        if not result.wasSuccessful():
            self.stream.write("FAILED")
            failed, errored = len(result.failures), len(result.errors)
            if failed:
                infos.append("failures=%d" % failed)
            if errored:
                infos.append("errors=%d" % errored)
        else:
            pass
        if skipped:
            infos.append("skipped=%d" % skipped)
        if expectedFails:
            infos.append("expected failures=%d" % expectedFails)
        if unexpectedSuccesses:
            infos.append("unexpected successes=%d" % unexpectedSuccesses)
        if infos:
            self.stream.writeln(" (%s)" % (", ".join(infos),))
        else:
            pass
        return result


# ------------------------------------------------------------------------------
class ModuleGather:
    r'''
    Utility class for gathering and importing all modules in the project
    package. Puts them in self.modulePaths.

    >>> from dh_testers import commonTest
    >>> mg = commonTest.ModuleGather(stack_level=0, useExtended=True)
    >>> #_DOCS_SHOW print mg.modulePaths[0]
    D:\Web\eclipse\music21base\music21\volume.py
    '''

    def __init__(self, *, start_module=None, useExtended=False,
                 autoWalk=True, stack_level=None):
        if start_module is None:
            frame_record = common.get_first_external_stackframe()
            if frame_record is None and stack_level is None:
                stack_level = 1

            if stack_level is not None:
                frame_record = inspect.stack()[stack_level]

            mod_name = common.likely_python_module(frame_record.filename)
            start_module = __import__(mod_name)
        dirParent = pathlib.Path(start_module.__file__).parent

        # do not store start_module, since modules can't be pickled
        # self.start_module = start_module
        self.start_module_name = start_module.__name__
        self.dirParent = dirParent
        self.useExtended = useExtended
        self.modulePaths = []
        self.moduleSkip = []
        self.moduleSkipExtended = self.moduleSkip + []
        # run these first...
        self.slowModules = []

        # skip any path that contains this string
        self.pathSkip = []
        self.pathSkipExtended = self.pathSkip + []

        self.moduleSkip = [x.replace('/', os.sep) for x in self.moduleSkip]
        self.moduleSkipExtended = [x.replace('/', os.sep)
                                    for x in self.moduleSkipExtended]
        self.pathSkip = [x.replace('/', os.sep) for x in self.pathSkip]
        self.pathSkipExtended = [x.replace('/', os.sep)
                                    for x in self.pathSkipExtended]
        self.slowModules = [x.replace('/', os.sep) for x in self.slowModules]

        # search on init
        if autoWalk:
            self.walk()

    def _visitFunc(self, args, dirname, names):
        '''
        append all module paths from _walk() to self.modulePaths.
        Utility function called from os.walk()
        '''
        for fileName in names:
            if fileName.endswith('py'):
                fp = os.path.join(dirname, fileName)
                if not os.path.isdir(fp):
                    self.modulePaths.append(fp)

    def walk(self):
        '''
        Get all the modules in reverse order, storing them in self.modulePaths
        '''
        def manyCoreSortFunc(name):
            '''
            for many core systems, like the MacPro, running slowest modules first
            helps there be fewer idle cores later
            '''
            name = name[len(str(self.dirParent)) + 1:]
            name = name.replace('.py', '')
            return (name in self.slowModules, name)

        # the results of this are stored in self.curFiles, self.dirList
        for dirpath, unused_dirnames, filenames in os.walk(self.dirParent):
            self._visitFunc(None, dirpath, filenames)

        if common.cpus() > 4:# @UndefinedVariable
            self.modulePaths.sort(key=manyCoreSortFunc)
        else:
            self.modulePaths.sort()

        self.modulePaths.reverse()

    def _getName(self, fp):
        r'''
        Given full file pathlib.Path, find a name for the module
        with _ as the separator.

        >>> from dh_testers import commonTest
        >>> mg = commonTest.ModuleGather(stack_level=0)
        >>> #_DOCS_SHOW mg._getName(r'D:\music21base\music21\chord.py')
        'chord'
        '''
        fn = fp.replace(str(self.dirParent), '') # remove parent
        if fn.startswith(os.sep):
            fn = fn[1:]
        fn = fn.replace(os.sep, '_') # replace w/ _
        fn = fn.replace('.py', '')
        return fn

    def _getNamePeriod(self, fp, *, add_module_name=False):
        r'''
        Given full file path, find a name for the module with . as the separator.

        >>> from dh_testers import commonTest
        >>> mg = commonTest.ModuleGather(stack_level=0)
        >>> name = '/Users/cuthbert/git/music21base/music21/features/native.py'
        >>> #_DOCS_SHOW mg._getNamePeriod(name)
        'features.native'
        '''
        if not isinstance(fp, str):
            fp = str(fp)

        fn = fp.replace(str(self.dirParent), '') # remove parent
        parts = [x for x in fn.split(os.sep) if x]
        if parts[-1] == '__init__.py':
            parts.pop()
        fn = '.'.join(parts) # replace w/ period

        fn = fn.replace('.py', '')
        if add_module_name and fn:
            fn = add_module_name + '.' + fn
        elif add_module_name:
            fn = add_module_name


        return fn

    def load(self):
        '''
        Return a list of module objects that are not in the skip list.

        N.B. the list is a list of actual module objects not names,
        therefore cannot be pickled.
        '''
        modules = []
        for fp in self.modulePaths:
            moduleObject = self.getModule(fp)
            if moduleObject is not None:
                modules.append(moduleObject)
        return modules

    def getModule(self, fp):
        '''
        gets one module object from the file path
        '''
        skip = False
        ms = self.moduleSkip
        if self.useExtended:
            ms = self.moduleSkipExtended

        for fnSkip in ms:
            if fp.endswith(fnSkip):
                skip = True
                break
        if skip:
            return None

        ps = self.pathSkip
        if self.useExtended:
            ps = self.pathSkipExtended


        for dirSkip in ps:
            if dirSkip in fp:
                skip = True
                break
        if skip:
            return None

        name = common.likely_python_module(fp)
        # for importlib
        # name = self._getNamePeriod(fp, add_module_name='music21')

        # print(name, os.path.dirname(fp))
        try:
            with warnings.catch_warnings():
                # warnings.simplefilter('ignore', RuntimeWarning)
                # importlib is messing with coverage...
                mod = importlib.import_module(name)
                # mod = importlib.import_module(name)
        except Exception as excp: # pylint: disable=broad-except
            warnings.warn('failed import: ' + name + ' at ' + str(fp) + '\n'
                + '\tEXCEPTION:' + str(excp).strip())
            return None

        return mod

    def get_module_without_imp(self, fp, start_module=None):
        '''
        gets one module object from the file path without using imp

        start_module is the actual module object for the main project,
        such as "dhFrame" or "gender_novels" or "music21".  If None,
        it will try to import it.
        '''
        if start_module is None:
            start_module = common.import_main_module()
        skip = False
        for fnSkip in self.moduleSkip:
            if fp.endswith(fnSkip):
                skip = True
                break
        if skip:
            return "skip"

        for dirSkip in self.pathSkip:
            dirSkipSlash = os.sep + dirSkip + os.sep
            if dirSkipSlash in fp:
                skip = True
                break
        if skip:
            return "skip"
        moduleName = self._getNamePeriod(fp)
        moduleNames = moduleName.split('.')
        currentModule = start_module
        # print(currentModule, moduleName, fp)

        for thisName in moduleNames:
            if not thisName.strip():
                continue
            if hasattr(currentModule, thisName):
                currentModule = object.__getattribute__(currentModule, thisName)
                if not isinstance(currentModule, types.ModuleType):
                    return "notInTree"
            else:
                return "notInTree"
        mod = currentModule

        print('starting ' + moduleName)
        return mod


if __name__ == '__main__':
    from .testRunner import main_test
    main_test()
