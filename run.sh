set -e
FILENAME=${1:-fizzbuzz.morth}
BASE=`basename "${FILENAME}" .morth`
python3 ./morth.py "$FILENAME"
nasm -felf64 -g -F dwarf out/${BASE}.asm
ld out/${BASE}.o -oout/${BASE}
set +e
./out/${BASE}
echo -e "\n---RESULT:$?"

