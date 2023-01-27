# Mining log
## Preprocess
### Data split
- Data is splitted to 5M shards
- List of languages to split: tha, swe, spa, slk, por, nld, eng, bul, ind, swh
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

## Data and code structure
### M3
```shell
ROOT_DIR=/scratch/ry10/oscar
DATA_DIR=$ROOT_DIR/split-oscar
OUT_DIR=$ROOT_DIR/mining-outputs
TMP_DIR=$ROOT_DIR/tmp
```
### Fitcluster
```shell
ROOT_DIR=/nfsdata/data/lwll/nllb
DATA_DIR=$ROOT_DIR/split-oscar
OUT_DIR=$ROOT_DIR/mining-outputs
TMP_DIR=$ROOT_DIR/tmp
```

## Mining
Mining scripts can be found in `runs/mine.sh` and `runs/mine_shard.sh`. The main difference is that `mine_shard` has an option to customize the engligh subset.

Script explanation:
- DATA_DIR: path to folder language data and laser models. Each language has 2 files: compressed data `ara.xz` and line number file `ara.nl`. For language with multiple shards, we use the sublanguage instead, i.e. `eng001.xz` and `eng001.nl`
- OUT_DIR: embedding, index and mined output
- TMP_DIR: cached dir

- The main config file can be found in `stopes/pipelines/bitext/conf/lwll`. We have several config options
  - local: run in local mode, i.e. sequential
  - m3_cpu: run on m3 with cpu only
  - m3: run on m3 with gpu

- How to add additional config to the default config? You can create additional folders and config yaml file and add to the command with `+lwll/shard_langs=eng000_009`. The config in `eng000_009.yaml` will be appended or overried the main config `+lwll=m3`. Note that the order matters. Each new config file should start with `# @package _global_`. You can only add 1 config file per config folder.

The folder `stopes/pipelines/bitext/conf` contains sample config for multiple steps in global_mining. Feel free to have a look. My suggestion is to start with `global_mining.yaml`.

```shell
DATA_DIR=/scratch/ry10/oscar/split-oscar
OUT_DIR=/scratch/ry10/oscar/mining-outputs
TMP_DIR=/scratch/ry10/oscar/tmp
MAIN_CONF=m3
python -m stopes.pipelines.bitext.global_mining_pipeline src_lang=$src tgt_lang=$tgt data_dir=$DATA_DIR tmp_dir=$TMP_DIR +lwll=$MAIN_CONF +lwll/shard_langs=$SHARD_NAME output_dir=$OUT_DIR embed_text=laser3
```
### Model output logs
How to check the actual configuration that the model use? In the output, you should observe something like
```
[2023-01-27 00:20:32,469][global_mining][INFO] - working dir: /fs03/ry10/oscar/scripts/outputs/2023-01-27/00-20-32
```
Check the file `config_logs/global_mining.yaml` for the all configurations. If there is any config you want to change, the easiest way is to copy that config to your config yaml file and modify it with your desired value.

Execution output structure
- config_logs: all config files for each step
- executor_logs: you can check slurm submission script, output and error log for each job

### Adjust the requested resource
Each step corresponds to a stopes_module and comes with a requirement specifying the resource requested for job in slurm. Common setting is:
```shell
requirements:
  nodes: 1
  tasks_per_node: 1
  gpus_per_node: 0
  cpus_per_task: 4
  timeout_min: 2880 # running time
  mem_per_cpu: 15000
```