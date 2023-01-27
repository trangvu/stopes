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
MAIN_CONF=m3
DATA_DIR=/scratch/ry10/oscar/split-oscar
OUT_DIR=/scratch/ry10/oscar/mining-outputs
TMP_DIR=/scratch/ry10/oscar/tmp
module load cuda/11.3
module load python/3.8.5-gcc8-static
ENV_DIR=/scratch/da33/jinming/nllb/env
source $ENV_DIR/bin/activate
export LD_LIBRARY_PATH=/fs03/da33/jinming/nllb/env/lib/python3.8/site-packages/nvidia/cublas/lib:$LD_LIBRARY_PATH

mkdir -p $OUT_DIR
mkdir -p $TMP_DIR

python -m stopes.pipelines.bitext.global_mining_pipeline src_lang=$src tgt_lang=$tgt data_dir=$DATA_DIR tmp_dir=$TMP_DIR +lwll=$MAIN_CONF output_dir=$OUT_DIR embed_text=laser3
