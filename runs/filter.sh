#!/bin/bash
#SBATCH --job-name=trang-job
#SBATCH --account=da33
#SBATCH --ntasks=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=25000
#SBATCH --partition=comp
#SBATCH --time=7-00:00:00
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=vuth0001@student.monash.edu
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err

src=$1
ifile=$2
pct=$3
tgt=eng

ipath=/scratch/da33/lwll/mine_data/bitext
opath=/scratch/da33/lwll/mine_data/filtered
ofile=filter.pct${pct}.${ifile}

module load cuda/11.3
module load python/3.8.5-gcc8-static
ENV_DIR=/scratch/da33/jinming/nllb/env
source $ENV_DIR/bin/activate

mkdir -p $OUT_DIR
filter_minlen=5
filter_maxlen=300
ov_rate_max=0.35
ov_mean_ratio=1.0
filter_order=6

FILTER=/scratch/da33/jinming/nllb/trang-stopes/stopes/pipelines/filtering/filter_by_rules.py
python ${FILTER} \
    --ipath ${ipath} \
    --ifile ${ifile} \
    --opath ${opath} \
    --ofile ${ofile} \
    --percentile ${pct} \
    --filter_minlen ${filter_minlen} \
    --filter_maxlen ${filter_maxlen} \
    --filter_overlap_rate_max ${ov_rate_max} \
    --filter_overlap_mean_ratio ${ov_mean_ratio} \
    --filter_same \
    --filter_order ${filter_order} \
    --log_examples 50
