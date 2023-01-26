#!/bin/bash

### Split data

for idx in `seq 200 299`; do
  echo "process "$idx
  wc -l eng$idx > eng$idx.nl
  xz eng$idx
done

