#!/bin/bash
#SBATCH --job-name=trang-job
#SBATCH --ntasks=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=10000
#SBATCH --time=7-00:00:00
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=vuth0001@student.monash.edu
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err

if [ "$#" -lt 2 ]; then
   echo "Mine using a shard_langs config file"
   echo "Usage: $0 <src> <shard_name>"
   exit 1
fi

src=$1
tgt=eng
SHARD_NAME=$2
MAIN_CONF=fitcluster_A100

ROOT_DIR=/nfsdata/data/lwll/nllb
DATA_DIR=$ROOT_DIR/split-oscar
OUT_DIR=$ROOT_DIR/mining-outputs
TMP_DIR=$ROOT_DIR/tmp

module load anaconda/anaconda3
source activate $ROOT_DIR/env
export LD_LIBRARY_PATH=/nfsdata/data/lwll/nllb/env/lib/python3.10/site-packages/nvidia/cublas/lib:$LD_LIBRARY_PATH


python -m stopes.pipelines.bitext.global_mining_pipeline src_lang=$src tgt_lang=$tgt data_dir=$DATA_DIR tmp_dir=$TMP_DIR +lwll=$MAIN_CONF +lwll/shard_langs=$SHARD_NAME output_dir=$OUT_DIR embed_text=laser3