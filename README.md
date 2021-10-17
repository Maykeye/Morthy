# Verbs:

## Stack operations
* `xchg` (xb.. xa.. x2 x1 x0 a b -- xa.. xb.. x2 x1 x0) <br>
    Swaps arbitrary cells

## Control flow

* `do`  (code -- XXX) <br>
 Executes code block on the stack (main use case is to start loops do-loops)

## Debug
* `sentinel!` ( -- S) <br>
    Assume that next push to the stack happens to address at `N`,
    sentinel! puts integer `(C+N)` to stack,
    where C is implementation defined.

    It's needed as if stack sits around 0x10, random data 0x10
    can be mistaked for sentinel later

* `sentinel@` (S -- ) <br>
    Assume that next pop happens at address `N`,
    the verb will pops the value and check if it's equal to `C+N`
    if it is, continues as normal.
    Otherwise implementation-defined crash happens

* `stack-pointer` ( -- sp ) <br>
    Pushes the address of top of stack before the push itself. I.e.
    If we have `..x y z` on stack with `z` on top, then `stack-pointer` will push the address of `z`.

* `dump-stack-n` ( n -- ) <br>
    Pops n, then print N element on top of the stack (excluding N at this point)
    in implementation-defined way




## Relational operation
In all of these operation the result is either 0(false) or 1(true).
All of them have the form of (a b -- ?)

* `=`, `!=` <br>
    Equality, inequality

* `<`, `>` <br>
    Signed comparison

## Arithmethic


* `+` `*` `-` (a b -- n) <br>
    In all of these operation the result is 64 bit number(s). In case of overflow/underflow, result must wrap.

## Binary operations
* `shr` (a n -- a>>n) <br>
    Pops two values (`n` then `a`), shifts `a` right by `n` bits,
    leaving last bit zero. Then the result is pushed to the stack.

## I/O and conversion
* `hex-digit` (n -- ch) <br>
    Takes last 4 bits of the number and converts them
    to human-readable character represention

* `n>s$` (n -- buf len) <br>
    Using the same buffer for each call, converts number to
    string in base 10.
    Returns string buffer and length of the string.
    Return form is suitable for `type`ing.

* `emit` (b -- ) <br>
    Emit a single character

* `cr` ( -- )
    Emit a new line

* `type` (buf len -- ) <br>
    Emits characters from the buffer.

* `emitXX`, `emitX8` (n -- ) <br>
    Pops a value and prints its least-significant byte in human-readable form. Byte is always printed using two characters, i.e. leading zero are not truncated.

* `emitXXXX`, `emitX16` (n -- ) <br>
    Pops a value and prints its least-significant 2-byte word in human-readable form. Word is always printed using four characters, i.e. leading zero are not truncated.

* `emitXXXXXXXX`, `emitX32` (n -- ) <br>
    Pops a value and prints its least-significant 4-byte word in human-readable form. Word is always printed using four characters, i.e. leading zero are not truncated.

* `emitXXXXXXXXXXXXXXXX`, `emitX64` (n -- ) <br>
    Pops a value and prints its least-significant 8-byte word in human-readable form. Word is always printed using sixteen characters, i.e. leading zero are not truncated.

## Shorthands

* `1+` increase top of the stack by 1
* `1-` decrease top of the stack by 1
* `1shr` shift top of the stack by 1 bit.

##
System:

* `exit` (n -- noreturn) <br>
    Terminates the program, returning n as the error code in implementation-defined way.
    UB: If stack is not balanced.

