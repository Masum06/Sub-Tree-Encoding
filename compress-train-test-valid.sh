#!/bin/bash
for filename in ../CodeSearchNet/train_test_valid_uncompressed/*[0-9].json; do
    python compress.py $filename 10000
done