#!/usr/local/bin/python3

# TODO:
# - change clamp() => min() max() :)~
# - add b64(), decodeb64()

import sys, time, io, array

assert sys.byteorder == 'little' # sorry ;)

_BIT_POS = [0, 0, 1, 26, 2, 23, 27, 0, 3, 16, 24, 30, 28, 11, 0, 13, 4, 7, 17, 0, 25, 22, 31, 15, 29, 10, 12, 6, 0, 21, 14, 9, 5, 20, 8, 19, 18]

def ffb(x):
    # NOTE: this only works for values where 1 bit is set
    return _BIT_POS[(x&-x)%37]

NIL = None; T = -1; F = 0

def int16(value):
    return ((value&0xFFFF)^0x8000) - 0x8000

def uint16(value):
    return value & 0xFFFF

class VMError(Exception):
    pass

class InternalVMError(Exception):
    def __init__(self, line_trace):
        super(InternalVMError, self).__init__("Internal error: {}".format(line_trace or '?'))
        self.line_trace = line_trace

class VM(object):
    def __init__(self, stdout=None, stdin=None):
        self.operand_stack = []
        self.var_stack = [[NIL]*1024] + [[NIL]*256 for _ in range(49)]
        self.err_stack = []
        self.frame_stack = [0]
        self.start_time = time.time()
        self.stdout = stdout or sys.stdout
        self.stdin = stdin or sys.stdin

    def call(self, exec_ops, i, args=[], line_exec_indices=None):
        self.operand_stack.extend(VM.to_vm_object(arg) for arg in args)
        self.frame_stack.append(i)
        self.execute(exec_ops, line_exec_indices)
        return self.operand_stack.pop()

    def execute(self, exec_ops, line_exec_indices=None):
        i = self.frame_stack[-1]
        try:
            while True:
                i = exec_ops[i](i)
        except VMError:
            self.frame_stack[-1] = i
            raise
        except Exception as e:
            self.frame_stack[-1] = i  # must happen here so not to throw off line trace
            # This is a super hacky and will wrongly consider "actual"
            # IndexErrors as a clean exit, but I don't really care!
            # It allows for no test in main loop and no extra logic
            # in any operation (ie. return) to eke out even more performance!
            if not isinstance(e, IndexError):
                raise InternalVMError(self.err_line_trace(line_exec_indices)) from e

    def compile_exec_op_list(self, ir, tune=True):
        exec_opcodes, exec_args, line_exec_indices = \
            VM._compile_exec_set(ir, tune=tune)
        ops = self._build_ops(exec_args)
        exec_ops = [ops[opcode] for opcode in exec_opcodes]
        return exec_ops, line_exec_indices

    @staticmethod
    def _compile_exec_set(ir, tune=True):
        line_exec_indices = [0]
        ips_to_exec_indices = {}
        exec_opcodes = array.array('B', (0 for _ in ir))
        exec_args = [None] * len(ir)
        exec_index = 0
        ip = 0
        while ip < len(ir):
            op = ord(ir[ip])
            ips_to_exec_indices[ip] = exec_index
            exec_opcodes[exec_index] = op
            ip += 1
            # Handle arguments and special cases (ie. newline)
            if op in b'gGisaf?jt':
                x = int(ir[ip:ip+4], 16)
                ip += 4
                if op in b's':
                    exec_args[exec_index] = bytearray(ir[ip:ip+x], 'ascii')
                    ip += x
                elif op in b'i':
                    exec_args[exec_index] = int16(x)
                elif op in b'gG':
                    exec_args[exec_index] = uint16(x)
                else: # addresses and array sizes
                    exec_args[exec_index] = uint16(x)
            elif op in b':#p':
                exec_args[exec_index] = uint16(int(ir[ip:ip+2], 16))
                ip += 2
            elif op in b'\\':
                exec_opcodes[exec_index] = int(ir[ip:ip+2], 16)
                ip += 2
            elif op in b'\n':
                line_exec_indices.append(exec_index)
                continue
            else:
                pass # no args is okay too
            exec_index += 1

        # Remap address references
        for i, op in enumerate(exec_opcodes):
            if op in b'f?jt':
                exec_args[i] = ips_to_exec_indices[exec_args[i]]

        # Tune calls (this is an optional step, for performance only)
        if tune:
            global_funcs = {} # index -> byte addr
            def mark_global_func(i):
                global_funcs[exec_args[i+1]] = exec_args[i]
            def global_func_call(i):
                func_addr = global_funcs.get(exec_args[i])
                if func_addr is None:
                    return False # indirect call, leave as is
                elif exec_opcodes[func_addr] >= 0x80:
                    exec_opcodes[i] = exec_opcodes[func_addr]
                    exec_opcodes[i+1] = 0
                else: # direct call
                    exec_opcodes[i] = 0x10
                    exec_args[i] = func_addr
                return True
            def increment_local(i):
                if exec_args[i] == exec_args[i+3]:
                    exec_opcodes[i] = 0x11
                    return True
            def decrement_local(i):
                if exec_args[i] == exec_args[i+3]:
                    exec_opcodes[i] = 0x12
                    return True
            def get_two_locals(i):
                exec_opcodes[i] = 0x13
                return True
            i = 0
            while i < len(exec_opcodes):
                for pattern, func in [
                    (b'fG', mark_global_func),
                    (b'g{', global_func_call),
                    (b'#i+:', increment_local),
                    (b'#i-:', decrement_local),
                    (b'##', get_two_locals)
                ]:
                    if bytes(exec_opcodes[i:i+len(pattern)]) == pattern and func(i):
                        i += len(pattern)
                        break
                else:
                    i += 1

        # Trim excess
        del exec_opcodes[exec_index:]
        del exec_args[exec_index:]

        return exec_opcodes, exec_args, line_exec_indices

    def err_line_trace(self, line_exec_indices):
        return " -> ".join(str(VM.find_line_index(line_exec_indices, i)+1)
                           for i in self.frame_stack)

    @staticmethod
    def find_line_index(line_exec_indices, exec_index):
        line_num = 0
        for next_line_index, next_exec_index in enumerate(line_exec_indices):
            if exec_index < next_exec_index:
                break
            line_num = next_line_index
        return line_num

    @staticmethod
    def to_vm_object(value):
        # Note that reciprocal function does not exist because types do not map 1:1
        # ex. text strings become just data in ursla and can't be distinguished
        # reliably from other non-text data
        if value is None:
            return NIL
        elif isinstance(value, str):
            return value.decode("ascii")
        elif isinstance(value, int):
            return int16(value)
        elif isinstance(value, bool):
            return T if value else F
        elif isinstance(value, list):
            return [VM.to_vm_object(x) for x in value]
        else:
            return value

    @staticmethod
    def vm_object_to_str(value):
        if isinstance(value, bytearray):
            return value.decode("ascii")
        elif isinstance(value, list):
            return '[{}]'.format(','.join(VM.vm_object_to_str(x) for x in value))
        elif value is NIL:
            return ''
        else:
            return str(value)
        
    def _build_ops(self, exec_args):
        os = self.operand_stack
        vs = self.var_stack
        gv = vs[0]
        fs = self.frame_stack
        es = self.err_stack
        def _nop(i):
            return i + 1
        def _load_int(i):
            os.append(exec_args[i])
            return i + 1
        def _load_addr(i):
            os.append(exec_args[i])
            return i + 1
        def _load_str(i):
            os.append(exec_args[i])
            return i + 1
        def _load_array(i):
            n = exec_args[i]
            a = os[-n:]
            del os[-n:]
            os.append(a)
            return i + 1
        def _drop(i):
            os.pop()
            return i + 1
        def _eq(i):
            os[-1] = T if os[-2] == os.pop() else F
            return i + 1
        def _lt(i):
            os[-1] = T if os[-2]  < os.pop() else F
            return i + 1
        def _gt(i):
            os[-1] = T if os[-2]  > os.pop() else F
            return i + 1
        def _and(i):
            os[-1] = os[-2] & os.pop()
            return i + 1
        def _or(i):
            os[-1] = os[-2] | os.pop()
            return i + 1
        def _xor(i):
            os[-1] = os[-2] ^ os.pop()
            return i + 1
        def _not(i):
            os[-1] = ~os[-1]
            return i + 1
        def _neg(i):
            os[-1] = -os[-1]
            return i + 1
        def _add(i):
            os[-1] = int16(os[-2]+os.pop())
            return i + 1
        def _sub(i):
            os[-1] = int16(os[-2]-os.pop())
            return i + 1
        def _mul(i):
            os[-1] = int16(os[-2]*os.pop())
            return i + 1
        def _div(i):
            os[-1] = os[-2] // os.pop()
            return i + 1
        def _mod(i):
            os[-1] = os[-2] % os.pop()
            return i + 1
        def _jump(i):
            return exec_args[i]
        def _jump_if_zero(i):
            if os.pop():
                return i + 1
            return exec_args[i]
        def _call(i):
            fs[-1] = i
            fs.append(-1)
            return os.pop()
        def _args(i):
            vsi = len(fs) - 1
            for j in range(exec_args[i])[::-1]:
                vs[vsi][j] = os.pop()
            return i + 1
        def _set_local(i):
            vs[len(fs)-1][exec_args[i]] = os.pop()
            return i + 1
        def _get_local(i):
            os.append(vs[len(fs)-1][exec_args[i]])
            return i + 1
        def _set_global(i):
            gv[exec_args[i]] = os.pop()
            return i + 1
        def _get_global(i):
            os.append(gv[exec_args[i]])
            return i + 1
        def _return(i):
            fs.pop()
            return fs[-1] + 1
        def _try(i):
            es.append((len(fs), exec_args[i], len(os)))
            return i + 1
        def _end_try(i):
            es.pop()
            return i + 1
        def _throw(i):
            err = os.pop()
            if not es:
                raise VMError(VM.vm_object_to_str(err))
            frame_n, j, operand_n = es.pop()
            del fs[frame_n:]
            del os[operand_n:]
            os.append(err)
            return j
        # Built-in functions
        def _is(i):
            os[-1] = -1 if os[-2] is os.pop() else 0
            return i + 1
        def _weak(i):
            return i + 1
        def _hash(i):
            os[-1] = hash(VM.vm_object_to_str(os[-1]))
            return i + 1
        def _time(i):
            os.append(uint16(round((time.time()-self.start_time)*1000)))
            return i + 1
        def _in(i):
            os.append(bytearray(self.stdin.read(), 'ascii'))
            return i + 1
        def _out(i):
            self.stdout.write(VM.vm_object_to_str(os[-1]))
            return i + 1
        def _pack(i):
            value, mask = os.pop(), os.pop()
            os[-1] = uint16((os[-1]&~mask)|(value<<ffb(mask)))
            return i + 1
        def _unpack(i):
            mask = os.pop()
            os[-1] = ((uint16(os[-1])&mask)>>ffb(mask))
            return i + 1
        def _min(i):
            os.append(min(os.pop(), os.pop()))
            return i + 1
        def _max(i):
            os.append(max(os.pop(), os.pop()))
            return i + 1
        def _data(i):
            os[-1] = bytearray(os[-1])
            return i + 1
        def _array(i):
            os.append([NIL]*uint16(os.pop()))
            return i + 1
        def _len(i):
            os[-1] = len(os[-1])
            return i + 1
        def _get(i):
            j, a = os.pop(), os.pop()
            os.append(a[uint16(j)])
            return i + 1
        def _set(i):
            x, j, a = os.pop(), os.pop(), os[-1]
            a[uint16(j)] = x
            return i + 1
        def _copy(i):
            n, si, di = os.pop(), os.pop(), os.pop()
            src = os.pop()[si:si+n]
            dest = os[-1]
            for j in range(n):
                dest[di+j] = src[j]
            return i + 1
        # Compound operations 
        def _jump_func_direct(i):
            fs[-1] = i + 1 # advance from "g" to "{"
            fs.append(-1)
            return exec_args[i]
        def _increment_local(i):
            vs[len(fs)-1][exec_args[i]] += int16(exec_args[i+1])
            return i + 4
        def _decrement_local(i):
            vs[len(fs)-1][exec_args[i]] -= int16(exec_args[i+1])
            return i + 4
        def _get_two_locals(i):
            os.append(vs[len(fs)-1][exec_args[i]])
            os.append(vs[len(fs)-1][exec_args[i+1]])
            return i + 2
        ops = [_nop] * 256
        ops[ord('i')] = _load_int
        ops[ord('s')] = _load_str
        ops[ord('a')] = _load_array
        ops[ord('f')] = _load_addr
        ops[ord(';')] = _drop        
        ops[ord('~')] = _not    
        ops[ord('n')] = _neg
        ops[ord('=')] = _eq
        ops[ord('<')] = _lt
        ops[ord('>')] = _gt
        ops[ord('|')] = _or
        ops[ord('&')] = _and
        ops[ord('^')] = _xor
        ops[ord('+')] = _add
        ops[ord('-')] = _sub
        ops[ord('*')] = _mul
        ops[ord('/')] = _div
        ops[ord('%')] = _mod
        ops[ord('?')] = _jump_if_zero
        ops[ord('j')] = _jump
        ops[ord('{')] = _call
        ops[ord('p')] = _args
        ops[ord(':')] = _set_local
        ops[ord('#')] = _get_local
        ops[ord('G')] = _set_global
        ops[ord('g')] = _get_global
        ops[ord('$')] = _return
        ops[ord('t')] = _try
        ops[ord('T')] = _end_try
        ops[ord('!')] = _throw
        ops[0x10] = _jump_func_direct
        ops[0x11] = _increment_local
        ops[0x12] = _decrement_local
        ops[0x13] = _get_two_locals
        ops[0x80] = _is
        ops[0x81] = _weak
        ops[0x82] = _hash
        ops[0x83] = _time
        ops[0x84] = _in
        ops[0x85] = _out
        ops[0x86] = _pack
        ops[0x87] = _unpack
        ops[0x88] = _min
        ops[0x89] = _max
        ops[0x8a] = _data
        ops[0x8b] = _array
        ops[0x8c] = _len
        ops[0x8d] = _get
        ops[0x8e] = _set
        ops[0x8f] = _copy
        return ops

