#!/usr/local/bin/python3

# TODO:
# - separate ops from exec_bytes to make all ops += 1
# - get rid of need for u?int16(exec_bytes) 
# - small program optimization: turn exec_ops => exec_direct_ops = self.ops[exec_ops[op]] structure
# - cleanup tuning, simplify naming of funcs
# - rename native => operation
# - clamp => min, max :)
# - vsc syntax highlighting
# - vsc preview

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

class VM(object):
    def __init__(self, stdout=None, stdin=None):
        self.operand_stack = []
        self.var_stack = [[NIL]*1024] + [[NIL]*256 for _ in range(49)]
        self.frame_stack = [0]
        self.err_stack = []
        self.start_time = time.time()
        self.stdout = stdout or sys.stdout
        self.stdin = stdin or sys.stdin

    @staticmethod
    def create_func(jam, tune=True, **vm_options):
        vm = VM(**vm_options)
        exec_set, line_exec_indices = VM.compile_exec_set(jam, tune=tune)
        def exec_root():
            vm.exec(exec_set, line_exec_indices)
            return [lambda *sub_args: vm.call(exec_set, f, sub_args, line_exec_indices)
                for f in vm.var_stack[0][0]]
        return exec_root

    def err_line_trace(self, line_exec_indices):
        return " -> ".join(str(VM.err_line_num(line_exec_indices, i))
                           for i in self.frame_stack)

    @staticmethod
    def err_line_num(line_exec_indices, exec_index):
        line_num = 0
        for next_line_index, next_exec_index in enumerate(line_exec_indices):
            if exec_index < next_exec_index:
                break
            line_num = next_line_index
        return line_num + 1

    def call(self, exec_set, ip, args=[], line_exec_indices=None):
        self.operand_stack.extend(VM.to_vm_object(arg) for arg in args)
        self.frame_stack.append(ip)
        self.exec(exec_set, line_exec_indices)
        return self.operand_stack.pop()

    def exec(self, exec_set, line_exec_indices=None):
        exec_ops, exec_args = exec_set
        ops = self._build_ops(exec_args)
        direct_exec_ops = [ops[op] for op in exec_ops]  # DANGER: this will slowdown calls and needs to be rethought
        i = self.frame_stack[-1]
        try:
            while True:
                i = direct_exec_ops[i](i)
        except Exception as e:
            self.frame_stack[-1] = i
            # This is a super hacky and will wrongly consider "actual"
            # IndexErrors as a clean exit, but I don't really care;
            # it allows for no test in main loop and no extra logic
            # in any operation (ie. return)
            if not isinstance(e, IndexError):
                e.jam_line_trace = self.err_line_trace(line_exec_indices)
                raise

    @staticmethod
    def compile_exec_set(jam, tune=True):
        line_exec_indices = [0]
        ips_to_exec_indices = {}
        exec_ops = array.array('B', (0 for _ in jam))
        exec_args = [None] * len(jam)  # this is a little hoggish, but fast
        exec_index = 0
        ip = 0
        while ip < len(jam):
            op = ord(jam[ip])
            ips_to_exec_indices[ip] = exec_index
            exec_ops[exec_index] = op
            ip += 1
            # Handle arguments and special cases (ie. newline)
            if op in b'gGisar?jt':
                x = int(jam[ip:ip+4], 16)
                ip += 4
                if op in b's':
                    exec_args[exec_index] = bytearray(jam[ip:ip+x], 'ascii')
                    ip += x
                elif op in b'i':
                    exec_args[exec_index] = int16(x)
                elif op in b'gG':
                    exec_args[exec_index] = uint16(x)
                else: # addresses and array sizes
                    exec_args[exec_index] = uint16(x)
            elif op in b':#p':
                exec_args[exec_index] = uint16(int(jam[ip:ip+2], 16))
                ip += 2
            elif op in b'\\':
                exec_ops[exec_index] = int(jam[ip:ip+2], 16)
                ip += 2
            elif op in b'\n':
                line_exec_indices.append(exec_index)
                continue
            else:
                pass # no args is okay too
            exec_index += 1

        # Remap address references
        for i, op in enumerate(exec_ops):
            if op in b'r?jt':
                exec_args[i] = ips_to_exec_indices[exec_args[i]]

        # if tune:
        #     exec_bytes = VM.tune_exec_bytes(exec_bytes)

        # Trim excess
        del exec_ops[exec_index:]
        del exec_args[exec_index:]

        return (exec_ops, exec_args), line_exec_indices

    # @staticmethod
    # def tune_exec_bytes(exec_bytes):
    #     funcs = {}
                
    #     def mark_func(exec_bytes, op_ips):
    #         funcs[exec_bytes[op_ips[1]+1]] = \
    #             exec_bytes[op_ips[0]+1]
    #         return True

    #     def global_func_call(exec_bytes, op_ips):
    #         func_addr = funcs.get(exec_bytes[op_ips[0]+1])
    #         if func_addr is None:
    #             return False  # indirect call, leave as is
    #         elif exec_bytes[func_addr] >= 0x80:
    #             # native
    #             exec_bytes[op_ips[0]] = exec_bytes[func_addr]
    #             exec_bytes[op_ips[1]] = 0
    #         else:
    #             # direct call
    #             exec_bytes[op_ips[0]] = 0x90
    #             exec_bytes[op_ips[0]+1] = func_addr
    #         return True

    #     def incl(exec_bytes, op_ips):
    #         if exec_bytes[op_ips[0]+1] == exec_bytes[op_ips[0]+10]:
    #             exec_bytes[op_ips[0]] = 0x91
    #             return True

    #     def decl(exec_bytes, op_ips):
    #         if exec_bytes[op_ips[0]+1] == exec_bytes[op_ips[0]+10]:
    #             exec_bytes[op_ips[0]] = 0x92
    #             return True

    #     def getl2(exec_bytes, op_ips):
    #         exec_bytes[op_ips[0]] = 0x93
    #         return True

    #     def getli(exec_bytes, op_ips):
    #         func_addr = funcs.get(exec_bytes[op_ips[1]+1])
    #         if func_addr is None or exec_bytes[func_addr] != 0x8b:
    #             return False
    #         exec_bytes[op_ips[0]] = 0x94
    #         return True
            
    #     patterns = [
    #         ('rG', mark_func),
    #         ('ig{', getli),
    #         ('g{', global_func_call),
    #         ('#i+:', incl),
    #         ('#i-:', decl),
    #         ('##', getl2)
    #     ]
    #     max_pattern_length = max(len(pattern) for pattern, _ in patterns)
    #     op_ips = []
    #     ip = 0
    #     while ip < len(exec_bytes):
    #         op_ips.append(ip)
    #         if len(op_ips) > max_pattern_length:
    #             op_ips.pop(0)
    #         op = exec_bytes[ip]
    #         ip += 1
    #         if op >= 0x80 or op in b':#p':
    #             ip += 2
    #         elif op in b'gGisar?jt':
    #             if op == b's':
    #                 ip += exec_bytes[ip]
    #             ip += 4
    #         op_window = ''.join(chr(exec_bytes[x] if x >= 0 else 0x00) for x in op_ips)
    #         for pattern, func in patterns:
    #             if op_window[:len(pattern)] == pattern:
    #                 if func(exec_bytes, op_ips):
    #                     op_ips = op_ips[len(pattern):]

    #     return exec_bytes

    @staticmethod
    def to_vm_object(value):
        # Note that reciprocal function does not exist because types do not map 1:1
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
            return ''.join(VM.vm_object_to_str(value))
        elif value is NIL:
            return ''
        else:
            return str(value)
        
    def _build_ops(self, exec_args):
        os = self.operand_stack
        vs = self.var_stack
        gv = vs[0]
        fs = self.frame_stack
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
        def _jmp(i):
            return exec_args[i]
        def _jz(i):
            if os.pop():
                return i + 1
            return exec_args[i]
        def _jsr(i):
            fs[-1] = i
            fs.append(-1)
            return os.pop()
        def _args(i):
            vsi = len(fs) - 1
            for j in range(exec_args[i])[::-1]:
                vs[vsi][j] = os.pop()
            return i + 1
        def _setl(i):
            vs[len(fs)-1][exec_args[i]] = os.pop()
            return i + 1
        def _getl(i):
            os.append(vs[len(fs)-1][exec_args[i]])
            return i + 1
        def _setg(i):
            gv[exec_args[i]] = os.pop()
            return i + 1
        def _getg(i):
            os.append(gv[exec_args[i]])
            return i + 1
        def _ret(i):
            fs.pop()
            return fs[-1] + 1
        def _try(i):
            self.err_stack.append((
                len(self.frame_stack),
                exec_args[i],
                len(os)))
            return i + 1
        def _end_try(i):
            self.err_stack.pop()
            return i + 1
        def _throw(i):
            gv[0] = os.pop()
            if not self.err_stack:
                raise VMError(VM.vm_object_to_str(gv[0]))
            frame_n, j, operand_n = self.err_stack.pop()
            del fs[frame_n:]
            del os[operand_n:]
            return j
        # REMINDER: write exec_index to fs[-1] before executing subroutine in func v
        def _is(i):
            os[-1] = -1 if os[-2] is os.pop() else 0
            return i + 1
        def _weak(i):
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
        def _clamp(i):
            max_, min_ = os.pop(), os.pop()
            os[-1] = min(max(os[-1], min_), max_)
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
            n, si, di, src = os.pop(), os.pop(), os.pop(), os.pop()
            dest = os[-1]
            for j in range(n):
                dest[di+j] = src[si+j]
            return i + 1
        # def _ijsr(exec_bytes, ip):
        #     fs[-1] = ip + 5
        #     fs.append(-1)
        #     return exec_bytes[ip]
        # def _incl(exec_bytes, ip):
        #     vs[len(fs)-1][exec_bytes[ip]] += int16(exec_bytes[ip+3])
        #     return ip + 11
        # def _decl(exec_bytes, ip):
        #     vs[len(fs)-1][exec_bytes[ip]] -= int16(exec_bytes[ip+3])
        #     return ip + 11
        # def _getl2(exec_bytes, ip):
        #     os.append(vs[len(fs)-1][exec_bytes[ip]])
        #     os.append(vs[len(fs)-1][exec_bytes[ip+3]])
        #     return ip + 5
        # def _getli(exec_bytes, ip):
        #     os[-1] = os[-1][int16(exec_bytes[ip])]
        #     return ip + 10
        ops = [_nop] * 256
        ops[ord('i')] = _load_int
        ops[ord('s')] = _load_str
        ops[ord('a')] = _load_array
        ops[ord('r')] = _load_addr
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
        ops[ord('?')] = _jz
        ops[ord('j')] = _jmp
        ops[ord('{')] = _jsr
        ops[ord('p')] = _args
        ops[ord(':')] = _setl
        ops[ord('#')] = _getl
        ops[ord('G')] = _setg
        ops[ord('g')] = _getg
        ops[ord('$')] = _ret
        ops[ord('t')] = _try
        ops[ord('T')] = _end_try
        ops[ord('!')] = _throw        
        ops[0x80] = _is
        ops[0x81] = _weak
        ops[0x82] = _time
        ops[0x83] = _in
        ops[0x84] = _out
        ops[0x85] = _pack
        ops[0x86] = _unpack
        ops[0x87] = _clamp
        ops[0x88] = _data
        ops[0x89] = _array
        ops[0x8a] = _len
        ops[0x8b] = _get
        ops[0x8c] = _set
        ops[0x8d] = _copy
        # ops[0x90] = _ijsr
        # ops[0x91] = _incl
        # ops[0x92] = _decl
        # ops[0x93] = _getl2
        # ops[0x94] = _getli
        return ops

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='MiniP v0.1 | Compile and execute ky/jam scripts')
    parser.add_argument('source', nargs='?',
                        help='source file')
    parser.add_argument('-o', '--output',
                        help='output jam file (implies compile-only)')
    parser.add_argument('-c', '--compile-only', action='store_true',
                        help='compile to jam, then exit (do not execute)')
    parser.add_argument('--compiler-jam',
                        help='compiler jam file')
    parser.add_argument('--debug', action='store_true',
                        help='compile with debug information')
    parser.add_argument('--disable-tuning', action='store_true',
                        help='disable performance tuning of executable code')
    parser.add_argument('--jam', action='store_true',
                        help='source is jam')
    parser.add_argument('--execution-time', action='store_true',
                        help='print time it takes to execute')
    args = parser.parse_args()

    minip_jam = open(args.compiler_jam or 'minip.jam').read()
    source = open(args.source) if args.source else sys.stdin
    is_source_jam = args.jam or (args.source and args.source[-4:].lower()==".jam")
    compile_only = args.compile_only or args.output

    if is_source_jam:
        # no compilation needed, just read in and skip to execution!
        code = source.read()
    else:
        if compile_only:
            out_file = args.output and open(args.output, "wt")
        else:
            out_file = io.StringIO()
        compiler = VM.create_func(minip_jam, tune=False, stdout=out_file, stdin=source)
        try:
            compile, = compiler()
            compile(args.debug)
        except VMError as vm_error:
            sys.stderr.write(str(vm_error))
            exit(1)
        except Exception as e:
            import traceback; traceback.print_exc()
            sys.stderr.write("Compiler error on line {}".format(e.jam_line_trace or '?'))
            exit(1)
        if compile_only:
            exit(0)
        code = out_file.getvalue()

    run_program = VM.create_func(code, tune=(not args.disable_tuning))
    try:
        start_time = time.time()
        run_program()
        if args.execution_time:
            print("Executed in {} seconds".format(time.time()-start_time))
    except Exception as e:
        import traceback; traceback.print_exc()
        sys.stderr.write("Runtime error on line {}".format(e.jam_line_trace or '?'))
        exit(1)