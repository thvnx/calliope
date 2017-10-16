# calliope
GDB tool for instruction trace

## Usage
./calliope.py [--disassemble] [--output=filename] [--break=breakpoint] [--limit=n] [—args=program,arg1,…,argn]

| Command | Description |
| --- | --- |
| `--disassemble` | Disassemble instructions |
| `--output=filename` | Output trace in _filename_ |
| `--break=breakpoint` | Set a GDB's breakpoint to _breakpoint_ (a function name) |
| `--limit=n` | Limit the trace to _n_ instructions |
| `--args=program,arg1,...,argn` | Trace the program _program_ with arguments _arg1_ to _argn_ (comma separated list). |

## Warnings
- Poorly tested on debian (x86_64 and AArch64), with GDB 7.7.1 and 7.12-6.
- The architecture must support GDB’s record function.
