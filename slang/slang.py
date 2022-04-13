#!/usr/bin/env python

import os
import sys
import argparse
import simplejson

from . import runtime


def main():
    parser = make_cli_parser()
    args = parser.parse_args()
    try:
        compile_slang(args)
    except runtime.ParseError as e:
        print("Compilation error.", file=sys.stderr)
        e.print()
        sys.exit(-1)


def make_environment():
    return runtime.make_default_environment()


def compile_slang(args):
    scope = make_environment()
    result = runtime.run_file(args.in_path, scope)
    if not result:
        sys.exit(-1)

    simplejson.dump(result, sys.stdout, for_json=True)
    sys.stdout.write("\n")
    sys.stdout.flush()


def make_cli_parser():
    parser = argparse.ArgumentParser(prog="slang", usage="%(prog)s [options]")
    parser.add_argument(
        "in_path", type=str, help="The path to the cady program to run."
    )

    parser.add_argument("out_path", nargs="?", type=str, help="Path to write result.")
    return parser


if __name__ == "__main__":
    import cProfile

    cProfile.run("main()")
