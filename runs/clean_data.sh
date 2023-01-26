#!/bin/bash

l=$1
DATA_DIR=/scratch/ry10/oscar/split-oscar
OUT_DIR=/scratch/ry10/oscar/split-oscar
xzcat $DATA_DIR/$l.xz | cut -d$'\t' -f 6 > "${OUT_DIR}/${l}"
rm -f $DATA_DIR/$l.xz
xz "${OUT_DIR}/${l}"