# -*- coding: utf-8 -*-

"""tracei-command.py: GDB tool for instruction trace."""

__author__ = "Laurent Thévenoux"
__copyright__ = "Copyright 2017"
__license__ = "MIT, see LICENSE file"
__email__ = "laurent.thevenoux@gmail.com"

import gdb
import signal
import datetime


stop_message = None
stop_command = False

def long_of (addr):
    try:
        return long (addr)
    except:
        return int (addr)

def format_examine (insn):
    # get the instruction bytes and join them to form the entire instruction
    insn_bytes = insn[insn.rindex (":") + 1:].strip ().split ()
    insn_merged_b = [insn_bytes[0]] + [elem[2:] for elem in insn_bytes[1:]]
    insn_merged_b = ''.join (insn_merged_b)
    if ">:" not in insn:
        # get the address
        insn_addr = insn[:insn.index (":")].strip ()
        # no label
        insn_lbl = "n/a"
    else:
        # get the address
        insn_addr = insn[:insn.index ("<")].strip ()
        # get the label
        insn_lbl = insn[insn.index ("<") + 1:insn.rindex (">")]
    return [insn_addr, insn_merged_b, insn_lbl]


def handler (signum, frame):
    global stop_command, stop_message
    stop_command = True
    stop_message = "ctrl+c has been pressed (signal: {})".format (signum)


class instruction_trace_stop_point (gdb.Breakpoint):
    "Use instruction_trace_stop_point to stop the trace."
    def __init__ (self, spec):
        # init breakpoint at spec
        super(instruction_trace_stop_point, self).__init__(spec, internal=False)

    def stop (self):
        # breakpoint has been reached
        global stop_command, stop_message
        stop_command = True
        stop_message = "breakpoint: {} has been reached".format (self.location)
        return False


class instruction_trace_command (gdb.Command):
    "Use instruction_trace_command command to trace instructions of an entire program or a given function only."

    def __init__ (self):
        # define a new gdb command tracei
        super (instruction_trace_command, self).__init__("tracei", gdb.COMMAND_USER)

    def invoke (self, args, from_tty):
        # invoke the command with the four following parameters (in that specific order):
        # - 0|1     specifies if the instructions must be disassembled
        # - outfile specifies the output file name of the trace
        # - fn      specifies the function name to break in
        # - n       limits the trace to the n first instructions

        args = args.split( )
        disassemble = True if args[0] == "1" else False
        outputfile  = args[1]
        breakpoint  = args[2]
        limit       = int (args[3])

        of = open (outputfile, 'w')
        of.write ('{\n')
        of.write ('"info":{{"calliope":"{}","date":"{}"}},\n'.format (args,
                                                        datetime.datetime.now ()))

        gdb.execute ("set pagination off", to_string=True)
        gdb.execute ("set confirm off",    to_string=True)

        gdb.execute ("break {}".format (breakpoint))
        gdb.execute ("start")

        if breakpoint == 'main':
            # allow to find a frame above main's frame
            gdb.execute ("set backtrace past-main 1", to_string=True)
        else:
            # allow the use of reverse-next command
            gdb.execute ("target record-full", to_string=True)
            # continue to breakpoint
            gdb.execute ("continue")


        # get the address where to stop the trace
        stop_at = gdb.selected_frame().older().pc()

        # set a breakpoint which will stop the trace when reached
        instruction_trace_stop_point ("*{}".format (long_of (stop_at)))

        if not breakpoint == 'main':
            # weird fix to unsure that the first instructions of
            # the targeted function will be traced
            gdb.execute ("reverse-next")

        arch = gdb.selected_frame().architecture()

        of.write ('"trace":{\n')

        i = 0
        l = limit if limit > 0 else sys.maxsize
        global stop_command, stop_message
        while (not stop_command) and i < l:
            try:
                # disassemble the current instruction
                pc = gdb.parse_and_eval ("$pc")
                disa = arch.disassemble (long_of (pc))

                # write it to outputfile
                try:
                    examine = gdb.execute ("x/{}xb $pc".format (disa[0]["length"]), to_string=True)
                    formatted_examine = format_examine (examine)
                    addr = formatted_examine[0]
                    insn = formatted_examine[1]
                    labl = formatted_examine[2]
                except gdb.error:
                    stop_command = True
                    stop_message = "error while examine $pc"
                except:
                    stop_command = True
                    stop_message = "error while formating examine ({})".format (examine)

                if disassemble:
                    asm = " ".join (disa[0]["asm"].split ())
                    of.write ('"{}":{{"insn":"{}","asm":"{}","debug":"{}"}},\n'.format (addr, insn, asm, labl))
                else:
                    of.write ('"{}":{{"insn":"{}"}},\n'.format (addr, insn))

                gdb.execute ("stepi", to_string=True)
                i += 1

            except Exception as e:
                print ("Exception: {}".format (e))

        print("Done: {}".format(stop_message))
        print("{} instructions executed".format(i))

        of.write ('"eot":"{}",\n'.format (datetime.datetime.now ()))
        of.write ('"length":"{}"\n'.format (i))
        of.write ('}}\n')

        of.close ()
        gdb.execute("quit")

instruction_trace_command()
signal.signal(signal.SIGINT, handler)
