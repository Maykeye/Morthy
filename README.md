# Verbs:

## Debug
* `sentinel!` ( -- S)
    Assume that next push to the stack happens to address at `N`,
    sentinel! puts integer `(C+N)` to stack,
    where C is implementation defined.

    It's needed as if stack sits around 0x10, random data 0x10
    can be mistaked for sentinel later

* `sentinel@` (S -- )
    Assume that next pop happens at address `N`,
    the verb will pops the value and check if it's equal to `C+N`
    if it is, continues as normal.
    Otherwise implementation-defined crash happens

## Relational operation
In all of these operation the result is either 0(false) or 1(true).
All of them have the form of (a b -- ?)

* `=`, `!=`

    Equality, inequality

* `<`, `>`

    Signed comparison

## Binary operations

* `shr` (a n -- a>>n)

    Pops two values (`n` then `a`), shifts `a` right by `n` bits,
    leaving last bit zero. Then the result is pushed to the stack.

## I/O
* `hex-digit` (n -- ch)

    Takes last 4 bits of the number and converts them
    to human-readable character represention

* `emitXX`, `emitX8` (n -- )

    Pops a value and prints its least-significant byte in human-readable form. Byte is always printed using two characters, i.e. leading zero are not truncated.

* `emitXXXX`, `emitX16` (n -- )

    Pops a value and prints its least-significant 2-byte word in human-readable form. Word is always printed using four characters, i.e. leading zero are not truncated.

* `emitXXXXXXXX`, `emitX32` (n -- )

    Pops a value and prints its least-significant 4-byte word in human-readable form. Word is always printed using four characters, i.e. leading zero are not truncated.

* `emitXXXXXXXXXXXXXXXX`, `emitX64` (n -- )

    Pops a value and prints its least-significant 8-byte word in human-readable form. Word is always printed using sixteen characters, i.e. leading zero are not truncated.

## Shorthands

* `1+` increase top of the stack by 1
* `1-` decrease top of the stack by 1
* `1shr` shift top of the stack by 1 bit.

##
System:

* `exit` (n -- noreturn) exit
    terminates the program, returning n as the error code.
    UB: If stack is not balanced.

