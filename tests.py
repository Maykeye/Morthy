import morth
import pytest

XXX=2**64-1
YYY=2**32-1
LR10=list(range(10))
LR32=list(range(32))

def run_errcode_test(src, raw=None):
    filename = "out/_unittest.morth"
    with open(filename, "w") as f:
        f.write(raw or f": main [ {src} exit ]")
    (res, out, err) = morth.run(filename, "nasm-ld-pipe")
    return res
def run_stdout_test(src):
    filename = "out/_unittest.morth"
    with open(filename, "w") as f:
        f.write(f": run [ {src} ]\n")
        f.write(f": main [ sentinel! run sentinel@ ]\n")
    (res, out, err) = morth.run(filename, "nasm-ld-pipe")
    return out.decode('utf-8')

@pytest.mark.parametrize("num",[0,1,2,10,100,1000,12345,102030,1122444, 2**31, 2**63,2**64-1,0x10203040AABBCCDD])
def test_exit(num):
    assert run_errcode_test(f"{num}") == num & 0xff
def test_exit_using_character_literal():
    assert run_errcode_test(f"'0'") == 48
def test_exit_using_hex_character_literal():
    assert run_errcode_test(f"'\\x32'") == 50

def test_nested_comments():
    assert run_errcode_test("", raw=f": (foo ( b)) main(poo) [(1)10(2(3))exit ] ") == 10
def test_func_call():
    assert run_errcode_test("", raw=
        ": run [ run1 23 + ] \n"
        ": run1 [ run2 100 run2 ] \n"
        ": run2 [ ] \n"
        ": main [ run exit ]"
    ) == 123
@pytest.mark.parametrize("num",[0,1,2,3,4,5,6,7,8,9,49])
def test_hex_digit_digits(num):
    assert run_errcode_test(f"{num} hex-digit") == 48+(num & 0xf)
@pytest.mark.parametrize("num",[10,11,12,13,14,15,31])
def test_hex_digit_hex(num):
    assert run_errcode_test(f"{num} hex-digit") == 55+(num & 0xf)
@pytest.mark.parametrize("s",["", "1 drop", "[ 1 ] drop", "3 swap nip"])
def test_sentinel_balanced(s):
    assert run_errcode_test(f"sentinel! {s} sentinel@ 10") == 10
@pytest.mark.parametrize("s",["drop", "3 swap"])
def test_sentinel_unbalanced(s):
    assert run_errcode_test(f"sentinel! {s} sentinel@ 11 ") == 255
@pytest.mark.parametrize(("s", "res"),
   [("1 2 <", 1), ("2 1 <", 0),
    ("2 1 >", 1), ("1 2 >", 0),
    ("2 1 =", 0), ("1 1 =", 1),
    ("2 1 !=", 1), ("1 1 !=", 0)
])
def test_relop(s, res):
    assert run_errcode_test(f"{s}") == res
def test_xchg0():
    assert run_errcode_test(f"10 20 0 1 xchg") == 10
@pytest.mark.parametrize(("s", "res"), [
    ("10 20 30 0 0", 30),
    ("10 20 30 0 1", 20),
    ("10 20 30 0 2", 10),
    ("10 20 30 1 2 xchg 0 1", 10),
])
def test_xchg(s, res):
    assert run_errcode_test(f"{s} xchg") == res
def test_emit():
    assert run_stdout_test(f"49 48 emit emit") == "01"
def test_do():
    assert run_errcode_test(f"10 [ drop 1 ] do") == 1
def test_invalid_src():
    with pytest.raises(Exception) as e_info:
        run_errcode_test("", raw=f": main [  [  ]   ")
    assert "end-of-code-block expected" in str(e_info)
@pytest.mark.parametrize("num",[0, 10, 255, 256, 65534])
def test_emitxx(num):
    expect = num & 0xFF
    assert run_stdout_test(f"{num} emitXX") == f"{expect:02X}"
@pytest.mark.parametrize("num",[0, 10, 255, 256, 65534, 0x1234, 0xF1234, 2**64-1, 2**64-10])
def test_emitxxxx(num):
    expect = num & 0xFFFF
    assert run_stdout_test(f"{num} emitXXXX") == f"{expect:04X}"