class UrslaScript(object):
    def __init__(self, ir, tune=True, **vm_options):
        self.ir = ir
        self.vm = VM(**vm_options)
        self.exec_ops, self.line_exec_indices = \
            self.vm.compile_exec_op_list(ir, tune=tune)

    @staticmethod            
    def compile(source, debug=False, ursla_filename=None, **vm_options):
        if isinstance(source, str):
            source = io.StringIO(source)
        dest = io.StringIO()
        compile(source, dest, debug=debug, ursla_filename=ursla_filename)
        return UrslaScript(dest.getvalue(), **vm_options)

    def call(self, func_idx, *args):
        return self.vm.call(
            self.exec_ops,
            self.vm.var_stack[0][func_idx],
            args,
            self.line_exec_indices)
        
    def execute(self):
        self.vm.execute(self.exec_ops, self.line_exec_indices)

    def __call__(self, num_funcs=0):
        self.execute()
        return tuple(
            lambda args: self.call(func_idx, args) 
            for func_idx in range(num_funcs)
        )

def compile(source, dest, debug=False, ursla_filename=None):
    ursla_uir = open(ursla_filename or 'ursla.uir').read()
    compile_, = UrslaScript(ursla_uir, tune=False, stdout=dest, stdin=source)(1)
    compile_(debug)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Ursla v0.1 | Compile and execute Ursla scripts')
    parser.add_argument('source', nargs='?',
                        help='source file; if not specified then stdin is used')
    parser.add_argument('-d', '--dest',
                        help='compile to custom file or stdout if set to "", then exit (do not execute)')
    parser.add_argument('-c', '--compile-only', action='store_true',
                        help='compile then exit (do not execute)')
    parser.add_argument('--compiler',
                        help='compiler IR file')
    parser.add_argument('--debug', action='store_true',
                        help='compile with debug information')
    parser.add_argument('--disable-tuning', action='store_true',
                        help='disable performance tuning of executable code')
    parser.add_argument('--ir', action='store_true',
                        help='source is compiled/IR')
    parser.add_argument('--execution-time', action='store_true',
                        help='print time it takes to execute')
    args = parser.parse_args()
    source = open(args.source) if args.source else sys.stdin
    is_ir = args.ir or (args.source and args.source[-4:].lower()==".uir")
    tune = not args.disable_tuning
    compiler_options = dict(debug=args.debug, ursla_filename=args.compiler)

    try:
        if args.compile_only or args.dest is not None:
            if is_ir:
                raise ValueError("Can't compile what is already compiled, duh")
            dest_filename = args.dest
            if dest_filename == "" or (dest_filename is None and args.source is None):
                dest_file = sys.stdout
            else:
                if not dest_filename:  # default dest filename to source filename
                    dest_filename = args.source + "ir"
                dest_file = open(dest_filename, "wt")
            compile(source, dest_file, **compiler_options)
            exit(0)
        if is_ir:
            if not isinstance(source, str):
                source = source.read()
            run_program = UrslaScript(source, tune=tune)
        else:
            run_program = UrslaScript.compile(source, tune=tune, **compiler_options)
    except VMError as e:
        sys.stderr.write(str(e))
        exit(1)

    start_time = time.time()
    run_program()
    if args.execution_time:
        print("Executed in {} seconds".format(time.time()-start_time))