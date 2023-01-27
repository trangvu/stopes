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