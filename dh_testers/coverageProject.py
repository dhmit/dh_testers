# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         coverageProject.py
# Purpose:      Starts Coverage w/ default arguments
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2014-15 MIT DH Project
#               forked from music21, Copyright © 2014-15 Michael Scott Cuthbert
#               and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
import sys

omit_modules = [
                ]

# THESE ARE NOT RELEVANT FOR coveralls.io -- edit .coveragerc to change that
exclude_lines = [
                r'.*main_test\(',
                r'.*#\s*pragma:\s*no cover.*',
                r'class .*External.*',
                r'class .*Slow.*',
                ]


def get_coverage(overrideVersion=False):
    if overrideVersion or sys.version_info.minor == 5:
        # run on Py 3.5 -- to get Py 3.6/3.7 timing...
        try:
            import coverage
            cov = coverage.coverage(omit=omit_modules)
            for e in exclude_lines:
                cov.exclude(e, which='exclude')
            cov.start()
        except ImportError:
            cov = None
    else:
        cov = None
    return cov


def stop_coverage(cov):
    if cov is not None:
        cov.stop()
        cov.save()
