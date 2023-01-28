# Guideline
- Exp log: https://docs.google.com/spreadsheets/d/1XcbNB7EVFVyRTVYY-HRMljHhRzrVg7WlX7b4c671Ywc/edit?usp=sharing
- Pick a language and put your name on member column
- Check data quality of source language data. Some languages, e.g. ara, have very bad quality, noisy sentence with a mix of mainly English. If the data is noisy, highligh it with red color. We will need to redownload or reprocess data for that language.
  - Check the data with this command
```shell
    xzcat ara.xz | head -n 100
    xzcat ara.xz | tail -n 100
```

- Pick a group of English shards to work on. Ensure that the English shards you work on is not overlapped with others. Otherwise, we may submit multiple jobs to process, index for the same shards and lead to data conflict/pollution. I suggest to work with 1-5 English shards at a time. Put a note on that colum so that other people will avoid using that English group until you finished.

- Running scripts:
  - On fitcluster: in `runs/fitcluster`
    - For fitcluster, change `MAIN_CONF` in `mine_shard.sh` to `fitcluster` or `fitcluster_A100` to switch between default and A100 partition.
  - On m3: in `runs/m3`
  - Change the email address in the script if you need to. Either create your own git branch or local commit so that later you can easily rebase any updates in main branch.
  - Create/update shard_langs config with English shards you want to work on in `stopes/pipelines/bitext/conf/lwll/shard_langs`. For example, you create a `test_shard.yaml` file in that folder with following content to work with eng200, eng201, eng200 shards
  ```yaml
  # @package _global_
  sharded_langs:
    eng:
      - eng200
      - eng201
      - eng202
  ```
  - Ensure the file to start with `# @package _global_`
  - Submit job with following command:
  ```shell
  src=ara
  shard_config=test_shard
  sbatch --job-name=$src-$shard_config mine_shard.sh $src $shard_config
  ```
- Checking results:
  - How to check the actual configuration that the model use? In the output, you should observe something like
```
[2023-01-27 00:20:32,469][global_mining][INFO] - working dir: /fs03/ry10/oscar/scripts/outputs/2023-01-27/00-20-32
```
  - Check the file `config_logs/global_mining.yaml` for the all configurations. If there is any config you want to change, the easiest way is to copy that config to your config yaml file and modify it with your desired value.

  - Execution output structure
    - config_logs: all config files for each step
    - executor_logs: you can check slurm submission script, output and error log for each job
  
  - Output: `$OUT_DIR` in `mine_shard`
    - embed.V32m: tokenized data with moses and laser embedding
    - index.V32m: faiss index
    - mine.V32m: mine result
      - For each shard of src and tgt, there is a mining result file with format `{src}-{tgt}.TH-{min_threshold}TH-{max_threshold}.bitext.TH-{min_threshold}TH-{max_threshold}.bitext.tsv.gz`
      - A final file which merges results from all shard: `{src}_{tgt}_bitext.gz`. Please note that if you run mining for the same pairs in multiple runs with different shards, this file will be overrided. So please rename and copy the result to another folder.
      - Each file is a tsv file with 3 colums: `<distance score> <src> <tgt>` 
- Adjust the requested resource in config file
  - Each step corresponds to a stopes_module and comes with a requirement specifying the resource requested for job in slurm. Common setting is:
```shell
requirements:
  nodes: 1
  tasks_per_node: 1
  gpus_per_node: 0
  cpus_per_task: 4
  timeout_min: 2880 # running time
  mem_per_cpu: 15000
```
# Mining Process
## Installation notes
- faiss-gpu needs to be installed with conda to be able to run on A100 GPU
```shell
conda install -c pytorch faiss-gpu
#or
conda install -c conda-forge faiss-gpu
```
## Preprocess
### Data split
- TODO: Should we shuffle the data? The clean data seem to be ordered by similarity.
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