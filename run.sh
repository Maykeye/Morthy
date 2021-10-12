set -e
FILENAME=${1:-fizzbuzz.morth}
BASE=`basename "${FILENAME}" .morth`
python3 ./morth.py "$FILENAME"
nasm -felf64 out/${BASE}.asm
ld out/${BASE}.o -oout/${BASE}
set +e
./out/${BASE}
echo $?
