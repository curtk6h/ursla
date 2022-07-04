#!/usr/local/bin/python3

# TODO:
# - add _neg(),
# - add undefined?
# - use intarray instead of byte array to avoid unp
# - allow > 256 globals 
# - vm per func? add args and return value to exec
# - structs
# - yield instruction or here
# - vsc syntax highlighting
# - vsc preview

import sys, time

minip_jam = '''j0009\80$r0005:04j001a\81$r0016:05j002b\82$r0027:06j003c\83$r0038:07j004d\84$r0049:08j005e\85$r005a:09j006f\86$r006b:0aj0080\87$r007c:0bj0091\88$r008d:0cj00a2\89$r009e:0dj00b3\8a$r00af:0ej00c4\8b$r00c0:0fj00d5\8c$r00d1:10j00e6\8d$r00e2:11j00f7\8e$r00f3:12s0000:13i0000#0d{:14i000a:15i0009:16i0020:17i0021:18i0022:19i0024:1ai0027:1bi0028:1ci0029:1di002b:1ei002c:1fi002d:20i003a:21i003b:22i003c:23i003d:24i003e:25i003f:26i0040:27i005c:28i007b:29i007d:2ai007e:2b#00#00#00#00#00a0005:2cj01f8p02g2c#00#01g11{$r01e7:2dj0213p01g2c#00g10{$r0205:2ej026ep01i007f:01#01iffff>?026a#00#01i0001g0c{i0000#01g11{g11{;#01i0001-:01j022b#00$r0220:2fi0080#0d{#2f{:30j0299p01g30#00g10{$r028b:31j02bap01g30#00i0030+g10{$r02a6:32j02d8p02#00i0000*#01+$r02c7:33j02f2p01#00i0000/$r02e5:34j03a3p01#00i0000=?0317s00010$#00:01i0000:02#01?034a#01i000a/:01#02i0001+:02j0325#02g0c{:03#02i0001-:04#00?039f#03#04#00i000a%i0030+g11{;#00i000a/:00#04i0001-:04j0360#03$r02ff:35j03cdp03#02g0c{#00i0000#01#02g12{$r03b0:36j0401p01#00g0e{g0c{#00i0000i0000#00g0e{g12{$r03da:37j0431p02#01g0d{#00i0000i0000#00g0e{g12{$r040e:38j0495p02#00g0e{#01g0e{+g0c{:02#02#00i0000i0000#00g0e{g12{$#02#01#00g0e{i0000#01g0e{g12{$#02$r043e:39j05d4p02#01g0e{:02#02i0001-:03#03i0000=?04cdg13$#03#00g0e{*:04#03iffff>?050f#04#01#03g10{g0e{+:04#03i0001-:03j04db#04g0c{:05#01i0000g10{:06#05#06i0000i0000#06g0e{g12{;#06g0e{:07i0001:03#03#02<?05d0#01#03g10{:06#05#00#07i0000#00g0e{g12{;#07#00g0e{+:07#05#06#07i0000#06g0e{g12{;#07#06g0e{+:07#03i0001+:03j0556#05$r04a2:3aj05f3p01g15g31{#00g3a{$r05e1:3bj061dp03#02g0d{#00i0000#01#02g12{$r0600:3cj0651p01#00g0e{g0d{#00i0000i0000#00g0e{g12{$r062a:3dj0681p02#01g0d{#00i0000i0000#00g0e{g12{$r065e:3ej06e5p02#00g0e{#01g0e{+g0d{:02#02#00i0000i0000#00g0e{g12{$#02#01#00g0e{i0000#01g0e{g12{$#02$r068e:3fj07c9p01#00g0e{:01#01i0001-:02#02i0000=?071dg14$i0000:03#02iffff>?0759#03#00#02g10{g0e{+:03#02i0001-:02j0725#03g0d{:04i0000:05i0000:02#02#01<?07c5#00#02g10{:06#04#06#05i0000#06g0e{g12{;#05#06g0e{+:05#02i0001+:02j0773#04$r06f2:40j0825p01i0000:01#00g0e{i0001-:02#02iffff>?0821#01#00#02g10{+:01#02i0001-:02j07f1#01$r07d6:41j084ap03#00?0846#01$j084a#02$r0832:42j0876p02#00g00g04{?0872#01$j0876#00$r0857:43j089fp01#00g00g04{#00g0e{i0000=|$r0883:44j08f7p04i0000:04#01#02<?08f3#00#01g10{#03=?08e2#04i0001+:04#01i0001+:01j08b7#04$r08ac:45j0941p04#01#02<?093b#00#01g10{#03=?092a#01$#01i0001+:01j0907iffff$r0904:46j098bp04#02#01>?0985#02i0001-:02#00#02g10{#03=?0980#02$j0951iffff$r094e:47j09f8p03#02#00g0e{+g0c{:03#03#00#02i0000#00g0e{g12{;#02i0000>?09f4#02i0001-:02#03#02#01g11{;j09c7#03$r0998:48j0a25p02#00i0000#00g0e{#01g46{iffff>$r0a05:49j0a7cp02i0000:02#00g0e{:03#02#03<?0a78#00#02#00#02g10{#01{g11{;#02i0001+:02#00$r0a32:4as00100123456789abcdef:4bj0aafp01g4b#00g10{$r0aa1:4cj0aedp01#00i0061-:01#01i0000<?0ae3#01i0031+$#01i000a+$r0abc:4dj0b11p01#00i002f>#00i003a<&$r0afa:4ej0b49p01#00i002f>#00i003a<&#00i0060>#00i0067<&|$r0b1e:4fj0b81p01#00i0040>#00i005b<&#00i0060>#00i007b<&|$r0b56:50j0bd7p01#00i0040>#00i005b<&#00i0060>#00i007b<&|#00i002f>#00i003a<&|#00i005f=|$r0b8e:51j0bf4p01#00i0000g10{$r0be4:52j0c11p01#00i0001g10{$r0c01:53j0c32p01#00i0000g10{g0e{$r0c1e:54j0c52p02#00i0000#01g11{$r0c3f:55j0c72p02#00i0001#01g11{$r0c5f:56j0ca2p02#00i0000#00i0000g10{#01g3e{g11{$r0c7f:57j0cc6p02#00i0000g10{#01g10{$r0caf:58j0cf1p03#00i0000g10{#01#02g11{;#00$r0cd3:59j0d16p01#00#00g53{i0001-g58{$r0cfe:5aj0d52p01#00g53{i0001-:01#00#01g58{:02#00#01g56{;#00$r0d23:5bj0dc7p02#00g52{:02#00g53{:03#02g0e{:04#03#04=?0da4#00#02#04i0002*g3e{g55{;#00#03i0001+g56{;#00#03#01g59{;#00$r0d5f:5cj0e2dp01i0000:01#00i0000g10{:02#00i0001g10{:03#01#03<?0e29#02#01g10{g08{;#01i0001+:01j0dfd#00$r0dd4:5dj0e5dp02#00#01g0d{g55{;#00i0000g56{;#00$r0e3a:5ej0e7ep01i0002g0d{#00g5e{$r0e6a:5fi0020:60i0069:61i0073:62i0061:63i0072:64i005c:65i003b:66i0023:67i0067:68i003a:69i006a:6ai003f:6bi007b:6ci0070:6di0024:6ei0074:6fi0054:70i005e:71i0021:72i007e:73j0f3bp01#00i0000g10{$r0f2b:76j0f58p01#00i0001g10{$r0f48:77j0f78p02#00i0001#01g11{$r0f65:78j0f95p01#00i0002g10{$r0f85:79j0fb2p01#00i0003g10{$r0fa2:7aj0fcfp01#00i0004g10{$r0fbf:7bj0ff5p01#00i0004g10{i0000g58{$r0fdc:7cj1016p01#00i0004g10{g5a{$r1002:7dj1079p03#00g76{:03#03#01i0000+#02i00f0g0a{g4c{g11{;#03#01i0001+#02i000f&g4c{g11{;#01i0002+$r1023:7ej111ep03#00g76{:03#03#01i0000+#02if000g0a{g4c{g11{;#03#01i0001+#02i0f00g0a{g4c{g11{;#03#01i0002+#02i00f0g0a{g4c{g11{;#03#01i0003+#02i000f&g4c{g11{;#01i0004+$r1086:7fj1165p02#00g77{:02#00g76{#02#01g11{;#00#02i0001+g78{;#02i0001+$r112b:80j11b2p03#00g77{:03#00g76{#03#01g11{;#00#03i0001+#02g7e{:03#00#03g78{$r1172:81j11ffp03#00g77{:03#00g76{#03#01g11{;#00#03i0001+#02g7f{:03#00#03g78{$r11bf:82j126cp04#00g76{:04#00g77{:05#02#03<?1261#04#05#01#02g10{g11{;#05i0001+:05#02i0001+:02j1223#00#05g78{$r120c:83#82:84j12ecp03#00g76{:03#00g77{:04#02#01-:05#04#02-:06#03#02#06g36{:07#03#03#01#06+#01#05g12{;#03#07#01i0000#06g12{;#00$r127f:85j13e9p03#00i0000#01g15g45{i0001+:03#00i0000#01g15g47{i0001+:04#04iffff=?1348i0000:04#00#01#00g0e{g15g46{:05#05iffff=?1377#00g0e{:05#00#04#05#04-g36{:06s0001^g17#01#04-g48{:07g13s0015Syntax error on line #03g35{s0002: #02a0004g3a{#06#07a0003g3b{!r12f9:86j145fp03#00#01g10{:03#03#02=?141c#01i0001+$g13s0009Expected #02g31{s0005 got #03g31{a0004g3a{:04#00#01#04g86{;r13f6:87j1492p02#00#01g10{g17=?148e#01i0001+:01#01$r146c:88j15e4p02i0001:02#00#01g10{:03#03g1e=?14d4#01i0001+:01j14f4#03g20=?14f4iffff:02#01i0001+:01#01:04#00#04g10{g4f{?151e#04i0001+:04j14fai0000:05#04#01-i0001-:06i0001:07#06iffff>?1586#05#00#01#06+g10{g4d{#07*+:05#07i0010*:07#06i0001-:06j153e#01#04=?15cfg13s0011Expected int got #00#01g10{a0002g3a{:08#00#01#08g86{;i0000#05#02*g2d{;#04$r149f:89j16f5p03#01#02g10{g51{~?164eg13s0016Expected wordchar got #01#02g10{g31{a0002g3a{:03#01#02#03g86{;i0000:04#01#02#04+g10{g51{?167e#04i0001+:04j1656#01#02#04g36{:05#00g7a{:06#06g52{:07#06g53{:08#07i0000#08#05g46{:09#09iffff=?16e0#08:09#06#05g5c{;i0000#09g2d{;#02#04+$r15f1:8aj1779p03#01#02g10{:03#03g15=#03g17=|?1730#02i0001+$g13s001aExpected end-of-line got '#03g31{s0001'a0003g3a{:04#01#02#04g86{;r1702:8bj17aep03#01#02g89{:02#00g61i0000g2e{g82{;#02$r1786:8cj1a4cp03#01#02g10{:03#03g4e{#03g1e=|#03g20=|?17f5#00#01#02g8c{$#03g19=?1872#02i0001+:02#01#02g10{:03#02:04#01#04g10{g19=~?1845#04i0001+:04j1820#00g62#04#02-g82{;#00#01#02#04g83{;#04i0001+$#03g51{?194c#00#01#02g8a{:02i0000g2e{:05#00g7d{:06#06g52{i0000#06g53{#05g46{:07#07iffff>?18e1#00g67#07g81{;#02$#00g7c{:08#08g52{i0000#08g53{#05g46{:07#07iffff>?1928#00g68#07g81{;#02$#01#02s0014Variable not definedg86{;#03g1c=?197c#00#01#02i0001+g74{:02#01#02g1dg87{$#03g1f=?19dci0000:09#01#02g10{g1f=?19ca#00#01#02i0001+g74{:02#09i0001+:09j1990#00g63#09g82{;#02$#03g28=?1a13#01#02i0001+g89{:02#00g65i0000g2e{g81{;#02$g13s0010Invalid operand #03g31{a0002g3a{:0a#01#02#0ag86{;r17bb:8dj1b59p03g02:03#01#02g10{g2b=?1a8d#03~:03#02i0001+:02j1a62#00g77{:04#00#01#02g8d{:02#01#02g10{g1c=?1b42#02i0001+:02#00g77{:05#01#02g10{g1d=~?1b18#00#01#02g74{:02#01#02g10{g1f=?1b13#02i0001+:02j1ad0#02i0001+:02#00#04#05g85{;#00g6cg80{;j1aa7#03?1b55#00g73g80{;#02$r1a59:8ej1bd3p03#00#01#02g8e{:02s000b&|^=<>+-*/%#01#02g10{g49{?1bcf#01#02g10{:03#00#01#02i0001+g8e{:02#00#03g80{;j1b79#02$r1b66:74j20e5p03#01#02g10{:03#03g26=?1de3#01#02i0001+g10{g29=?1c55#00g77{:04#00g6fi0000g84{;#00#01#02i0001+g75{:02#00g70g80{;j1c9f#00g77{:05#00#01#02i0001+g74{:02#00g77{:04#00g6bi0000g84{;#00#01#02g75{:02#01#02g10{g21=?1d99#01#02g10{g21=?1d94#04:06#02i0001+:02#00g77{:04#00g6ai0000g84{;#00#06i0001+#00g77{g7f{;#01#02g10{g26=?1d7f#00#01#02i0001+g74{:02#00g77{:06#00g6bi0000g84{;#00#01#02g75{:02#00#04i0001+#00g77{g7f{;#06:04j1d8f#00#01#02g75{:02j1cb2j1dc6#01#02g10{g71=?1dc6#02i0001+:02#00g6a#05g84{;#00#04i0001+#00g77{g7f{;j1fe6#03g21=?1feb#00#01#02i0001+g8a{:02i0000g2e{:07#00g7d{:08#08g53{:09#08g52{i0000#09#07g46{:0a#0aiffff=?1e5d#09:0a#08#07g5c{;#01#02g10{:03#03g21=#03g1c=|#03g29=|~?1e8cj1fe6#03g21=?1eb3#00#01#02i0001+g74{:02j1fd8#00g7b{:0b#00g77{:05#00g6ai0000g84{;i00ffg5f{:0c#0b#0cg5c{;i0000:0d#01#02g10{g1c=?1f94#02i0001+:02#01#02g10{g1d=~?1f7a#00#01#02g8a{:02#0ci0000g2e{g5c{;#01#02g10{g1f=?1f69#02i0001+:02#0di0001+:0dj1f15#02i0001+:02#00g6d#0dg81{;#00#01#02g75{:02#0bg5b{;#00#05i0001+#00g77{g7f{;#00g64#05i0005+g84{;#00g69#0ag81{;j2012#03g51{?2017#00#01#02g74{:02#00g66g80{;j2044#03g1a=?2049#00#01#02i0001+g74{:02#00g6eg80{;j2076#03g18=?207b#00#01#02i0001+g74{:02#00g72g80{;j20ac#03g27=?20b1#01#02g10{g15=~?20ac#02i0001+:02j2087j20b1#00g79{#01#02g10{g15=&?20d7#00g15g80{;#00#01#02g8b{$r1be0:8fj2138p03#01#02g29g87{:02#01#02g10{g2a=~?212e#00#01#02g8f{:02j2105#02i0001+$r20f2:75j215cp02#00#01i0000g75{;#00$r2145:90j218cp01#00g76{i0000#00g77{g36{g08{;#00$r2169:91j21dcp01#00s0003NILg5c{;#00s0003ERRg5c{;#00s0001Fg5c{;#00s0001Tg5c{;#00$r2199:92j223bp01i0100g5f{:01#01i0000g5c{;#01i0001g5c{;#01i0002g5c{;#01i0003g5c{;#00#01g5c{;#00$r21e9:93j22bbp02#00i0000i7fffg0c{g11{;#00i0001i0000g11{;#00i0002#01g11{;#00i0003i0004g5f{g92{g11{;#00i0004i0001g5f{g93{g11{;#00$r2248:94j22dcp01i0005g0d{#00g94{$r22c8:95t2303#02#95{#07{#90{#91{;Tj230b#01#08{;'''

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
        def _getg(exec_bytes, ip):
            os.append(vs[exec_bytes[ip]])
            return ip + 2
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
