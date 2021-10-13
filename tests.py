import morth
import pytest

def run_errcode_test(src):
    filename = "out/_unittest.morth"
    with open(filename, "w") as f:
        f.write(src)
    (res, out, err) = morth.run(filename, "nasm-ld-pipe")
    return res
    
@pytest.mark.parametrize("num",[0,1,2,10,100,1000,12345,102030,1122444, 2**31, 2**63,2**64-1,0x10203040AABBCCDD])
def test_exit0(num):
    assert run_errcode_test(f": main [ {num} exit ]") == num & 0xff

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
