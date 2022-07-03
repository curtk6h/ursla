#!/usr/local/bin/python3

# TODO:
# - rename lang, commit
# - implement compiler in lang
# - add _neg(),
# - add undefined?
# - use intarray instead of byte array to avoid unp
# - allow > 256 globals 
# - vm per func? add args and return value to exec
# - yield instruction or here
# - structs

import sys, time


VM_LODI = 'i'
VM_LODS = 's'
VM_LODA = 'a'
VM_LODR = 'r'
VM_DROP = ';'
VM_EQ   = '='
VM_LT   = '<'
VM_GT   = '>'
VM_OR   = '|'
VM_AND  = '&'
VM_XOR  = '^'
VM_NOT  = '~'
VM_ADD  = '+'
VM_SUB  = '-'
VM_MUL  = '*'
VM_DIV  = '/'
VM_MOD  = '%'
VM_JZ   = '?'
VM_JMP  = 'j'
VM_SET  = ':'
VM_GET  = '#'
VM_GETG = 'g'
VM_RET  = '$'
VM_JSR  = '{'
VM_ARGS = 'p'
VM_TRY  = 't'
VM_ETRY = 'T'
VM_THRO = '!'
VM_NATV = '\\'
VM_EOL  = '\n'

class _SyntaxError(Exception):
    def __init__(self, remaining_code_chars, msg):
        super(_SyntaxError, self).__init__(msg)
        self.remaining_code_chars = remaining_code_chars

