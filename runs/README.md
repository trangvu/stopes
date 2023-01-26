# Mining log
## Preprocess
### Data split
- Data is splitted to 5M shards
- List of languages to split: tha, swe, spa, slk, por, nld, eng, bul, ind
- Keep-as-is languages: 
- Empty/missing: swa, sqi, bos, arg

TODO: get some African language from WMT22 mining task
```bash
SCRIPT_DIR=/scratch/ry10/oscar/scripts
l=swe
sbatch --job-name split-$l split_data.sh $l
```

### Clean data
For the language that we don't have to split to smaller shards
```bash
SCRIPT_DIR=/scratch/ry10/oscar/scripts
cd $SCRIPT_DIR
./clean_data.sh $l
```