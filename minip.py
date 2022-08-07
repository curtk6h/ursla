#!/usr/local/bin/python3

# TODO:
# - rename native => operation
# - clamp => min, max :)
# - vsc syntax highlighting
# - vsc preview

import sys, time, io, array

assert sys.byteorder == 'little' # sorry ;)

def int16(value):
    return ((value&0xFFFF)^0x8000) - 0x8000

def uint16(value):
    return value & 0xFFFF

_BIT_POS = [0, 0, 1, 26, 2, 23, 27, 0, 3, 16, 24, 30, 28, 11, 0, 13, 4, 7, 17, 0, 25, 22, 31, 15, 29, 10, 12, 6, 0, 21, 14, 9, 5, 20, 8, 19, 18]

def ffb(x):
    # NOTE: this only works for values where 1 bit is set
    return _BIT_POS[(x&-x)%37]

NIL = None; T = -1; F = 0

class VMError(Exception):
    pass

class VM(object):
    def __init__(self, stdout=None, stdin=None):
        self.operand_stack = []
        self.var_stack = [[NIL]*1024] + [[NIL]*256 for _ in range(49)]
        self.frame_stack = [-1]
        self.err_stack = []
        self.start_time = time.time()
        self.stdout = stdout or sys.stdout
        self.stdin = stdin or sys.stdin
        self._init_ops()

    @staticmethod
    def err_line_num(line_ips, ip):
        line_num = 0
        for next_line_index, next_ip in enumerate(line_ips):
            if ip < next_ip:
                break
            line_num = next_line_index
        return line_num + 1

    def err_line_trace(self, line_ips):
        return " -> ".join(str(VM.err_line_num(line_ips, ip))
                           for ip in self.frame_stack)

    def exec(self, exec_bytes, ip=0, *args):
        self.operand_stack.extend(args)
        self.frame_stack.append(ip)
        ops = self.ops
        try:
            while True:
                ip = ops[exec_bytes[ip]](exec_bytes, ip+1)
        except IndexError:
            # this is a super hacky way to assume proper exit, 
            # however, it allows for no conditional in main loop and
            # no extra logic in any operation
            pass
        finally:
            self.frame_stack.append(ip)
        return self.operand_stack.pop()

    @staticmethod
    def compile_exec_bytes(jam):
        line_ips = [0]
        exec_bytes = array.array('H', (0 for _ in range(len(jam)+6)))
        ip = 0
        while ip < len(jam):
            op = jam[ip]
            exec_bytes[ip] = ord(op)
            ip += 1
            if op in 'gGisar?jt':
                x = int(jam[ip:ip+4], 16)
                exec_bytes[ip] = uint16(x)
                ip += 4
                if op == 's':
                    x += ip
                    while ip < x:
                        exec_bytes[ip] = ord(jam[ip])
                        ip += 1
            elif op in ':#p':
                exec_bytes[ip] = int(jam[ip:ip+2], 16)
                ip += 2
            elif op == '\\':
                exec_bytes[ip-1] = int(jam[ip:ip+2], 16)
                ip += 2
            elif op == '\n':
                line_ips.append(ip)
            else:
                pass # no params
        exec_bytes[ip] = ord('g')    # push zeroth global aka ERR
        exec_bytes[ip+5] = ord('$')  # return (TODO: don't do this)
        return exec_bytes, line_ips

    @staticmethod
    def tune_exec_bytes(exec_bytes):
        funcs = {}
                
        def mark_func(exec_bytes, op_ips):
            funcs[exec_bytes[op_ips[1]+1]] = \
                exec_bytes[op_ips[0]+1]
            return True

        def global_func_call(exec_bytes, op_ips):
            func_addr = funcs.get(exec_bytes[op_ips[0]+1])
            if func_addr is None:
                return False  # indirect call, leave as is
            elif exec_bytes[func_addr] >= 0x80:
                # native
                exec_bytes[op_ips[0]] = exec_bytes[func_addr]
                exec_bytes[op_ips[1]] = 0
            else:
                # direct call
                exec_bytes[op_ips[0]] = 0x90
                exec_bytes[op_ips[0]+1] = func_addr
            return True

        def incl(exec_bytes, op_ips):
            if exec_bytes[op_ips[0]+1] == exec_bytes[op_ips[0]+10]:
                exec_bytes[op_ips[0]] = 0x91
            return True

        def decl(exec_bytes, op_ips):
            if exec_bytes[op_ips[0]+1] == exec_bytes[op_ips[0]+10]:
                exec_bytes[op_ips[0]] = 0x92
            return True

        def getl2(exec_bytes, op_ips):
            exec_bytes[op_ips[0]] = 0x93
            return True

        def getli(exec_bytes, op_ips):
            func_addr = funcs.get(exec_bytes[op_ips[1]+1])
            if func_addr is None or exec_bytes[func_addr] != 0x8b:
                return False
            exec_bytes[op_ips[0]] = 0x94
            return True
            
        patterns = [
            ('rG', mark_func),
            ('ig{', getli),
            ('g{', global_func_call),
            ('#i+:', incl),
            ('#i-:', decl),
            ('##', getl2)
        ]
        max_pattern_length = max(len(pattern) for pattern, _ in patterns)
        op_ips = []
        ip = 0
        while ip < len(exec_bytes):
            op_ips.append(ip)
            if len(op_ips) > max_pattern_length:
                op_ips.pop(0)
            op = exec_bytes[ip]
            ip += 1
            if op >= 0x80 or op in b':#p':
                ip += 2
            elif op in b'gGisar?jt':
                if op == b's':
                    ip += exec_bytes[ip]
                ip += 4
            op_window = ''.join(chr(exec_bytes[x] if x >= 0 else 0x00) for x in op_ips)
            for pattern, func in patterns:
                if op_window[:len(pattern)] == pattern:
                    if func(exec_bytes, op_ips):
                        op_ips = op_ips[len(pattern):]

        return exec_bytes

    @staticmethod
    def primitive_to_str(value):
        if isinstance(value, bytearray):
            return value.decode("ascii")
        elif isinstance(value, list):
            return ''.join(map(str, value))
        elif value is NIL:
            return ''
        else:
            return str(value)
        
    def _init_ops(self):
        os = self.operand_stack
        vs = self.var_stack
        gv = vs[0]
        fs = self.frame_stack
        def _nop(exec_bytes, ip):
            return ip
        def _load_int(exec_bytes, ip):
            os.append(int16(exec_bytes[ip]))
            return ip + 4
        def _load_str(exec_bytes, ip):
            n = exec_bytes[ip]
            ip += 4
            os.append(bytearray(x for x in exec_bytes[ip:ip+n]))
            return ip + n
        def _load_array(exec_bytes, ip):
            n = exec_bytes[ip]
            a = os[-n:]
            del os[-n:]
            os.append(a)
            return ip + 4
        def _drop(exec_bytes, ip):
            os.pop()
            return ip
        def _eq(exec_bytes, ip):
            os[-1] = T if os[-2] == os.pop() else F
            return ip
        def _lt(exec_bytes, ip):
            os[-1] = T if os[-2]  < os.pop() else F
            return ip
        def _gt(exec_bytes, ip):
            os[-1] = T if os[-2]  > os.pop() else F
            return ip
        def _and(exec_bytes, ip):
            os[-1] = os[-2] & os.pop()
            return ip
        def _or(exec_bytes, ip):
            os[-1] = os[-2] | os.pop()
            return ip
        def _xor(exec_bytes, ip):
            os[-1] = os[-2] ^ os.pop()
            return ip
        def _not(exec_bytes, ip):
            os[-1] = ~os[-1]
            return ip
        def _neg(exec_bytes, ip):
            os[-1] = -os[-1]
            return ip
        def _add(exec_bytes, ip):
            os[-1] = int16(os[-2]+os.pop())
            return ip
        def _sub(exec_bytes, ip):
            os[-1] = int16(os[-2]-os.pop())
            return ip
        def _mul(exec_bytes, ip):
            os[-1] = int16(os[-2]*os.pop())
            return ip
        def _div(exec_bytes, ip):
            os[-1] = os[-2] // os.pop()
            return ip
        def _mod(exec_bytes, ip):
            os[-1] = os[-2] % os.pop()
            return ip
        def _jmp(exec_bytes, ip):
            return exec_bytes[ip]
        def _jz(exec_bytes, ip):
            if os.pop() == 0:
                return exec_bytes[ip]
            return ip + 4
        def _jsr(exec_bytes, ip):
            fs[-1] = ip
            fs.append(-1)
            return os.pop()
        def _args(exec_bytes, ip):
            vsi = len(fs) - 1
            for i in range(exec_bytes[ip])[::-1]:
                vs[vsi][i] = os.pop()
            return ip + 1
        def _setl(exec_bytes, ip):
            vs[len(fs)-1][exec_bytes[ip]] = os.pop()
            return ip + 2
        def _getl(exec_bytes, ip):
            os.append(vs[len(fs)-1][exec_bytes[ip]])
            return ip + 2
        def _setg(exec_bytes, ip):
            gv[exec_bytes[ip]] = os.pop()
            return ip + 4
        def _getg(exec_bytes, ip):
            os.append(gv[exec_bytes[ip]])
            return ip + 4
        def _ret(exec_bytes, ip):
            fs.pop()
            return fs[-1]
        def _try(exec_bytes, ip):
            self.err_stack.append((
                len(self.frame_stack),
                exec_bytes[ip],
                len(os)))
            return ip + 4
        def _end_try(exec_bytes, ip):
            self.err_stack.pop()
            return ip
        def _throw(exec_bytes, ip):
            gv[0] = os.pop()
            if not self.err_stack:
                raise VMError(self.primitive_to_str(gv[0]))
            frame_n, ip, operand_n = self.err_stack.pop()
            del fs[frame_n:]
            del os[operand_n:]
            return ip
        # REMINDER: write ip to fs[-1] before executing subroutine in func v
        def _is(exec_bytes, ip):
            os[-1] = -1 if os[-2] is os.pop() else 0
            return ip + 1
        def _weak(exec_bytes, ip):
            return ip + 1
        def _time(exec_bytes, ip):
            os.append(uint16(round((time.time()-self.start_time)*1000)))
            return ip + 1
        def _in(exec_bytes, ip):
            os.append(bytearray(self.stdin.read(), 'ascii'))
            return ip + 1
        def _out(exec_bytes, ip):
            self.stdout.write(self.primitive_to_str(os[-1]))
            return ip + 1
        def _pack(exec_bytes, ip):
            value, mask = os.pop(), os.pop()
            os[-1] = uint16((os[-1]&~mask)|(value<<ffb(mask)))
            return ip + 1
        def _unpack(exec_bytes, ip):
            mask = os.pop()
            os[-1] = ((uint16(os[-1])&mask)>>ffb(mask))
            return ip + 1
        def _clamp(exec_bytes, ip):
            max_, min_ = os.pop(), os.pop()
            os[-1] = min(max(os[-1], min_), max_)
            return ip + 1
        def _data(exec_bytes, ip):
            os[-1] = bytearray(os[-1])
            return ip + 1
        def _array(exec_bytes, ip):
            os.append([NIL]*uint16(os.pop()))
            return ip + 1
        def _len(exec_bytes, ip):
            os[-1] = len(os[-1])
            return ip + 1
        def _get(exec_bytes, ip):
            i, a = os.pop(), os.pop()
            os.append(a[uint16(i)])
            return ip + 1
        def _set(exec_bytes, ip):
            x, i, a = os.pop(), os.pop(), os[-1]
            a[uint16(i)] = x
            return ip + 1
        def _copy(exec_bytes, ip):
            n, si, di, src = os.pop(), os.pop(), os.pop(), os.pop()
            dest = os[-1]
            for j in range(n):
                dest[di+j] = src[si+j]
            return ip + 1
        def _ijsr(exec_bytes, ip):
            fs[-1] = ip + 5
            fs.append(-1)
            return exec_bytes[ip]
        def _incl(exec_bytes, ip):
            vs[len(fs)-1][exec_bytes[ip]] += int16(exec_bytes[ip+3])
            return ip + 11
        def _decl(exec_bytes, ip):
            vs[len(fs)-1][exec_bytes[ip]] -= int16(exec_bytes[ip+3])
            return ip + 11
        def _getl2(exec_bytes, ip):
            os.append(vs[len(fs)-1][exec_bytes[ip]])
            os.append(vs[len(fs)-1][exec_bytes[ip+3]])
            return ip + 5
        def _getli(exec_bytes, ip):
            os[-1] = os[-1][int16(exec_bytes[ip])]
            return ip + 10
        self.ops = [_nop] * 256
        self.ops[ord('i')] = _load_int
        self.ops[ord('s')] = _load_str
        self.ops[ord('a')] = _load_array
        self.ops[ord('r')] = _load_int
        self.ops[ord(';')] = _drop        
        self.ops[ord('~')] = _not    
        self.ops[ord('n')] = _neg
        self.ops[ord('=')] = _eq
        self.ops[ord('<')] = _lt
        self.ops[ord('>')] = _gt
        self.ops[ord('|')] = _or
        self.ops[ord('&')] = _and
        self.ops[ord('^')] = _xor
        self.ops[ord('+')] = _add
        self.ops[ord('-')] = _sub
        self.ops[ord('*')] = _mul
        self.ops[ord('/')] = _div
        self.ops[ord('%')] = _mod
        self.ops[ord('?')] = _jz
        self.ops[ord('j')] = _jmp
        self.ops[ord('{')] = _jsr
        self.ops[ord('p')] = _args
        self.ops[ord(':')] = _setl
        self.ops[ord('#')] = _getl
        self.ops[ord('G')] = _setg
        self.ops[ord('g')] = _getg
        self.ops[ord('$')] = _ret
        self.ops[ord('t')] = _try
        self.ops[ord('T')] = _end_try
        self.ops[ord('!')] = _throw        
        self.ops[0x80] = _is
        self.ops[0x81] = _weak
        self.ops[0x82] = _time
        self.ops[0x83] = _in
        self.ops[0x84] = _out
        self.ops[0x85] = _pack
        self.ops[0x86] = _unpack
        self.ops[0x87] = _clamp
        self.ops[0x88] = _data
        self.ops[0x89] = _array
        self.ops[0x8a] = _len
        self.ops[0x8b] = _get
        self.ops[0x8c] = _set
        self.ops[0x8d] = _copy
        self.ops[0x90] = _ijsr
        self.ops[0x91] = _incl
        self.ops[0x92] = _decl
        self.ops[0x93] = _getl2
        self.ops[0x94] = _getli