class Compiler(object):
    def __init__(self, debug=False):
        self.vm_code = []
        self.debug = debug
        self.words = ["NIL", "ERR", "F", "T"]
        self.vs = [list(range(len(self.words)))]

    def compile(self, code):
        try:
            self.code_block(code)
        except _SyntaxError as e:
            error_idx = len(code) - e.remaining_code_chars
            line_num = code[:error_idx].count("\n") + 1
            line_start = code[:error_idx].rfind("\n") + 1
            line = code[line_start:line_start+code[line_start:].find("\n")]
            print("Syntax error on line {}: {}".format(line_num, str(e)))
            print(line)
            print(" "*(error_idx-line_start)+"^")
            exit(0)
        return ''.join(self.vm_code)

    def code_block(self, code):
        code = self._parse_char(code, "{")
        while code[0] != "}":
            code = self.statement(code)
        return code[1:]

    def statement(self, code):
        # if / while / try
        if code[0] == "?":
            if code[1] == "{":
                i = len(self.vm_code)
                self._write_vm_op_w_addr(VM_TRY, 0)
                code = self.code_block(code[1:])
                self._write_vm_op(VM_ETRY)
            else:
                top = len(self.vm_code)
                code = self.expr(code[1:])
                i = len(self.vm_code)
                self._write_vm_op_w_addr(VM_JZ, 0)   
                code = self.code_block(code)
            if code[0] == ":":
                while code[0] == ":":
                    j = i
                    code = code[1:]
                    i = len(self.vm_code)
                    self._write_vm_op_w_addr(VM_JMP, 0)
                    self._write_vm_addr(j+1, len(self.vm_code))
                    if code[0] == "?":
                        code = self.expr(code[1:])
                        j = len(self.vm_code)
                        self._write_vm_op_w_addr(VM_JZ, 0)
                        code = self.code_block(code)
                        self._write_vm_addr(i+1, len(self.vm_code))
                        i = j
                    else:
                        code = self.code_block(code)
            elif code[0] == "^":
                code = code[1:]
                self._write_vm_op_w_addr(VM_JMP, top)
            self._write_vm_addr(i+1, len(self.vm_code))
        # function call
        elif self._is_word(code[0]):
            code = self.expr(code)
            self._write_vm_op(VM_DROP)
        # function or variable assignment
        elif code[0] == ":":
            symbol, code = self._parse_symbol(code[1:])
            try:
                var_idx = self.vs[-1].index(symbol)
            except ValueError:
                var_idx = len(self.vs[-1])
                self.vs[-1].append(symbol)
            if code[0] in ":({": # otherwise, it's just a declaration
                if code[0] == ":":
                    code = self.expr(code[1:])
                else:
                    top = len(self.vm_code)
                    self._write_vm_op_w_addr(VM_JMP, 0)
                    self.vs.append([])
                    n = 0
                    if code[0] == "(":
                        code = code[1:]
                        while code[0] != ")":
                            symbol, code = self._parse_symbol(code)
                            self.vs[-1].append(symbol)
                            if code[0] == ",":
                                code = code[1:]
                            n += 1
                        code = code[1:]
                        self._write_vm_op_w_byte(VM_ARGS, n)
                    code = self.code_block(code)
                    self.vs.pop()
                    self._write_vm_addr(top+1, len(self.vm_code))
                    self._write_vm_op_w_addr(VM_LODR, top+5)
                self._write_vm_op_w_byte(VM_SET, var_idx)
        # return
        elif code[0] == "$":
            code = self.expr(code[1:])
            self._write_vm_op(VM_RET)
        # annotation (aka comment)
        elif code[0] == "@":
            while code[0] != "\n":
                code = code[1:]
        # throw
        elif code[0] == '!':
            code = self.expr(code[1:])
            self._write_vm_op(VM_THRO)
        else:
            pass # empty line is valid statement

        if self.debug and code[0] == "\n":
            self._write_vm_op(VM_EOL)

        return self._parse_char(code, "\n ")

    def expr(self, code):
        code = self.unary_op(code)
        while code[0] in "&|^=<>+-*/%":
            op = code[0]
            code = self.unary_op(code[1:])
            self._write_vm_op(op)
        return code
    
    # def expr(self, code):
    #     code = self.comparison(code)
    #     while code[0] in "&|":
    #         op = code[0]
    #         code = self.comparison(code[1:])
    #         self._write_vm_op(op)
    #     return code
    
    # def comparison(self, code):
    #     code = self.arithmetic(code)
    #     while code[0] in "=<>":
    #         op = code[0]
    #         code = self.arithmetic(code[1:])
    #         self._write_vm_op(op)
    #     return code
    
    # def arithmetic(self, code):
    #     code = self.mul_div_mod(code)
    #     while code[0] in "+-":
    #         op = code[0]
    #         code = self.mul_div_mod(code[1:])
    #         self._write_vm_op(op)
    #     return code
    
    # def mul_div_mod(self, code):
    #     code = self.unary_op(code)
    #     while code[0] in "*/%":
    #         op = code[0]
    #         code = self.unary_op(code[1:])
    #         self._write_vm_op(op)
    #     return code
    
    def unary_op(self, code):
        pre_ops = []
        while code[0] == "~":
            pre_ops.append(code[0])
            code = code[1:]
        op_start = len(self.vm_code)
        code = self.operand(code)
        while code[0] == "(":
            args_start = len(self.vm_code)
            code = code[1:]
            while code[0] != ")":
                code = self.expr(code)
                if code[0] == ",":
                    code = code[1:]
            self._swap_end_chunks(op_start, args_start)
            self._write_vm_op(VM_JSR)
            code = code[1:]
        while pre_ops:
            self._write_vm_op(pre_ops.pop())
        return code

    def operand(self, code):
        # integer
        if code[0] in "0123456789-+":
            value, code = self._parse_int(code)
            self._write_vm_op_w_int(VM_LODI, value)
            return code
        # string
        elif code[0] == '"':
            code = code[1:]
            n = 0
            while code[n] != '"':
                n += 1
            self._write_vm_op_w_int(VM_LODS, n)
            self.vm_code.extend(code[:n])
            return code[n+1:]
        # get variable
        elif self._is_word(code[0]):
            symbol, code = self._parse_symbol(code)
            if symbol in self.vs[-1]:
                self._write_vm_op_w_byte(VM_GET , self.vs[-1].index(symbol))
            elif symbol in self.vs[0]:
                self._write_vm_op_w_byte(VM_GETG, self.vs[ 0].index(symbol))
            else:
                raise _SyntaxError(
                    len(code), "Variable not defined")
            return code
        # group
        elif code[0] == "(":
            code = self.expr(code[1:])
            return self._parse_char(code, ")")
        # array        
        elif code[0] == ",":
            n = 0
            while code[0] == ",":
                code = self.expr(code[1:])
                n += 1
            self._write_vm_op_w_int(VM_LODA, n)
            return code
        # native operation
        elif code[0] == '\\':
            op, code = self._parse_int(code[1:])
            self._write_vm_op_w_byte(VM_NATV, op)
            return code
        else:
            raise _SyntaxError(
                len(code), "Invalid operand {!r}".format(code[0]))

    def _parse_int(self, code):
        n = 0
        if code[n] in "+-":
            n += 1
        while self._is_digit(code[n]):
            n += 1
        if not n:
            raise _SyntaxError(
                len(code), "Expected int got {!r}".format(code[0]))
        return int(code[:n], 16), code[n:]

    def _parse_symbol(self, code):
        if not self._is_word(code[0]):
            raise _SyntaxError(
                len(code), "Expected wordchar got {!r}".format(code[0]))
        n = 0
        while self._is_word(code[n]):
            n += 1
        word = code[:n]
        try:
            symbol = self.words.index(word)
        except ValueError:
            symbol = len(self.words)
            self.words.append(word)
        return symbol, code[n:]

    @staticmethod
    def _is_digit(text):
        return text in "0123456789abcdef"

    @staticmethod
    def _is_word(text):
        return text.isalpha() or text.isdigit() or text == '_'    
        
    @staticmethod
    def _parse_char(code, chars):
        if code[0] not in chars:
            raise _SyntaxError(
                len(code), "Expected {!r} got {!r}".format(chars, code[0]))
        return code[1:]

    def _write_vm_op(self, op):
        self.vm_code.append(op)
        
    def _write_vm_addr(self, off, addr):
        addr_hex = "{0:04x}".format(addr)
        self.vm_code[off+0] = addr_hex[0]
        self.vm_code[off+1] = addr_hex[1]
        self.vm_code[off+2] = addr_hex[2]
        self.vm_code[off+3] = addr_hex[3]
        
    def _write_vm_op_w_byte(self, op, param):
        self.vm_code.extend([op]+[_ for _ in "{0:02x}".format(param)])

    def _write_vm_op_w_int(self, op, param):
        self.vm_code.extend([op]+[_ for _ in "{0:04x}".format(param)])

    def _write_vm_op_w_addr(self, op, param):
        self.vm_code.extend([op]+[_ for _ in "{0:04x}".format(param)])

    def _swap_end_chunks(self, a_start, b_start):
        self.vm_code = self.vm_code[:a_start] +\
            self.vm_code[b_start:] +\
            self.vm_code[a_start:b_start]

