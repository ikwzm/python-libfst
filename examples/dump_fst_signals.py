#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 ikwzm

from   fst_reader import FST_Reader
import sys
import yaml
import argparse

import re

def parse_time_arg(reader, text):
    """
    Parse command line time argument.

    Examples:
        "100 ns" -> reader.parse(100, "ns")
        "100ns"  -> reader.parse(100, "ns")
        "10000"  -> reader.parse(10000)
    """
    if text is None:
        return None
    text = text.strip()
    # 数値 + 単位
    m = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Zµ]+)", text)
    if m:
        value = float(m.group(1))
        unit  = m.group(2)
        return reader.parse_timestamp(value, unit)

    # 数値のみ
    m = re.fullmatch(r"[0-9]+", text)
    if m:
        return reader.parse_timestamp(int(text))

    raise ValueError(f"Invalid time format: {text}")

if __name__ == '__main__':
    print_tag = "Dump_FST_Signals :"
    parser = argparse.ArgumentParser(description="Dump FST signals ad VCD")
    parser.add_argument("input"          , metavar="FST" , help="Input FST file(s)" )
    parser.add_argument("-s", "--signal" , dest="signals", metavar="PATTERN", action="append",
                        help=("Signal pattern (glob). "
                              "May be specified multiple times."))
    parser.add_argument("-S", "--start-time", metavar="TIME", default=None,
                        help="Start Time (default: 0)")
    parser.add_argument("-E", "--end-time"  , metavar="TIME", default=None,
                        help="End Time (default: end of file)")
    parser.add_argument("-o", "--output"    , metavar="FILE", default="-",
                        help="Output file ('-' for stdout)")
    parser.add_argument("-l", "--list-signals", action="store_true",
                        help="List matching signals only")

    args   = parser.parse_args()

    if args.output == "-":
        out = sys.stdout
    else:
        out = open(args.output, "w", encoding="utf-8")

    try:
        reader = FST_Reader(args.input)
        try:
            reader.print_info()
            reader.read_tree()
            signal_list = []
            for pattern in args.signals:
                signal_list.extend(reader.find_var_list(pattern))

            name_list = []
            var_list  = []
            for name,var in signal_list:
                name = "::".join(name)
                name_list.append(name)
                if "handle" in var:
                    var_list.append((name, var["width"], var["handle"]))

            for name, width, handle in var_list:
                print(f"{handle:6d} {name}", file=out)

            if args.list_signals is False:
                
                reader.clear_facility_process_mask_all()
                for name,width, handle in var_list:
                    reader.set_facility_process_mask(handle)

                if args.start_time is not None or args.end_time is not None:
                    if args.start_time is None:
                        start_time = reader.start_time
                    else:
                        start_time = parse_time_arg(reader, args.start_time)
                        if start_time < reader.start_time:
                            start_time = reader.start_time
                    if args.end_time is None:
                        end_time = reader.end_time
                    else:
                        end_time = parse_time_arg(reader, args.end_time)
                        if end_time > reader.end_time:
                            end_time = reader.end_time
                    if start_time > end_time:
                        raise ValueError(f"Invalid time range: {start_time} > {end_time}")
                    print(f"start_time : {reader.format_timestamp(start_time)}")
                    print(f"end_time   : {reader.format_timestamp(end_time)}"  )
                    reader.set_limit_time_range(start_time, end_time)
                    for time,handle,value in reader.blocks():
                        if time >= start_time and time <= end_time:
                            print(f"{reader.format_timestamp(time)} {handle} {value}", file=out)
                else:
                    for time,handle,value in reader.blocks():
                        print(f"{reader.format_timestamp(time)} {handle} {value}", file=out)
            
        finally:
            reader.close()
    finally:
        if out is not None and out is not sys.stdout: 
            out.close()
        
