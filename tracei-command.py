#!/usr/bin/python

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
    try:
        # get the instruction bytes and join them to form the entire instruction
        insn_bytes = insn[insn.rindex (":") + 1:].strip ().split ()
        insn_merged_b = [insn_bytes[-1]] + [elem[2:] for elem in insn_bytes[-2::-1]]
        insn_merged_b = ''.join (insn_merged_b)
        # get the address
        insn_addr = insn[:insn.index ("<")].strip ()
        return [insn_addr, insn_merged_b]
    except:
        return [insn, insn]


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
        while (not stop_command) and i < l:
            try:
                # disassemble the current instruction
                pc = gdb.parse_and_eval ("$pc")
                disa = arch.disassemble (long_of (pc))

                # write it to outputfile
                try:
                    examine = gdb.execute ("x/{}xb $pc".format (disa[0]["length"]), to_string=True)
                    formated_examine = format_examine (examine)
                    addr = formated_examine[0]
                    insn = formated_examine[1]
                except:
                    insn = "<error while examine $pc>"
                    addr = insn

                if disassemble:
                    asm = " ".join (disa[0]["asm"].split ())
                    of.write ('"{}":{{"insn":"{}","asm":"{}"}},\n'.format (addr, insn, asm))
                else:
                    of.write ('"{}":{{"insn":"{}"}},\n'.format (addr, insn))

                gdb.execute ("stepi", to_string=True)
                i += 1

            except Exception as e:
                print ("Exception: {}".format (e))

        print("Done: {}".format(stop_message))
        print("{} instructions executed".format(i))

        of.write ('"eot":"{}"\n'.format (datetime.datetime.now ()))
        of.write ('}}\n')
        
        of.close ()
        gdb.execute("quit")

instruction_trace_command()
signal.signal(signal.SIGINT, handler)
