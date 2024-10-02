# Copyright (C) 2024  Cameron McDonald

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
from pathlib import Path
from .macro import Preprocessor, PreprocessingException
from sys import stderr, exit
from time import sleep

WATCH_POLL_DELAY = 0.5  # check 2x per second


def main(source_file, out_file, should_print, clobber, err_keep_going, should_watch):
    source_path = Path(source_file)

    # get the path to be written to
    if should_print:
        out_path = None
    else:
        if out_file is None:
            out_path = source_path.with_suffix(".preprocessed" + source_path.suffix)
        else:
            out_path = Path(out_file)

        # check args
        if not clobber and source_path.resolve() == out_path.resolve():
            stderr.write(
                "ERROR - Source and destination files are the same, use --clobber to allow this.\n"
            )
            exit(1)

    # do the preprocessing
    preprocessor = Preprocessor(err_keep_going)
    if should_watch:
        # poll the input file and reprocess if it has been changed
        preprocess_watch(preprocessor, source_path, out_path)
    else:
        preprocess_once(preprocessor, source_path, out_path)


def write_output(out_path, output):
    if out_path is None:
        # output to stdout
        print(output)
    else:
        out_path.write_text(output)


def preprocess_watch(preprocessor, source_path, out_path):
    while True:
        prev_mtime = source_path.stat().st_mtime

        prog = read_prog(source_path)
        try:
            output = preprocessor.process(prog)
            write_output(out_path, output)
            stderr.write("[ Preprocessing succeeded ]\n")
        except PreprocessingException:
            # we don't want to exit, just report the errors
            stderr.write("[ Preprocessing failed, no output was generated ]\n")  

        # periodically check to see if the file has changed
        stderr.write("\n[ Watching for Changes... ]\n")
        stderr.flush()
        try:
            while source_path.stat().st_mtime == prev_mtime:
                sleep(WATCH_POLL_DELAY)
        except KeyboardInterrupt:
            stderr.write("[ Got ctrl-c, exiting ]\n")
            exit(0)
        stderr.write("[ Source file change detected ]\n")


def preprocess_once(preprocessor, source_path, out_path):
    prog = read_prog(source_path)
    try:
        output = preprocessor.process(prog)
        write_output(out_path, output)
    except PreprocessingException:
        # error has already been logged, just exit
        exit(1)


def read_prog(source_path):
    try:
        return source_path.read_text()
    except FileNotFoundError:
        stderr.write(f"ERROR - Source file {source_path} does not exist.\n")
        exit(1)


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("sourcefile", help="The path of the file to be preprocessed.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-o", "--outfile",
        help="The path of the file to output to. If no path is specified, " +
        "{sourcefile}.processed.{sourcefile extension} is used."
    )
    group.add_argument("--print", action="store_true", help="Output to stdout instead of a file.")
    parser.add_argument("--clobber", action="store_true", help="Allow overwriting the source file.")
    parser.add_argument(
        "--keep-going",
        action="store_true",
        help="Continue even if an error is detected. You probably shouldn't use this! " +
             "If you do, be prepared for crashes and incorrect output."
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch the source file for changes and automatically re-process it."
    )
    args = parser.parse_args()

    main(args.sourcefile, args.outfile, args.print, args.clobber, args.keep_going, args.watch)
