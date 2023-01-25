#!/bin/bash

module load anaconda/anaconda3
module load cuda/cuda-11.1.0

export LD_LIBRARY_PATH=/nfsdata/data/lwll/nllb/env/lib/python3.10/site-packages/nvidia/cublas/lib:$LD_LIBRARY_PATH

WRK_DIR=/scratch/ft49/trang/nllb
conda activate $WRK_DIR/env
DATA_DIR=$WRK_DIR/data
TMP_DIR=$WRK_DIR/tmp
OUT_DIR=$WRK_DIR/outputs
src=amh
tgt=ara
python -m stopes.pipelines.bitext.global_mining_pipeline src_lang=$src tgt_lang=$tgt data_dir=$DATA_DIR tmp_dir=$TMP_DIR +lwll=local output_dir=$OUT_DIR embed_text=laser3