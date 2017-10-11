#!/usr/bin/python

import sys
import getopt
import subprocess

disassemble = False
outputfile  = 'trace'
breakpoint  = 'main'
limit       = None
gdb_args    = 'a.out'

try:
    opts, args = getopt.getopt(sys.argv[1:],
                                   "do:b:l:a:",
                                   ["disassemble", "output=", "break=", "limit=", "args="])
except getopt.GetoptError as err:
    print str(err)
    #usage()
    sys.exit(2)

for opt, arg in opts:
    if opt in ("-d", "--disassemble"):
        disassemble = True
    elif opt in ("-o", "--output"):
        outputfile = arg
    elif opt in ("-b", "--break"):
        breakpoint = arg
    elif opt in ("-l", "--limit"):
        limit = arg
    elif opt in ("-a", "--args"):
        gdb_args = arg
disassemble = True # for now only disassemble = True is supported

fout = open ('calliope.stdout', 'w')
ferr = open ('calliope.stderr', 'w')

trace_command = "tracei" + (" 1" if disassemble else " 0") \
  + (" " + outputfile + (".trc" if disassemble else ".brc")) \
  + (" " + breakpoint) \
  + (" " + limit if limit else " 0")

try:
    gdb_process = subprocess.Popen (
        ["gdb", "-ex", "source ./tracei-command.py", "-ex", trace_command, "--args"] + gdb_args.split(','),
        stdout=fout,
        stderr=ferr)
    gdb_process.wait()
except KeyboardInterrupt:
    gdb_process.terminate()

fout.close()
ferr.close()
