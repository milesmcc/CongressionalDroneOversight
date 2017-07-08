# combine-cr
A series of scripts designed to make compiling a dataset on the congressional record as painless as possible.

## Replicate DroneScout's dataset
0. Modify the scripts' constant values to better suit your purposes
1. Scrape all dates between 2000 and 2017 (inclusive) using Sunlight Foundation's `congressional-record` tool (i.e. `parsecr date1 date2 date3 ... date6210`).
2. Run `combine.py` while in the root of the previous tool's output directory. This will merge all the records into a single JSON file, named `congressional_record.json`.
3. Run `annotate.py` on `congressional_record.py`, which will give you a (larger) `annotated_congressional_record.py`.
