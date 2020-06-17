#!/bin/bash
for filename in ../CodeSearchNet/train_test_valid_data/only_trees/*[0-9]u.json; do
    python compress.py $filename 100000
done