@pytest.mark.parametrize("num",[0, 10, 255, 256, 65534, 0x1234, 0xF1234, 0x12345678,0x80706050,2**64-1, 2**64-10])
def test_emitxxxxxxxx(num):
    expect = num & 0xFFFFFFFF
    assert run_stdout_test(f"{num} emitXXXXXXXX") == f"{expect:08X}"
def test_incr():
    assert run_stdout_test(f"11 1+ emitXX") == f"0C"
def test_indecr():
    assert run_stdout_test(f"11 1- emitXX") == f"0A"
def test_1shr():
    assert run_stdout_test(f"11 1shr emitXX") == f"05"
def test_x8():
    assert run_stdout_test(f"127 emitX8") == f"7F"
def test_x16():
    assert run_stdout_test(f"32769 emitX16") == f"8001"
def test_x32():
    assert run_stdout_test(f"268435466 emitX32") == f"1000000A"
def test_x64():
    assert run_stdout_test(f"1162849439785405935 emitX64") == f"1023456789ABCDEF"
def test_x64_2():
    assert run_stdout_test(f"17870283323409323519 emitX64") == f"F8000000776655FF"
def test_x64_3():
    assert run_stdout_test("256 emitX64") == f"0000000000000100"
def test_add():
    assert run_errcode_test("10 12 +") == 22
def test_sub():
    assert run_errcode_test("33 3 -") == 30
def test_mul():
    assert run_errcode_test("11 3 *") == 33
def test_dump_stack_n():
    stdout = run_stdout_test("10 20 30 3 dump-stack-n")
    assert stdout.find(':') == 16
    assert stdout.rfind(':') == 16
    assert stdout[17:18] == ' '
    assert stdout[18:] == "000000000000000A 0000000000000014 000000000000001E --TOP\n"
    assert all(x in "0123456789ABCDEF" for x in stdout[:16])
def test_dump_stack_x2():
    stdout = run_stdout_test("5 10 2 dump-stack-n 2 dump-stack-n").strip()
    lines = stdout.split('\n')
    assert len(lines) == 2
    assert lines[0] == lines[1], "stack dumping should not change anything in the stack"

@pytest.mark.parametrize("num",[0, 10, 255, 256, 65534, 0x1234, 0xF1234, 0x12345678,0x80706050,2**32-1, 2**32,2**40,2**64-1, 2**64-10])
def test_n_to_strlen(num):
    assert run_stdout_test(f"{num} n>s$ type") == str(num)
def test_cr():
    assert run_stdout_test(f"cr") == "\n"

#
# ENCODING test
#
@pytest.mark.parametrize("p",[('t', '\t'), ('n', '\n'), ('r', '\r')])
def test_char_enc_esc(p):
    txt, val = p
    assert run_errcode_test(f"'\\{txt}' {ord(val)} =") == 1
@pytest.mark.parametrize("n", [0, 2, 16, 127, 128, 255])
def test_char_enc_hex(n):
    assert run_errcode_test(f"'\\x{n:02x}' {n} =") == 1

def test_bstrlen():
    assert run_errcode_test('"\\x10\\t\\"cd" $bstrlen') == 5


#
# STD-TEXT module tests
#
@pytest.mark.parametrize("num",LR32 + [XXX, YYY])
def test_is_digit_0(num):
    assert run_errcode_test(f"{num} is-digit?") == 0
@pytest.mark.parametrize("num", LR10)
def test_is_digit_1(num):
    assert run_errcode_test(f"'{num}' is-digit?") != 0
@pytest.mark.parametrize("ch", "abcd-~12345[]/\x7f")
def test_is_wspace_0_p1(ch):
    assert run_errcode_test(f"'{ch}' is-white-space?") == 0
@pytest.mark.parametrize("num", [XXX, YYY, 0x120])
def test_is_wspace_0_p2(num):
    assert run_errcode_test(f"{num} is-white-space?") == 0
@pytest.mark.parametrize("ch", " \n\r\t")
def test_is_wspace_1(ch):
    assert run_errcode_test(f"{ord(ch)} is-white-space?") == 1
