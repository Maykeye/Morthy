import morth
import pytest

def run_errcode_test(src):
    filename = "out/_unittest.morth"
    with open(filename, "w") as f:
        f.write(src)
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
    assert run_errcode_test(f": main [ {num} exit ]") == num & 0xff
def test_nested_comments():
    assert run_errcode_test(f": (foo ( b)) main(poo) [(1)10(2(3))exit ] ") == 10
def test_func_call():
    assert run_errcode_test(
        ": run [ run1 23 + ] \n"
        ": run1 [ run2 100 run2 ] \n"
        ": run2 [ ] \n"
        ": main [ run exit ]"
    ) == 123


@pytest.mark.parametrize("num",[0,1,2,3,4,5,6,7,8,9])
def test_hex_digit_digits(num):
    assert run_errcode_test(f": main [ {num} hex-digit exit ] ") == 48+num

@pytest.mark.parametrize("num",[10,11,12,13,14,15])
def test_hex_digit_hex(num):
    assert run_errcode_test(f": main [ {num} hex-digit exit ] ") == 55+num
# TODO: wrap up

@pytest.mark.parametrize("s",["", "1 drop", "[ 1 ] drop", "3 swap nip"])
def test_sentinel_balanced(s):
    assert run_errcode_test(f": main [ sentinel! {s} sentinel@ 10 exit ] ") == 10

@pytest.mark.parametrize("s",["drop", "3 swap"])
def test_sentinel_unbalanced(s):
    assert run_errcode_test(f": main [ sentinel! {s} sentinel@ 11 exit ] ") == 255

@pytest.mark.parametrize(("s", "res"),
   [("1 2 <", 1), ("2 1 <", 0),
    ("2 1 >", 1), ("1 2 >", 0),
    ("2 1 =", 0), ("1 1 =", 1),
    ("2 1 !=", 1), ("1 1 !=", 0)
])
def test_relop(s, res):
    assert run_errcode_test(f": main [ {s} exit ] ") == res

def test_emit():
    assert run_stdout_test(f"49 48 emit emit") == "01"

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