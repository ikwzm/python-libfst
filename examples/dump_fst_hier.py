#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 ikwzm

from   fst_reader import FST_Reader
import sys
import yaml
import argparse

if __name__ == '__main__':
    print_tag = "Dump_FST_Hier :"
    parser = argparse.ArgumentParser(description="Dump FST hierarchy as YAML")
    parser.add_argument("inputs"        , metavar="FILE", nargs="+", help="Input FST file(s)" )
    parser.add_argument("-o", "--output", metavar="FILE", default=None,
                        help="Output file ('-' for stdout)")

    args   = parser.parse_args()

    if   args.output is None:
        out = None
    elif args.output == "-":
        out = sys.stdout
    else:
        out = open(args.output, "w", encoding="utf-8") 

    try:
        merged = {"files": []}
        for filename in args.inputs: 
            dumper = FST_Reader(filename)
            try:
                dumper.read_tree()
                dumper.print_info()
                merged["files"].append({"filename": filename, **dumper.tree})
            finally:
                dumper.close()

        if out is not None:
            yaml.dump(merged, out, sort_keys=False, allow_unicode=True)

    finally:
        if out is not None and out is not sys.stdout: 
            out.close()
