#!/usr/bin/python3
import sys
import os
import subprocess
VERBOSE=0
class Definition:
    def __init__(self, name, value, location):
        self.name = name
        self.value = value
        self.location = location
        self.compiled = False
        self.parent = None
        self.depth = 0

class Location:
    def __init__(self, filename, offset, row, col):
        self.offset = offset
        self.filename = filename
        self.row = row
        self.col = col
    def __str__(self):
        return f"{self.filename}:{self.row}:{self.col}"
    def __eq__(self, other):
        return self.offset == other.offset


class Context:
    WSPACE=' \t\n\r'
    TOKEN_SEP = WSPACE+'('
    STR_REPLACEMENT={}
    STR_LITERAL="\"\'`"

    def __init__(self, included_from = None):
        self.included_from = included_from
        self.macro = included_from.macro if included_from else {}
        self.vars = included_from.vars if included_from else {}
        self.code = included_from.code if included_from else {}
        self.check_token_names = True
        self.emit_channel = None
        self.channels = [ [] for _ in range(10) ]
        self.last_label_num = 0
        self.last_lit=""
        self.bstrlen=0
        self.last_name=""

    def parse_file(self, filename):
        if VERBOSE:
            print(f"Parsing {filename}")
        self.pos = Location(filename, 0, 1, 1)
        self.text = open(filename).read()
        self.parse()

    def parse(self):

        while True:
            self.skip_ws_comments()
            if self.eof():
                break
            if self.try_parse_system_directive():
                continue

            self.error("unexpected token")

    def try_parse_system_directive(self):
        if self.peek() != ":":
            return
        bak = self.pos
        if self.peek(1) == "i":
            return self.parse_include()
        if self.peek(1) == '$':
            return self.parse_macro()
        if self.peek(1) in Context.TOKEN_SEP:
            return self.parse_code()
        if self.consume(":varc"):
            if self.peek() in self.TOKEN_SEP:
                return self.parse_var(True)
            pos = bak
        return False

    def parse_var(self, is_char=False):
        self.skip_ws_comments()
        bak = self.pos
        var_name = self.read_id_token()
        token = self.read_token()
        if not token.isdigit():
            self.error("token size must be integer")
        self.vars[var_name] = self.make_unique(var_name, (token, is_char), bak)
        return True



    def parse_macro(self):
        self.goto_next_char()
        self.goto_next_char()
        start = self.skip_ws_comments()
        if start == self.pos:
            self.error("Macro definition(:$) must be followed by a whitespace.")

        token_name = self.read_id_token()
        body = self.parse_code_block(force_expand=token_name)
        self.macro[token_name] = Definition(token_name,body,start)
        return True

    def parse_code(self):
        self.goto_next_char()
        start = self.skip_ws_comments()
        token_name = self.read_id_token()
        body = self.parse_code_block()
        self.code[token_name] = self.make_unique(token_name,body,start)
        return True

    def make_unique(self, name, value, loc):
        definition = Definition(name, value, loc)
        if name in self.vars:
            self.error(f"{name} at {loc} conflicts with var at {self.vars[name].location}")
        if name in self.code:
            self.error(f"{name} at {loc} conflicts with var at {self.code[name].location}")
        return definition

    def check_token_name(self, token:str):
        if not self.check_token_names:
            return
        if token[0] in Context.STR_LITERAL:
            return
        if token.startswith("[") and token.endswith("]"):
            self.warning(f"Suspicious token name {token}, did you mean [ {token[1:-1]} ] ?")
        elif token.startswith("["):
            self.warning(f"Suspicious token name {token}, did you mean [ {token[1:]} ?")
        elif token.endswith("]"):
            self.warning(f"Suspicious token name {token}, did you mean {token[:-1]} ] ?")


    def parse_code_block(self, force_expand=None):
        start_pos = self.pos
        self.skip_ws_comments()
        self.must_consume("[", "[-start-of-code-block expected")
        body_start = self.pos
        self.skip_ws_comments()
        if self.pos == body_start:
            self.error("[-start-of-code-block expected, suspicious token found")
        body = []

        while not self.eof():
            self.skip_ws_comments()
            if self.peek() == "]" and self.peek(1) in Context.TOKEN_SEP:
                break

            if self.peek() == "[" and self.peek(1) in Context.TOKEN_SEP:
                token = self.parse_code_block(force_expand)
                body.append(token)
            else:
                token = self.read_token(f" for code block from {start_pos}")
                self.check_token_name(token)


                if token == force_expand and token in self.macro:
                    for child_token in self.macro[token]:
                        body.append(child_token)
                else:
                    body.append(token)
        self.must_consume("]", "]-end-of-code-block expected")

        return body

    def warning(self, warn):
        self.error(warn)

    def read_token(self, context=""):
        self.skip_ws_comments()
        if self.peek() in '`"\'':
            return self.read_string_token()

        start = self.skip_while(lambda x:x not in Context.TOKEN_SEP)
        if self.pos == start:
            self.error(f"token expected{context}")
        return self.substr(start, self.pos)

    def read_string_token(self, ):
        delimiter = self.peek()
        self.goto_next_char()
        string = ""
        while not self.eof():
            if self.peek() == delimiter:
                self.goto_next_char()
                break
            if self.peek() == "\n":
                self.error("unterminated string literal")
            if self.peek() != '\\':
                string += self.peek()
                self.goto_next_char()
                continue
            self.goto_next_char() # skip initial \\
            found = False
            attempt = ""
            for x in range(3):
                attempt += self.peek()
                self.goto_next_char()
                if attempt in Context.STR_REPLACEMENT:
                    string += Context.STR_REPLACEMENT[attempt]
                    found = True
                    break
            if not found:
                self.error("Unable to find \\-string-replacement")
        return delimiter + string

    def read_id_token(self):
        token = self.read_token()
        if token.isdigit():
            self.error("id-token expected, but number literal was read")
        return token


    def parse_include(self):
        if self.peek(2) not in self.WSPACE + '"':
            return False
        self.goto_next_char()
        self.goto_next_char()
        self.skip_ws_comments()
        self.must_consume('"', "Include expects string literal")

        path_start = self.skip_while(lambda x:x not in '"\n')
        path = self.substr(path_start, self.pos)
        self.must_consume('"', "Incorrect include path")

        child = Context(self)
        child.parse_file(path)

        return True

    def substr(self, posfrom:Location, posto:Location):
        return self.text[posfrom.offset:posto.offset]


    def skip_while(self, func):
        start = self.pos
        while not self.eof():
            if func(self.peek()):
                self.goto_next_char()
            else:
                break
        return start

    def peek(self,n=0):
        return self.text[n+self.pos.offset:self.pos.offset+1+n]

    def consume(self, c):
        if self.text[self.pos.offset:self.pos.offset+len(c)] == c:
            for _ in c:
                self.goto_next_char()
            return True
        return False

    def must_consume(self, c, message):
        if not self.consume(c):
            raise Exception(f"{self.pos}:{message}")

    def skip_ws_comments(self):
        start = self.pos
        while not self.eof():
            step_pos = self.skip_while(lambda x: x in Context.WSPACE)
            if self.consume('('):
                depth = 1
                while depth >= 1:
                    if self.eof():
                        self.error(f"EOF reached while parsing comment at {step_pos}, current nesting depth is {depth}")
                    if self.peek() == ')':
                        depth -= 1
                    elif self.peek() == '(':
                        depth += 1
                    self.goto_next_char()
            if step_pos == self.pos:
                break
        return start

    def eof(self):
        return self.pos.offset >= len(self.text)

    def goto_next_char(self):
        new_offset = self.pos.offset + 1
        if self.peek() == "\n":
            self.pos = Location(self.pos.filename,
                new_offset,  self.pos.row + 1, 1)
        else:
            self.pos = Location(self.pos.filename,
                new_offset, self.pos.row, self.pos.col + 1)

    def error(self, message):
        included_from = ""
        parent = self.included_from
        while parent:
            included_from += f"\n(included from {self.included_from.pos})"
            parent = parent.included_from
        raise Exception(f"{self.pos}:{message}{included_from}")

    def compile(self, func):
        self.pos = Location("(compilation)",0,0,0)
        for funcdef in self.code.values():
            self.last_label_num+=1
            funcdef.name = self.make_label("F")
        for vardef in self.vars.values():
            self.last_label_num+=1
            vardef.name = self.make_label("V")

        if func not in self.code:
            self.error(f"main function '{func}' is not defined")
        self.current_func = self.code[func]
        self.function_to_compile = [self.current_func]

        if ":prologue" in self.macro:
            self.last_lit = self.code[func].name
            self.do_compile_macro(":prologue")
        self.do_compile()

    def do_compile(self):
        while self.function_to_compile:
            func : Definition = self.function_to_compile.pop()
            if func.compiled:
                continue
            self.current_func = func
            func.compiled = True
            self.last_name = func.name
            self.do_compile_macro(":code-block-prologue")
            for token in func.value:
                self.do_compile_token(token)
            self.do_compile_macro(":code-block-epilogue")


    def do_compile_token(self, token):
        if self.emit_channel is not None and (type(token) != str or token[0] not in Context.STR_LITERAL):
            self.error(":e-EMIT directive found, but it's not followed by a string literal")

        if type(token) == str:
            token : str = token
            if token[0:1] in Context.STR_LITERAL:
                return self.do_compile_string(token)
            if token.isdigit():
                return self.do_compile_int_lit(int(token))
            if token == ":e":
                self.emit_channel = 0
                return
            if token.startswith(":e") and token[2:].isdigit():
                self.emit_channel = int(token[2:])
                return
            if token == "$bstrlen":
                return self.do_compile_int_lit(self.bstrlen)
            if token in self.macro and not self.macro[token].compiled:
                return self.do_compile_macro(token)
            if token in self.code:
                func = self.code[token]
                self.function_to_compile.append(func)
                self.last_lit = func.name
                return self.do_compile_macro(":func-call")
            if token in self.vars:
                var = self.vars[token]
                self.do_compile_variable(var)
                self.last_lit = var.name
                return self.do_compile_macro(":variable-ref")

            self.error(f"unknown word: {token}")
        elif type(token) == list:
            self.last_label_num += 1
            block = Definition(self.make_label('P'), token, self.pos)
            block.parent = self.current_func
            block.depth = self.current_func.depth+1
            self.function_to_compile.append(block)
            self.last_lit = block.name
            return self.do_compile_macro(":code-block-ref")
        else:
            self.error("unknown token")

    def do_compile_variable(self, var : Definition):
        if var.compiled:
            return
        size, is_char = var.value
        self.last_label_num += 1
        self.last_name = var.name
        self.last_lit = size
        var.compiled=True
        if is_char:
            return self.do_compile_macro(":global-variable-decl-char")
        return self.do_compile_macro(":global-variable-decl-cell")

    def make_label(self, pfx, offset=0):
        return f"{pfx}{self.last_label_num+offset:07X}"

    def do_compile_string(self, string):
        string_type, string = string[0], string[1:]
        if string_type == "'":
            if len(string) != 1:
                self.error("char literal must be 1 char long")
            return self.do_compile_int_lit(ord(string))

        if string_type == "`":
            if "{CL!}" in string:
                self.last_label_num += 1
                for prohibited in ["{CL+}", "{CL}", "{CL-}"]:
                    assert prohibited not in string
            string = string.replace("{LIT}", self.last_lit)
            string = string.replace("{NAME}", self.last_name)
            string = string.replace("{BLOCK_DEPTH}", str(self.current_func.depth))
            string = string.replace("{CL+}", self.make_label("L", 1))
            string = string.replace("{CL-}", self.make_label("L", -1))
            string = string.replace("{CL!}", self.make_label("L"))
        data = string.encode("utf-8")
        if self.emit_channel is None:
            self.bstrlen = len(data)
        if self.emit_channel is not None:
            self.channels[self.emit_channel].append(data)
            self.emit_channel = None
        elif string_type == "\"":
            self.last_lit = string
            self.do_compile_macro(":string-literal")
        else:
            self.error("nyi: string literal")

    def do_compile_macro(self, macro : str):
        if macro not in self.macro:
            self.error(f"Macro {macro} not defined")
        macro : Definition = self.macro[macro]
        if macro.compiled: #macro name inside of macro
            # TODO: call?
            return
        macro.compiled = True
        for token in macro.value:
            self.do_compile_token(token)
        macro.compiled = False


    def do_compile_int_lit(self, i):
        self.last_lit = str(i)
        if 0 <= i <= 255 and ":int-literal-u8" in self.macro:
            return self.do_compile_macro(":int-literal-u8")

        if ":int-literal" not in self.macro:
            self.error(":int-literal macro is not defined")

        self.do_compile_macro(":int-literal")

    def dump(self, name):
        with open(name, "w") as f:
            for i, channel in enumerate(self.channels):
                if not channel:
                    continue
                for entry in channel:
                    s = str(entry, 'utf-8')
                    if ':' not in s:
                        s = "    " + s
                    print(s, file=f)


