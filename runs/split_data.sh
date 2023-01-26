#!/bin/bash
#SBATCH --job-name=trang-job
#SBATCH --account=ft49
#SBATCH --ntasks=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=5000
#SBATCH --partition=comp
#SBATCH --time=7-00:00:00
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=vuth0001@student.monash.edu
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err

l=$1
shard_size=5000000
DATA_DIR=/scratch/ry10/oscar/clean-oscar-ln
OUT_DIR=/scratch/ry10/oscar/split-oscar
mkdir -p $OUT_DIR
xzcat $DATA_DIR/$l.xz | cut -d$'\t' -f 6 | split -d -l $shard_size -a 3 - "${OUT_DIR}/${l}"

# Count line number
cd $OUT_DIR
for file in ./${l}*; do
  file_name=`basename $file`
  wc -l $file_name > ${file_name}.nl
  xz $file_name
done