class JamProgram(object):
    def __init__(self, jam, func_names=[], tune=True, **vm_options):
        self.vm = VM(**vm_options)
        self.exec_bytes, self.line_ips = VM.compile_exec_bytes(jam)
        self.func_names = func_names
        self.err = None
        if tune:
            self.exec_bytes = VM.tune_exec_bytes(self.exec_bytes)

    def err_line_trace(self):
        return self.vm.err_line_trace(self.line_ips)

    def from_py(self, value):
        if value is None:
            return NIL
        elif isinstance(value, str):
            return value.decode("ascii")
        elif isinstance(value, int):
            return int16(value)
        elif isinstance(value, bool):
            return T if value else F
        else:
            return value

    def __call__(self):
        self.err = self.vm.exec(self.exec_bytes)

    def __getattr__(self, name):
        if name not in self.func_names:
            return super(JamProgram, self).__getattr__(name)
        func = self.err[self.func_names.index(name)]
        return lambda *args: self.vm.exec(self.exec_bytes, func, *(self.from_py(arg) for arg in args))

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
        compiler = JamProgram(minip_jam, ['compile'], stdout=out_file, stdin=source)
        try:
            compiler()
            compiler.compile(args.debug)
        except VMError as vm_error:
            sys.stderr.write(str(vm_error))
            exit(1)
        except Exception as e:
            import traceback; traceback.print_exc()
            sys.stderr.write("Compiler error on line {}".format(compiler.err_line_trace()))
            exit(1)
        if compile_only:
            exit(0)
        code = out_file.getvalue()
    
    prog = JamProgram(code, tune=(not args.disable_tuning))
    try:
        start_time = time.time()
        prog()
        if args.execution_time:
            print("Executed in {} seconds".format(time.time()-start_time))
    except Exception as e:
        sys.stderr.write("Runtime error on line {}".format(prog.err_line_trace()))
        exit(1)