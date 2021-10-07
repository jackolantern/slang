#!/usr/bin/env python

import os
import sys
import argparse
import simplejson

from . import compiler


def main():
    parser = make_cli_parser()
    args = parser.parse_args()
    try:
        compile_cady(args)
    except compiler.ParseError as e:
        print("Compilation error.", file=sys.stderr)
        e.print()
        sys.exit(-1)


def make_scope():
    return compiler.make_default_scope()


def compile_cady(args):
    scope = make_scope()
    result = compiler.run_file(args.in_path, scope)
    if not result:
        sys.exit(-1)

    simplejson.dump(result, sys.stdout, for_json=True)
    sys.stdout.write("\n")
    sys.stdout.flush()


def make_cli_parser():
    parser = argparse.ArgumentParser(prog="slang", usage="%(prog)s [options]")

    parser.add_argument(
        "--grid-size",
        dest="grid_size",
        metavar="N",
        type=int,
        default=4,
        help="Overide the default grid size.",
    )
    parser.add_argument(
        "--grid-fine",
        dest="grid_fine",
        metavar="N",
        type=int,
        default=1,
        help="Overide the default fine grid size.",
    )
    parser.add_argument(
        "--grid-position",
        dest="grid_position",
        choices=("top", "bottom", "none"),
        default="top",
        help="Overide the default grid position.",
    )

    parser.add_argument(
        "--ppu", dest="ppu", metavar="N", type=int, default=8, help="Pixels per unit."
    )
    parser.add_argument(
        "--zoom", dest="zoom", metavar="N", type=int, default=1, help="z position."
    )

    parser.add_argument(
        "-p",
        dest="doprint",
        action="store_true",
        help="Print the result instead of drawing.  Ignores the `out_path`.",
    )

    parser.add_argument(
        "in_path", type=str, help="The path to the cady program to run."
    )
    parser.add_argument("out_path", nargs="?", type=str, help="Path to write result.")
    return parser


if __name__ == "__main__":
    main()
