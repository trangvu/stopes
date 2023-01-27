#!/bin/bash

### Split data

for idx in `seq 200 299`; do
  echo "process "$idx
  wc -l eng$idx > eng$idx.nl
  xz eng$idx
done

l=eng
for idx in `seq -f%03g 200 221`; do
  echo 5000000 > ${l}${idx}.nl
done

l=eng
for idx in `seq -f%03g 50 221`; do
  mv ${l}${idx}.nl ${l}${idx}.tmp
  cut -f 1 -d' '  ${l}${idx}.tmp > ${l}${idx}.nl
  rm -f ${l}${idx}.tmp
done

kam
fuv
l=kam && mv ${l}.nl ${l}.tmp && cut -f 1 -d' '  ${l}.tmp > ${l}.nl && rm -f ${l}.tmp
### Submit shard
src=amh
shard=eng000_009
sbatch --job-name=$src-$shard mine_shard.sh $src $shard

src=nld
shard=eng010_019
sbatch --job-name=$src-$shard mine_shard.sh $src $shard

src=bul
shard=eng020_029
sbatch --job-name=$src-$shard mine_shard.sh $src $shard

src=por
shard=eng030_039
sbatch --job-name=$src-$shard mine_shard.sh $src $shard

src=swe
shard=eng040_049
sbatch --job-name=$src-$shard mine_shard.sh $src $shard


################## Fit cluster ################
ROOT_DIR=/nfsdata/data/lwll/nllb
DATA_DIR=$ROOT_DIR/split-oscar
OUT_DIR=$ROOT_DIR/mining-outputs
TMP_DIR=$ROOT_DIR/tmp
src=hin
tgt=eng
python -m stopes.pipelines.bitext.global_mining_pipeline src_lang=$src tgt_lang=$tgt data_dir=$DATA_DIR tmp_dir=$TMP_DIR +trang_test=fitcluster output_dir=$OUT_DIR embed_text=laser3

xzcat /nfsdata/data/lwll/nllb/split-oscar/hin.xz | perl /nfsdata/data/lwll/nllb/stopes/stopes/modules/preprocess/moses/scripts/tokenizer/remove-non-printing-char.perl | perl /nfsdata/data/lwll/nllb/stopes/stopes/modules/preprocess/moses/scripts/tokenizer/normalize-punctuation.perl -l hi | perl /nfsdata/data/lwll/nllb/stopes/stopes/modules/preprocess/moses/scripts/tokenizer/deescape-special-chars.perl | perl /nfsdata/data/lwll/nllb/stopes/stopes/modules/preprocess/moses/scripts/tokenizer/lowercase.perl > /nfsdata/data/lwll/nllb/mining-outputs/embed.V32m/moses_preprocess/moses.000.hin

src=tat
shard=eng100_105
sbatch --job-name=$src-$shard mine_shard.sh $src $shard
