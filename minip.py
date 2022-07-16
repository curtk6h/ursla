#!/usr/local/bin/python3

# TODO:
# - add get/set syntax? foo:x:1 / foo.x
# - ensure all funcs end in return value (that's right, no ending with "}:{ $x }")
# - add undefined to make missing args easier to debug in function calls
# - add types?
# - add unary op for - alongside ~, add _neg()
# - use intarray instead of byte array to avoid unp
# - yield instruction or here
# - vsc syntax highlighting
# - vsc preview

import sys, time, io

def int16(value):
    return ((value&0xFFFF)^0x8000) - 0x8000

def uint16(value):
    return value & 0xFFFF

def cmp(a, b):
    return (a > b) - (a < b)

_BIT_POS = [0, 0, 1, 26, 2, 23, 27, 0, 3, 16, 24, 30, 28, 11, 0, 13, 4, 7, 17, 0, 25, 22, 31, 15, 29, 10, 12, 6, 0, 21, 14, 9, 5, 20, 8, 19, 18]

T = -1; F = 0

def ffb(x):
    # NOTE: this only works for values where 1 bit is set
    return _BIT_POS[(x&-x)%37]

class VMError(Exception):
    pass

class VM(object):
    def __init__(self, stdout=None, stdin=None):
        self.operand_stack = []
        self.var_stack = [None] * 256 * 50
        self.var_stack[0] = None
        self.var_stack[1] = None
        self.var_stack[2] = F
        self.var_stack[3] = T
        self.var_stack[4] = [] # func_ips
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

    def exec_sub(self, exec_bytes, ip, *args):
        fs = self.frame_stack
        fs_end = len(fs)
        fs.append(ip)
        self.operand_stack.extend(args)
        try:
            while len(fs) != fs_end:
                ip = self.ops[exec_bytes[ip]](exec_bytes, ip+1)
        finally:
            fs[-1] = ip
        return self.operand_stack.pop()

    def exec(self, exec_bytes, ip=0):
        ip_end = len(exec_bytes)
        try:
            while ip != ip_end:
                ip = self.ops[exec_bytes[ip]](exec_bytes, ip+1)
        finally:
            self.frame_stack[-1] = ip
        return self.var_stack[4]

    @staticmethod
    def compile_exec_bytes(jam):
        line_ips = [0]
        exec_bytes = bytearray(len(jam))
        ip = 0
        while ip < len(jam):
            op = jam[ip]
            exec_bytes[ip] = ord(op)
            ip += 1
            if op in 'gGisar?jt':
                x = int(jam[ip:ip+4], 16)
                exec_bytes[ip] = (x>>8)&0xFF
                exec_bytes[ip+1] = x&0xFF
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
        return exec_bytes, line_ips

    @staticmethod
    def tune_exec_bytes(exec_bytes):
        # NOO HANLE IN COMPILER? if single return statement w/ no args,
        # indicate inlinable, then totally replace with code. ADD stack kw @0??
        
        # inline single command global calls i.e. natives
        #  1. record (lodr, set-x) where addr[+1] = return
        #  2. (get-x, jsr) with (native)
        # make compound ops:
        #  inc local, ?!=0{, get 2 locals, get local + attr, get local 0
        # window = [0, 0, 0, 0]
        # ip = 0
        # while ip < len(exec_bytes):
        #     op = exec_bytes[ip]
        #     exec_bytes[ip] = ord(op)
        #     ip += 1
        return exec_bytes

    def primitive_to_str(self, value):
        if isinstance(value, bytearray):
            return value.decode("ascii")
        elif isinstance(value, list):
            return ''.join(map(str, value))
        elif value is None:
            return ''
        else:
            return str(value)
    
    def unpack_uint(self, exec_bytes, ip):
        return (exec_bytes[ip]<<8) | exec_bytes[ip+1]
    
    def unpack_int(self, exec_bytes, ip):
        return int16(self.unpack_uint(exec_bytes, ip))
        
    def _init_ops(self):
        os = self.operand_stack
        vs = self.var_stack
        fs = self.frame_stack
        def _nop(exec_bytes, ip):
            return ip
        def _load_int(exec_bytes, ip):
            os.append(self.unpack_int(exec_bytes, ip))
            return ip + 4
        def _load_str(exec_bytes, ip):
            n = self.unpack_uint(exec_bytes, ip)
            ip += 4
            os.append(exec_bytes[ip:ip+n])
            return ip + n
        def _load_array(exec_bytes, ip):
            n = self.unpack_uint(exec_bytes, ip)
            a = os[-n:]
            del os[-n:]
            os.append(a)
            return ip + 4
        def _drop(exec_bytes, ip):
            os.pop()
            return ip
        def _eq(exec_bytes, ip):
            os[-1] = -1 if os[-2] == os.pop() else 0
            return ip
        def _lt(exec_bytes, ip):
            os[-1] = -1 if os[-2]  < os.pop() else 0
            return ip
        def _gt(exec_bytes, ip):
            os[-1] = -1 if os[-2]  > os.pop() else 0
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
            return self.unpack_uint(exec_bytes, ip)
        def _jz(exec_bytes, ip):
            if os.pop() == 0:
                return self.unpack_uint(exec_bytes, ip)
            return ip + 4
        def _jsr(exec_bytes, ip):
            fs[-1] = ip
            fs.append(-1)
            return os.pop()
        def _args(exec_bytes, ip):
            var_off = (len(fs)-1) * 256
            for i in range(var_off, var_off+exec_bytes[ip])[::-1]:
                vs[i] = os.pop()
            return ip + 1
        def _setl(exec_bytes, ip):
            var_off = (len(fs)-1) * 256
            vs[var_off+exec_bytes[ip]] = os.pop()
            return ip + 2
        def _getl(exec_bytes, ip):
            var_off = (len(fs)-1) * 256
            os.append(vs[var_off+exec_bytes[ip]])
            return ip + 2
        def _setg(exec_bytes, ip):
            vs[self.unpack_uint(exec_bytes, ip)] = os.pop()
            return ip + 4
        def _getg(exec_bytes, ip):
            os.append(vs[self.unpack_uint(exec_bytes, ip)])
            return ip + 4
        def _ret(exec_bytes, ip):
            fs.pop()
            return fs[-1]
        def _try(exec_bytes, ip):
            self.err_stack.append((
                len(self.frame_stack),
                self.unpack_uint(exec_bytes, ip),
                len(os)))
            return ip + 4
        def _end_try(exec_bytes, ip):
            self.err_stack.pop()
            return ip
        def _throw(exec_bytes, ip):
            vs[1] = os.pop()
            if not self.err_stack:
                raise VMError(self.primitive_to_str(vs[1]))
            frame_n, ip, operand_n = self.err_stack.pop()
            del fs[frame_n:]
            del os[operand_n:]
            return ip
        # REMINDER: write ip to fs[-1] before executing subroutine in func v
        def _is(exec_bytes, ip):
            os[-1] = -1 if os[-2] is os.pop() else 0
            return ip
        def _weak(exec_bytes, ip):
            return ip
        def _time(exec_bytes, ip):
            os.append(int(round((time.time()-self.start_time)*1000)))
            return ip
        def _in(exec_bytes, ip):
            os.append(bytearray(self.stdin.read(), 'ascii'))
            return ip
        def _out(exec_bytes, ip):
            self.stdout.write(self.primitive_to_str(os[-1]))
            return ip
        def _pack(exec_bytes, ip):
            value, mask = os.pop(), os.pop()
            os[-1] = uint16((os[-1]&~mask)|(value<<ffb(mask)))
            return ip
        def _unpack(exec_bytes, ip):
            mask = os.pop()
            os[-1] = ((uint16(os[-1])&mask)>>ffb(mask))
            return ip
        def _clamp(exec_bytes, ip):
            max_, min_ = os.pop(), os.pop()
            os[-1] = min(max(os[-1], min_), max_)
            return ip
        def _data(exec_bytes, ip):
            os[-1] = bytearray(os[-1])
            return ip
        def _array(exec_bytes, ip):
            os.append([None]*uint16(os.pop()))
            return ip
        def _len(exec_bytes, ip):
            os[-1] = len(os[-1])
            return ip
        def _cmp(exec_bytes, ip):
            os[-1] = cmp(os[-2], os.pop())
            return ip
        def _get(exec_bytes, ip):
            i, a = os.pop(), os.pop()
            os.append(a[uint16(i)])
            return ip
        def _set(exec_bytes, ip):
            x, i, a = os.pop(), os.pop(), os[-1]
            a[uint16(i)] = x
            return ip
        def _copy(exec_bytes, ip):
            n, si, di, src = os.pop(), os.pop(), os.pop(), os.pop()
            dest = os[-1]
            for j in range(n):
                dest[di+j] = src[si+j]
            return ip
        self.ops = [_nop] * 256
        self.ops[ord('i')] = _load_int
        self.ops[ord('s')] = _load_str
        self.ops[ord('a')] = _load_array
        self.ops[ord('r')] = _load_int
        self.ops[ord(';')] = _drop
        self.ops[ord('=')] = _eq
        self.ops[ord('<')] = _lt
        self.ops[ord('>')] = _gt
        self.ops[ord('|')] = _or
        self.ops[ord('&')] = _and
        self.ops[ord('^')] = _xor        
        self.ops[ord('~')] = _not
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
        self.ops[0x8b] = _cmp
        self.ops[0x8c] = _get
        self.ops[0x8d] = _set
        self.ops[0x8e] = _copy

