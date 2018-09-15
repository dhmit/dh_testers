# -*- coding: utf-8 -*-

import os
import io

if __name__ == '__main__':
    directory = os.getcwd()

    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith('.py') is not True:
                continue
            fullf = root + os.sep + f
            if 'ext' in root:
                continue
            with io.open(fullf, encoding='latin-1') as fh:
                data = fh.read()
                head = data[0:200]
                if 'utf-8' not in head:
                    print(fullf, ' is not utf-8 compliant')
