#!/usr/bin/env python

import codecs
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(__file__)
POOLE = os.path.join(HERE, "..", "poole.py")
ACTUAL = os.path.join(HERE, "actual")
EXPECTED = os.path.join(HERE, "expected")
ERRORS = os.path.join(HERE, "errors.diff")

EX_OK = getattr(os, "EX_OK", 0)

if os.path.exists(ACTUAL):
    shutil.rmtree(ACTUAL)

if os.path.exists(ERRORS):
    os.remove(ERRORS)

cmd_init = [POOLE, ACTUAL, "--init"]
cmd_build = [POOLE, ACTUAL, "--build"]
cmd_diff = ["diff", "-Naur", EXPECTED, ACTUAL]

r = subprocess.call(cmd_init, stdout=subprocess.PIPE)
if r != EX_OK:
    sys.exit(1)

r = subprocess.call(cmd_build, stdout=subprocess.PIPE)
if r != EX_OK:
    sys.exit(1)

p = subprocess.Popen(cmd_diff, stdout=subprocess.PIPE)
diff = p.communicate()[0]
if diff:
    with codecs.open(ERRORS, 'w', 'UTF8') as fp:
        fp.write(diff.decode('UTF8'))
    print("failed - see %s for details" % ERRORS)
    sys.exit(1)

print("passed")
