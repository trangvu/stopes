# import glob
# from itertools import filterfalse
# import os
# import sys
# import faiss
# import argparse
# import tempfile
import numpy as np
import torch
import gzip
import re
import argparse
import os

# from langdetect import detect
# from polyglot.detect import Detector
# from polyglot.detect.base import logger as polyglot_logger

# polyglot_logger.setLevel("ERROR")


# except ImportError as e:
#     print('langdetect and other detector not installed, run the following:')
#     print('bash install_mass_filter_noisy_prerequisite.sh or run the following:')
#     print("""
# export cur=$PWD
# cd ..
# git clone http://github.com/abosamoor/pycld2.git
# cd pycld2
# apt-get update && apt-get install -y apt-transport-https && apt-get install  -y  libicu-dev && ./setup.py install && pip install pyicu polyglot langdetect
# cd $cur
#     """)


def detect_exist_url(text):
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    url1 = re.findall('http[s]?//(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    url2 = re.findall('http[s]? : / / (?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    url3 = re.findall('http[s]? / / (?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    return len(urls) > 0 or len(url1) > 0 or len(url2) > 0 or len(url3) > 0


# def verify_lang(text, lang):
#     try:
#         for i, l in enumerate(Detector(text, quiet=True).languages):
#             if l.code == lang and i == 0:
#                 return True
#         if detect(text) == lang:
#             return True
#         return False
#     except:
#         return False

def process_line(byte_string):
    def clean(line):
        return line.replace("\"\"\"", "").replace("\"", "")
    line_lst = byte_string.decode("utf-8").strip("\n\r").split("\t")
    line_lst = [clean(item) for item in line_lst]

    return float(line_lst[0]), line_lst[1], line_lst[2]


def load_data(args, **kwargs):
    """

    :param args:
    :param kwargs:
    :return:
    """
    _src_txts = []
    _tgt_txts = []
    _scores = []
    with gzip.open(os.path.join(args.ipath, args.ifile), "rb") as fin:
        for i, line in enumerate(fin):
            # breakpoint()
            # print(f"# i: {i}")
            #if i == 100:
             #   break
            score, src_txt, tgt_txt = process_line(line)
            _src_txts.append(src_txt)
            _tgt_txts.append(tgt_txt)
            _scores.append(np.array(score))
    _index = [i for i in range(len(_src_txts))]
    assert len(_src_txts) == len(_tgt_txts) == len(_index)
    index = {"src_idx": _index,
             "tgt_idx": _index,
             "src_texts": _src_txts,
             "tgt_texts": _tgt_txts,
             "scores": _scores}
    return index


def rm_duplicates(args, index):
    print(f'Start removing duplicates...')
    size = len(index['src_texts'])
    src_idx = []
    tgt_idx = []
    scores = []
    src_texts = []
    tgt_texts = []
    included = set()
    for i in range(size):
        if i % 100000 == 0:
            print(f'rm duplicates: {i}')
        pair = f"{index['src_texts'][i]}\t{index['tgt_texts'][i]}"
        if pair not in included:
            included.add(pair)
            src_idx.append(index['src_idx'][i])
            tgt_idx.append(index['tgt_idx'][i])
            src_texts.append(index['src_texts'][i])
            tgt_texts.append(index['tgt_texts'][i])
            scores.append(index['scores'][i])
    print(
        f'Finish rm duplicates, found {len(index["src_idx"]) - len(src_idx)} dups / {len(index["src_idx"])}, remain {len(src_idx)}')
    index['src_idx'] = np.array(src_idx)
    index['tgt_idx'] = np.array(tgt_idx)
    index['src_texts'] = src_texts
    index['tgt_texts'] = tgt_texts
    index['scores'] = np.array(scores)
    return index


def filter_same_srctgt(args, index):
    filter_same = args.filter_same
    if filter_same:
        print(f'Start filtering by filter_same')
        src_idx = []
        tgt_idx = []
        scores = []
        src_texts = []
        tgt_texts = []
        size = len(index['src_idx'])
        for idx in range(size):
            if index['src_texts'][idx] != index['tgt_texts'][idx]:
                src_idx.append(index['src_idx'][idx])
                tgt_idx.append(index['tgt_idx'][idx])
                src_texts.append(index['src_texts'][idx])
                tgt_texts.append(index['tgt_texts'][idx])
                scores.append(index['scores'][idx])
        print(
            f'Finish filtering by filter_same, found {len(index["src_idx"]) - len(src_idx)} rm / {len(index["src_idx"])}, remain {len(src_idx)}')
        index['src_idx'] = np.array(src_idx)
        index['tgt_idx'] = np.array(tgt_idx)
        index['src_texts'] = src_texts
        index['tgt_texts'] = tgt_texts
        index['scores'] = np.array(scores)
    return index



def filter_best_unique_pairs(args, index):
    # due to partitioning, given x_i -> there can be multiple y_j from partitions
    src_idx = []
    tgt_idx = []
    scores = []
    src_texts = []
    tgt_texts = []
    seen_src, seen_tgt = set(), set()
    # search forward
    print(f'Start filtering by filter_best_unique_pairs')
    #breakpoint()
    for idx in np.argsort(-index['scores']):
        src_i = index['src_idx'][idx]
        tgt_i = index['tgt_idx'][idx]
        if not src_i in seen_src and not tgt_i in seen_tgt:
            seen_src.add(src_i)
            seen_tgt.add(tgt_i)
            src_idx.append(index['src_idx'][idx])
            tgt_idx.append(index['tgt_idx'][idx])
            src_texts.append(index['src_texts'][idx])
            tgt_texts.append(index['tgt_texts'][idx])
            scores.append(index['scores'][idx])
    print(
        f'Finish filtering by filter_best_unique_pairs, found {len(index["src_idx"]) - len(src_idx)} rm / {len(index["src_idx"])}, remain {len(src_idx)}')
    index['src_idx'] = np.array(src_idx)
    index['tgt_idx'] = np.array(tgt_idx)
    index['src_texts'] = src_texts
    index['tgt_texts'] = tgt_texts
    index['scores'] = np.array(scores)
    return index


def percentile_filter(args, index):
    percentile = args.percentile
    if percentile < 1.0:
        print(f'Start filtering by percentile {percentile}')
        truncated_size = int(percentile * len(index['src_idx']))
        if truncated_size == 0:
            raise ValueError(f'wrong values {truncated_size} / {len(index["src_idx"])}')
        indices = np.argsort(-index['scores'])[:truncated_size]
        src_idx = []
        tgt_idx = []
        scores = []
        src_texts = []
        tgt_texts = []
        for idx in indices:
            src_idx.append(index['src_idx'][idx])
            tgt_idx.append(index['tgt_idx'][idx])
            src_texts.append(index['src_texts'][idx])
            tgt_texts.append(index['tgt_texts'][idx])
            scores.append(index['scores'][idx])
        print(
            f'Finish filtering by percentile, found {len(index["src_idx"]) - len(src_idx)} dups / {len(index["src_idx"])}, remain {len(src_idx)}')
        index['src_idx'] = np.array(src_idx)
        index['tgt_idx'] = np.array(tgt_idx)
        index['src_texts'] = src_texts
        index['tgt_texts'] = tgt_texts
        index['scores'] = np.array(scores)
    return index


def filter_by_minlen(args, index):
    filter_minlen = args.filter_minlen
    filter_maxlen = args.filter_maxlen
    if filter_minlen > 0:
        print(f'Start filter by filter_minlen: {filter_minlen}')
        src_idx = []
        tgt_idx = []
        scores = []
        src_texts = []
        tgt_texts = []
        size = len(index['src_idx'])
        for idx in range(size):
            # if filter_overlap_rate_max > overlap_rate(index['src_texts'][idx], index['tgt_texts'][idx]) > filter_overlap_rate:
            pair_len = min(len(index['src_texts'][idx]), len(index['tgt_texts'][idx]))
            if pair_len > filter_minlen:
                src_idx.append(index['src_idx'][idx])
                tgt_idx.append(index['tgt_idx'][idx])
                src_texts.append(index['src_texts'][idx])
                tgt_texts.append(index['tgt_texts'][idx])
                scores.append(index['scores'][idx])
        print(
            f'Finish filtering by filter_minlen, found {len(index["src_idx"]) - len(src_idx)} rm / {len(index["src_idx"])}, remain {len(src_idx)}')
        index['src_idx'] = np.array(src_idx)
        index['tgt_idx'] = np.array(tgt_idx)
        index['src_texts'] = src_texts
        index['tgt_texts'] = tgt_texts
        index['scores'] = np.array(scores)

    if filter_maxlen > 0:
        print(f'Start filter by filter_maxlen: {filter_minlen}')
        src_idx = []
        tgt_idx = []
        scores = []
        src_texts = []
        tgt_texts = []
        size = len(index['src_idx'])
        for idx in range(size):
            # if filter_overlap_rate_max > overlap_rate(index['src_texts'][idx], index['tgt_texts'][idx]) > filter_overlap_rate:
            pair_len = max(len(index['src_texts'][idx]), len(index['tgt_texts'][idx]))
            if pair_len < filter_maxlen:
                src_idx.append(index['src_idx'][idx])
                tgt_idx.append(index['tgt_idx'][idx])
                src_texts.append(index['src_texts'][idx])
                tgt_texts.append(index['tgt_texts'][idx])
                scores.append(index['scores'][idx])
        print(
            f'Finish filtering by filter_maxlen, found {len(index["src_idx"]) - len(src_idx)} rm / {len(index["src_idx"])}, remain {len(src_idx)}')
        index['src_idx'] = np.array(src_idx)
        index['tgt_idx'] = np.array(tgt_idx)
        index['src_texts'] = src_texts
        index['tgt_texts'] = tgt_texts
        index['scores'] = np.array(scores)

    return index


def filter_by_threshold(args, index):
    filter_threshold = args.filter_threshold
    if filter_threshold > 0:
        print(f'Start filter by filter_threshold: {filter_threshold}')
        src_idx = []
        tgt_idx = []
        scores = []
        src_texts = []
        tgt_texts = []
        size = len(index['src_idx'])
        for idx in range(size):
            # pair_len = min(len(index['src_texts'][idx]), len(index['tgt_texts'][idx]))
            if index['scores'][idx] > filter_threshold:
                src_idx.append(index['src_idx'][idx])
                tgt_idx.append(index['tgt_idx'][idx])
                src_texts.append(index['src_texts'][idx])
                tgt_texts.append(index['tgt_texts'][idx])
                scores.append(index['scores'][idx])
        print(
            f'Finish filtering by filter_threshold, found {len(index["src_idx"]) - len(src_idx)} rm / {len(index["src_idx"])}, remain {len(src_idx)}')
        index['src_idx'] = np.array(src_idx)
        index['tgt_idx'] = np.array(tgt_idx)
        index['src_texts'] = src_texts
        index['tgt_texts'] = tgt_texts
        index['scores'] = np.array(scores)
    return index


def overlap_rate(src, tgt):
    toks = list(src.split(" ")) + list(tgt.split(" "))
    unique_toks = set(toks)
    rate = (len(toks) - len(unique_toks)) / float(len(toks))
    # rate: 0 (nooverlap) -> 0.5 (exact match)
    return rate


def filter_by_overlap_rate(args, index):
    filter_overlap_rate = args.filter_overlap_rate
    filter_overlap_rate_max = args.filter_overlap_rate_max
    if filter_overlap_rate_max < 0:
        filter_overlap_rate_max = 1.0
    if filter_overlap_rate > 0 or filter_overlap_rate_max > 0:
        print(f'Start filter by overlap rate: {filter_overlap_rate} / max={filter_overlap_rate_max}')
        src_idx = []
        tgt_idx = []
        scores = []
        src_texts = []
        tgt_texts = []
        size = len(index['src_idx'])
        for idx in range(size):
            if filter_overlap_rate_max > overlap_rate(index['src_texts'][idx],
                                                      index['tgt_texts'][idx]) > filter_overlap_rate:
                src_idx.append(index['src_idx'][idx])
                tgt_idx.append(index['tgt_idx'][idx])
                src_texts.append(index['src_texts'][idx])
                tgt_texts.append(index['tgt_texts'][idx])
                scores.append(index['scores'][idx])
        print(
            f'Finish filtering by overlap rate, found {len(index["src_idx"]) - len(src_idx)} rm / {len(index["src_idx"])}, remain {len(src_idx)}')
        index['src_idx'] = np.array(src_idx)
        index['tgt_idx'] = np.array(tgt_idx)
        index['src_texts'] = src_texts
        index['tgt_texts'] = tgt_texts
        index['scores'] = np.array(scores)
    return index


def filter_by_overlap_rate_mean_ratio(args, index):
    filter_overlap_mean_ratio = args.filter_overlap_mean_ratio
    if filter_overlap_mean_ratio > 0:
        print(f'Start filter by overlap rate mean ratio (should be > 1): {filter_overlap_mean_ratio}')
        src_idx = []
        tgt_idx = []
        scores = []
        src_texts = []
        tgt_texts = []
        size = len(index['src_idx'])
        rates = []
        for idx in range(size):
            rates.append(overlap_rate(index['src_texts'][idx], index['tgt_texts'][idx]))
        mean_rate = float(np.array(rates).mean())
        print(f"Mean overlap rate: {mean_rate}")
        for idx in range(size):
            if rates[idx] / mean_rate > filter_overlap_mean_ratio:
                src_idx.append(index['src_idx'][idx])
                tgt_idx.append(index['tgt_idx'][idx])
                src_texts.append(index['src_texts'][idx])
                tgt_texts.append(index['tgt_texts'][idx])
                scores.append(index['scores'][idx])
        print(
            f'Finish filtering by overlap rate mean ratio, found {len(index["src_idx"]) - len(src_idx)} rm / {len(index["src_idx"])}, remain {len(src_idx)}')
        index['src_idx'] = np.array(src_idx)
        index['tgt_idx'] = np.array(tgt_idx)
        index['src_texts'] = src_texts
        index['tgt_texts'] = tgt_texts
        index['scores'] = np.array(scores)
    return index


spm_underscore = "▁"

def get_decode_fn(args):
    bpe = args.bpe
    print(f'bpe={bpe}')
    if bpe == 'bpe':
        decode_fn = lambda x: x.replace("@@ ", "")
    elif bpe == 'spm':
        decode_fn = lambda x: x.replace(" ", "").replace(spm_underscore, " ").strip()
    else:
        decode_fn = lambda x: x
    return decode_fn


def log_examples(args, index, src_texts, tgt_texts, n=10):
    print(f'Examples ============================')
    decode_fn = get_decode_fn(args)
    if len(src_texts) < n:
        print(f'WARNING, data size ({len(src_texts)}) < n={n}')
    for i in range(min(len(src_texts), n)):
        s = decode_fn(src_texts[i])
        t = decode_fn(tgt_texts[i])
        print(f'------[{i}]--- score {index["scores"][i]}\n\t {s}\n\t {t}')


def strip_line_start(line):
    return re.sub(r'^.[0-9!:.) \]]+', '', line)


def export(args, index):
    output = args.opath
    os.makedirs(output, exist_ok=True)
    src_texts = index.pop("src_texts")
    tgt_texts = index.pop("tgt_texts")
    log_examples(args, index, src_texts, tgt_texts, n=args.log_examples)
    with gzip.open(os.path.join(args.opath, args.ofile), "wb") as fout:
        for src, tgt in zip(src_texts, tgt_texts):
            line = "\t".join([strip_line_start(src), strip_line_start(tgt)]).encode()
            fout.write(line)
            fout.write("\n".encode())

def offline_bleu_filter(args):
    # FIXME: only support forward side right now
    src_lang = args.src_lang
    src_txt = args.src_txt
    tgt_lang = args.tgt_lang
    tgt_txt = args.tgt_txt
    offline_scores = args.offline_scores
    assert os.path.exists(offline_scores), f'{offline_scores} not found.'
    bleu_threshold = args.bleu_threshold
    offline_out = args.offline_out
    lang_tokens = [f'__{x}__' for x in [src_lang, tgt_lang]]
    rm_toks = args.rm_toks.split(",")
    if len(rm_toks) > 0:
        print(f'rm_toks: {rm_toks}')

    print(f'Load score: {offline_scores}')
    with open(offline_scores, 'r') as f:
        lines = f.read().splitlines()
        _scores = [[float(x) for x in l.split('\t')] for l in lines]
        bleu_scores = np.array([x[0] for x in _scores])
        scores = np.array([x[1] for x in _scores])
    print(f'Load src: : {src_txt}')
    with open(src_txt, 'r', encoding=args.encoding, errors='surrogateescape') as f:
        src_texts = f.read().splitlines()
    print(f'Load tgt: : {tgt_txt}')
    with open(tgt_txt, 'r', encoding=args.encoding, errors='surrogateescape') as f:
        tgt_texts = f.read().splitlines()
    index = {
        "scores": [],
        "bleu_scores": [],
        "src_texts": [],
        "tgt_texts": [],
    }
    ori_size = len(bleu_scores)
    assert len(_scores) == len(src_texts) == len(tgt_texts) == ori_size

    # print(f'Start filtering by offline umt bleu: {bleu_threshold=}')
    included = set()
    for idx in np.argsort(-scores):
        s = src_texts[idx]
        t = tgt_texts[idx]
        s = ' '.join(s.split(" ")[1:]) if any(s.startswith(tok) for tok in lang_tokens) else s
        t = ' '.join(t.split(" ")[1:]) if any(t.startswith(tok) for tok in lang_tokens) else t
        if len(rm_toks) > 0:
            for rmt in rm_toks:
                s = s.replace(rmt, "").strip()
                t = t.replace(rmt, "").strip()
        pair = f"{s}\t{t}"
        if bleu_scores[idx] >= bleu_threshold and (pair not in included):
            included.add(pair)
            index['scores'].append(scores[idx])
            index['bleu_scores'].append(bleu_scores[idx])
            index['src_texts'].append(s)
            index['tgt_texts'].append(t)
    for k in ['scores', 'bleu_scores']:
        index[k] = np.array(index[k])
    print(
        f'Finish filtering by offline umt bleu, found {len(src_texts) - len(index["src_texts"])} rm / {len(src_texts)}, remain {len(index["src_texts"])}')

    export(args, index)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ipath", type=str, default="../data")
    parser.add_argument('--ifile', type=str, default="spa000-eng201.TH-0.TH-0.5.bitext.TH-0.TH-0.5.bitext.tsv.gz")
    parser.add_argument("--opath", type=str, default="../outputs")
    parser.add_argument('--ofile', type=str, default="filter.spa000-eng201.TH-0.TH-0.5.bitext.TH-0.TH-0.5.bitext.tsv.gz")
    parser.add_argument('--encoding', default='utf-8', help='Character encoding for input/output')
    parser.add_argument('--filter_same', default=False, action='store_true')
    parser.add_argument('--percentile', type=float, default=1.0, help="Keep top x best ones")

    parser.add_argument('--filter_threshold', type=float, default=-1,
                        help="if > 0, keep if by score > ")
    parser.add_argument('--filter_minlen', type=int, default=-1,
                        help="if > 0, keep if min(len(src), len(tgt)) > ")
    parser.add_argument('--filter_maxlen', type=int, default=-1,
                        help="if > 0, keep if min(len(src), len(tgt)) > ")

    parser.add_argument('--filter_overlap_rate', type=float, default=-1,
                        help="if > 0, keep if overlap_rate >, good for overlapped lang, bad for distance langs")

    parser.add_argument('--filter_overlap_rate_max', type=float, default=-1,
                        help="if > 0, keep if overlap_rate <, good for overlapped lang, bad for distance langs")

    parser.add_argument('--filter_overlap_mean_ratio', type=float, default=-1,
                        help="if > 0, keep if overlap_rate / mean_overlap_rate > , good for overlapped lang, bad for distance langs")
    parser.add_argument('--detect_lang', default=False, action='store_true')
    parser.add_argument('--bpe', type=str, default="", help='bpe/spm/none')
    parser.add_argument('--log_examples', type=int, default=10, help='log examples')

    parser.add_argument('--filter_order', type=int, default=1, help='Filtering order, see below')

    # --offline-bleu
    parser.add_argument('--offline_bleu', default=False, action='store_true')
    parser.add_argument('--bleu_threshold', default=30, type=float)
    parser.add_argument('--offline_scores', default=None, type=str)
    parser.add_argument('--offline_out', default=None, type=str)
    parser.add_argument('--rm_toks', type=str)

    args = parser.parse_args()
    print(args)

    if args.offline_bleu:
        print(f'Offline BLEU filtering...')
        offline_bleu_filter(args)
        exit(0)

    # src_lang = args.src_lang
    # src_txt = args.src_txt
    # index_file = args.index
    # tgt_lang = args.tgt_lang
    # tgt_txt = args.tgt_txt

    index = load_data(args)

    print(f'Filter with order: {args.filter_order}')
    if args.filter_order == 1:
        # order 1
        # index = rm_duplicates(args, index)
        index = filter_same_srctgt(args, index)
        index = percentile_filter(args, index)
        index = filter_by_overlap_rate(args, index)
        index = filter_by_overlap_rate_mean_ratio(args, index)
        # index = filter_detect_lang(args, index)
    elif args.filter_order == 6:
        # order 5
        # index = rm_duplicates(args, index)
        index = filter_same_srctgt(args, index)
        index = filter_by_minlen(args, index)
        # index = filter_detect_lang(args, index)
        index = filter_by_threshold(args, index)

        index = filter_best_unique_pairs(args, index)
        index = filter_by_overlap_rate(args, index)
        index = filter_by_overlap_rate_mean_ratio(args, index)
        index = percentile_filter(args, index)
    else:
        raise ValueError(f'{args.filter_order} wrong.')

    export(args, index)