class JamProgram(object):
    def __init__(self, jam, **vm_options):
        self.vm = VM(**vm_options)
        self.exec_bytes, self.line_ips = VM.compile_exec_bytes(jam)
        self.funcs = None

    def err_line_trace(self):
        return self.vm.err_line_trace(self.line_ips)

    def __call__(self, func_names=[]):
        self.funcs = dict(zip(func_names, self.vm.exec(self.exec_bytes)))

    def __getattr__(self, func_name):
        return lambda *args: self.vm.exec_sub(self.exec_bytes, self.funcs[func_name], *args)

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
    parser.add_argument('--jam', action='store_true',
                        help='source is jam')
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
        compiler = JamProgram(minip_jam, stdout=out_file, stdin=source)
        try:
            compiler(['compile'])
            compiler.compile(T if args.debug else F)
        except VMError as vm_error:
            sys.stderr.write(str(vm_error))
            exit(0)
        except Exception as e:
            import traceback; traceback.print_exc()
            sys.stderr.write("Compiler error on line {}".format(compiler.err_line_trace()))
            exit(0)
        if compile_only:
            exit(1)
        code = out_file.getvalue()

    prog = JamProgram(code)
    try:
        prog()
    except Exception as e:
        sys.stderr.write("Runtime error on line {}".format(prog.err_line_trace()))
        exit(0)
