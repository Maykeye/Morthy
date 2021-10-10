set -e
python3 ./morth.py
nasm -felf64 fizzbuzz.asm
ld fizzbuzz.o -ofizzbuzz
set +e
./fizzbuzz
echo $?