def init_context():
    for src, dst in [
        ('\\', '\\\\'), ('0', '\\\0'), ('\'', '\\\''),
        ('`', '`'),
        ('\"', '\\"'), ('t', '\\\t'), ('n', '\\n'),
        ('r', '\\r')
    ]:
        Context.STR_REPLACEMENT[src]=dst

    for x in "xX":
        for h0 in "0123456789ABCDEFabcdef":
            for h1 in "0123456789ABCDEFabcdef":
                Context.STR_REPLACEMENT[x + h0 + h1] = f"\\x{int(h0+h1,16):02x}"


def run(input_filename="fizzbuzz.morth", output="nasm"):
    assert output in ["nasm", "nasm-ld", "nasm-ld-pipe"]
    input_filename = input_filename.replace("\\","/")
    if input_filename.startswith("./"):
        input_filename = input_filename[2:]
    ctx = Context()
    core = Context(ctx)
    core.parse_file("std.morth")
    ctx.parse_file(input_filename)
    ctx.compile("main")
    basename = input_filename
    if (slash := input_filename.rfind('/')) >= 0:
        basename = input_filename[slash+1:]
    output_asm = f"out/{basename[:basename.rindex('.')]}.asm"
    ctx.dump(output_asm)
    if output.startswith("nasm-ld"):
        os.system(f"nasm -felf64 {output_asm}")
        BASE=output_asm[:output_asm.rindex('.')]
        os.system(f"ld {BASE}.o -o{BASE}")
        if output.startswith("nasm-ld-pipe"):
            sub = subprocess.Popen(f"./{BASE}", stdout=subprocess.PIPE)
            t = sub.communicate(timeout=5)
            print(sub.returncode)
            return (sub.returncode, t[0], t[1])

init_context()

if __name__ == "__main__":
    filename = "fizzbuzz.morth" if len(sys.argv) <=1 else sys.argv[1]
    mode = "nasm-ld" if len(sys.argv) <=2 else sys.argv[2]
    run(sys.argv[1], mode)