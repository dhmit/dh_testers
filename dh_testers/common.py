# -*- coding: utf-8 -*-
import inspect
import multiprocessing
import os
import pathlib
import time


def likely_python_module(filename):
    '''
    Given a filename or Path, return the "likely" python module name.  That is, iterate the
    parent directories until it doesn't contain an __init__.py file.

    :rtype: str
    '''
    p = pathlib.Path(filename).resolve()
    paths = []
    if p.name != '__init__.py':
        paths.append(p.stem)
    while True:
        p = p.parent
        if not p:
            break
        if not p.is_dir():
            break

        inits = [f for f in p.iterdir() if f.name == '__init__.py']
        if not inits:
            break

        paths.append(p.stem)

    return '.'.join(reversed(paths))


def get_first_external_stackframe():
    '''
    Get the first FrameInfo that is not in the dh_testers project.

    Obviously, this can't be tested in the dh_testers project

    Returns None if none are found.

    :rtype: inspect.FrameInfo
    '''
    stack = inspect.stack()
    for frame in stack:
        fn = frame.filename
        if 'dh_testers' not in fn and 'python' not in fn:
            return frame
    return None


def source_file_path():
    '''
    Returns a pathlib.Path object for the directory of the package.

    :rtype: pathlib.Path
    '''
    package_name = source_package_name()
    package = __import__(package_name)
    return pathlib.Path(package.__file__).parent


def source_package_name():
    '''
    Returns the source package (the first module without a dot)
    '''
    package_frame = get_first_external_stackframe()
    if package_frame is None:
        return None
    package_name = likely_python_module(package_frame.filename)
    project_package = package_name.split('.')[0]
    return project_package


def import_main_module():
    spm = source_package_name()
    if spm is not None:
        return __import__(spm)


def sort_modules(moduleList):
    '''
    Sort a lost of imported module names such that most recently modified is
    first.  In ties, last accesstime is used then module name

    Will return a different order each time depending on the last mod time

    :rtype: list(str)
    '''
    sort = []
    modNameToMod = {}
    for mod in moduleList:
        modNameToMod[mod.__name__] = mod
        fp = mod.__file__ # returns the py or pyc file
        stat = os.stat(fp)
        lastmod = time.localtime(stat[8])
        asctime = time.asctime(lastmod)
        sort.append((lastmod, asctime, mod.__name__))
    sort.sort()
    sort.reverse()
    # just return module list
    outMods = [modNameToMod[modName] for lastmod, asctime, modName in sort]
    return outMods


def cpus():
    '''
    Returns the number of CPUs or if >= 3, one less (to leave something out for multiprocessing)
    '''
    cpuCount = multiprocessing.cpu_count() # @UndefinedVariable
    if cpuCount >= 3:
        return cpuCount - 1
    else:
        return cpuCount


if __name__ == '__main__':
    from .testRunner import main_test
    main_test()
