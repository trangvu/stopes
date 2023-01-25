#!/bin/bash

module load python/3.8.5-gcc8-static
module load cuda/10.1

WRK_DIR=/nfsdata/data/lwll/nllb
conda activate $WRK_DIR/env
DATA_DIR=/nfsdata/data/lwll/nllb/stopes/demo/mining
TMP_DIR=/nfsdata/data/lwll/nllb/tmp
OUT_DIR=/nfsdata/data/lwll/nllb/outputs
src=fuv
tgt=zul
python -m stopes.pipelines.bitext.global_mining_pipeline src_lang=fuv tgt_lang=zul data_dir=$DATA_DIR tmp_dir=$TMP_DIR +lwll=local output_dir=$OUT_DIR embed_text=laser3