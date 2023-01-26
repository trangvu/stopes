#!/bin/bash
#SBATCH --job-name=trang-job
#SBATCH --account=da33
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

src=$1
tgt=eng

DATA_DIR=/scratch/ry10/jinming/oscar/split-oscar
OUT_DIR=/scratch/ry10/jinming/oscar/mining-outputs
TMP_DIR=/scratch/ry10/jinming/oscar/tmp
module load anaconda
source activate mine

mkdir -p $OUT_DIR
mkdir -p $TMP_DIR

python -m stopes.pipelines.bitext.global_mining_pipeline src_lang=$src tgt_lang=$tgt data_dir=$DATA_DIR tmp_dir=$TMP_DIR +lwll=m3_cpu output_dir=$OUT_DIR embed_text=laser3