def int16(value):
    return ((value&0xFFFF)^0x8000) - 0x8000

def uint16(value):
    return value & 0xFFFF

def cmp(a, b):
    return (a > b) - (a < b)

_BIT_POS = [0, 0, 1, 26, 2, 23, 27, 0, 3, 16, 24, 30, 28, 11, 0, 13, 4, 7, 17, 0, 25, 22, 31, 15, 29, 10, 12, 6, 0, 21, 14, 9, 5, 20, 8, 19, 18]

def ffb(x):
    # NOTE: this only works for values where 1 bit is set
    return _BIT_POS[(x&-x)%37]

class VM(object):
    def __init__(self):
        self.operand_stack = []
        self.var_stack = [None] * 256 * 32
        self.var_stack[0] = None
        self.var_stack[1] = None
        self.var_stack[2] = 0
        self.var_stack[3] = -1
        self.frame_stack = [-1]
        #self.operand_offset_stack = [0]
        self.err_stack = []
        self.start_time = time.time()
        self._init_ops()

    def err_line_num(self, vm_code, frame_index=-1):
        return vm_code[:self.frame_stack[frame_index]].count('\n') + 1

    def err_line_num_path(self, vm_code):
        return " -> ".join(str(self.err_line_num(vm_code, i))
                           for i in range(len(self.frame_stack)))

    def exec_sub(self, exec_bytes, ip, *args):
        fs = self.frame_stack
        fs_end = len(fs)
        fs.append(ip)
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

    @staticmethod
    def compile_exec_bytes(vm_code):
        exec_bytes = bytearray(len(vm_code))
        ip = 0
        while ip < len(vm_code):
            op = vm_code[ip]
            exec_bytes[ip] = ord(op)
            ip += 1
            if op in 'isar?jt':
                x = int(vm_code[ip:ip+4], 16)
                exec_bytes[ip] = (x>>8)&0xFF
                exec_bytes[ip+1] = x&0xFF
                ip += 4
                if op == 's':
                    x += ip
                    while ip < x:
                        exec_bytes[ip] = ord(vm_code[ip])
                        ip += 1
            elif op in ':#gp':
                exec_bytes[ip] = int(vm_code[ip:ip+2], 16)
                ip += 2
            elif op == '\\':
                exec_bytes[ip-1] = int(vm_code[ip:ip+2], 16)
                ip += 2
            else:
                pass # no params
        return VM.tune_exec_bytes(exec_bytes)

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
        #     op = vm_code[ip]
        #     exec_bytes[ip] = ord(op)
        #     ip += 1
        return exec_bytes
    
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
            # if len(os) != self.operand_offset_stack[-1]:
            #     print("WARNING: unbalanced stack {} vs {}".format(
            #         len(os),
            #         self.operand_offset_stack[-1]
            #     ))
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
            #self.operand_offset_stack.append(len(os)-1)
            return os.pop()
        def _args(exec_bytes, ip):
            var_off = (len(fs)-1) * 256
            for i in range(var_off, var_off+exec_bytes[ip])[::-1]:
                vs[i] = os.pop()
            #self.operand_offset_stack[-1] = len(os)
            return ip + 1
        def _setl(exec_bytes, ip):
            var_off = (len(fs)-1) * 256
            vs[var_off+exec_bytes[ip]] = os.pop()
            return ip + 2
        def _getl(exec_bytes, ip):
            var_off = (len(fs)-1) * 256
            os.append(vs[var_off+exec_bytes[ip]])
            return ip + 2
        def _getg(exec_bytes, ip):
            os.append(vs[exec_bytes[ip]])
            return ip + 2
        def _ret(exec_bytes, ip):
            fs.pop()
            #self.operand_offset_stack.pop()
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
            rval = os.pop()
            if not self.err_stack:
                raise RuntimeError("Error: {}".format(rval))
            frame_n, ip, operand_n = self.err_stack.pop()
            var_off = (frame_n-1) * 256
            vs[var_off+1] = rval
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
            os.append(bytearray(sys.stdin.read(), 'ascii'))
            return ip
        def _out(exec_bytes, ip):
            value = os[-1]
            if isinstance(value, bytearray):
                value = value.decode("ascii")
            elif isinstance(value, list):
                value = ''.join(map(str, value))
            elif value is None:
                value = ''
            sys.stdout.write(str(value))
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
        
# Example usage:
# do_something = DoitFunction(open("do_something.doit"))
# print(do_something(1, 2, "foo"))

class Function(object):
    def __init__(self, file_or_code, debug=False):
        self.vm = VM() # TODO: make singleton or something like that
        self.code = file_or_code
        self.debug = debug

    def __call__(self, *args):
        #self.vm_code = 
        #.exec(Compiler(debug=True).compile(open(sys.argv[1]).read()))
        pass

try:
    vm = VM()
    code = open(sys.argv[1]).read()
    if code[0] == '{':
        vm_code = Compiler(debug=True).compile(code)
    else:
        vm_code = code
    #print(vm_code)
    #print("{} bytes".format(len(vm_code)))
    vm.exec(vm.compile_exec_bytes(vm_code))
except Exception as e:
    import traceback; traceback.print_exc()
    sys.stderr.write("Error on line {}".format(vm.err_line_num_path(vm_code)))
