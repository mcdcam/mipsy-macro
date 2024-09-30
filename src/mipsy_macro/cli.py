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

def main(source_file, out_file, should_print, clobber, err_keep_going):
    source_path = Path(source_file)

    if not should_print:
        if out_file is None:
            out_path = source_path.with_suffix(".preprocessed" + source_path.suffix)
        else:
            out_path = Path(out_file)

        # check args
        if not clobber and source_path.resolve() == out_path.resolve():
            print("Source and destination files are the same, use --clobber to allow this.")
            exit(1)

    # Do the preprocessing
    preprocessor = Preprocessor(err_keep_going)
    prog = source_path.read_text()
    try:
        output = preprocessor.process(prog)
    except PreprocessingException:
        # error has already been logged, just exit
        exit(1)
    
    if should_print:
        print(output)
    else:
        out_path.write_text(output)

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
    args = parser.parse_args()

    main(args.sourcefile, args.outfile, args.print, args.clobber, args.keep_going)