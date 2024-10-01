# An Opinionated MIPS Macro Preprocessor

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


# Design Principles:
#   Should be easy to use and good at catching common mistakes
#   Should preserve whitespace/formatting.
#   Should be idempotent.
#   Should enforce conventions that make it easy to identify what a macro represents.
#   Should not be too dependent on precise syntax (i.e. should avoid complex parsing).

# Macro name rules:
#   Letters, numbers, underscores only
#   Can't start with a number
#   Warn on lowercase
#   Error on existing keyword match

# Macro value rules:
#   One line only (for now at least)
#
#   I like prefixes because they make it easy to know which kind of object a macro represents.
#   These prefixes should be enforced.
#   There are essentially 5 things that can be defined:
#   1. Immediates (already done by mipsy) --> #define NAME 123
#   2. Registers                          --> #define $NAME $xy
#   3. Addresses (incl. labels)           --> #define @NAME whatever_label($xy)
#   4. Directives                         --> #define .NAME .xyz
#   5. Other/raw e.g. instruction, string --> #define !NAME move $t0, $t1

# TODO: macro substitution inside a macro value
# TODO: editor support (hopefully won't be too hard)
# TODO: tidy up the code

from enum import Enum, auto
from logging import CRITICAL, WARNING, ERROR, getLogger, StreamHandler, Formatter
import re
import json
from collections import defaultdict
from pathlib import Path

# State machine states for tokenisation
class State(Enum):
    CODE = auto()        # anything that's not a string/char/comment
    STRING = auto()      # inside a string literal
    STRING_ESC = auto()  # the character escaped by a backslash in a string
    CHAR = auto()        # first internal character of a single-quoted char literal
    CHAR_2 = auto()      # second character in a single-quoted char literal
    CHAR_END = auto()    # closing quote of single-quoted char literal
    COMMENT = auto()     # characters between the # and \n in a comment

# regexr.com/86aoc
#                        match non-label tokens   match labels
TOKEN_RE = re.compile(r"(^[$.@!]?[A-Za-z_]\w*\Z)|(^[A-Za-z_][\w.]*:\Z)")
# allows starting with a number because we don't want to let numbers separate tokens
PSEUDO_TOKEN_RE = re.compile(r"(^[$.@!]?\w*\Z)|(^\w[\w.]*:\Z)")
MACRO_NAME_RE = re.compile(r"^[$.@!]?[A-Za-z_]\w*\Z")
# crude literal number matching
NUMBER_RE = re.compile(r"^-?(0(x|o|b))?[\da-fA-F]+\Z")
LABEL_RE = re.compile(r"^[A-Za-z_][\w.]*\Z")
# number/label/char
IMMEDIATE_RE = re.compile(r"^((-?(0(x|o|b))?[\da-fA-F]+)|([A-Za-z_][\w.]*)|('\\?.'))\Z")
# detection (not full matching) of comments or single-line strings
DETECT_COMMENT_OR_STR_RE = re.compile(r"(?<!')(#|\")")

# get the set of MIPS token names we want to avoid using
reserved_words_path = Path(__file__).parent / "./resources/reserved_words.json"
with open(reserved_words_path, "r") as f:
    reserved_word_lists = json.load(f)
    reserved_words = set([
        *reserved_word_lists["registers"],
        *reserved_word_lists["instructions"],
        *reserved_word_lists["directives"]
    ])
# the base token of the reserved words, e.g. $sp --> sp
reserved_words_stripped = {word.lstrip("$."): word for word in reserved_words}

# Custom exception class for errors that occur during processing as a result of invalid input
class PreprocessingException(Exception):
    pass

# Create a class so that the processing state can be easily accessed by methods
# and so the preprocessor can be used by other modules
class Preprocessor:
    # Note: most attrs are undefined until process() is called
    def __init__(self, err_keep_going=False) -> None:
        # Should an exception not be raised if a non-critical error is logged?
        self.err_keep_going = err_keep_going

        # If the user (of the class) wants the logs to go somewhere else they can modify self.logger
        self.logger = getLogger(str(id(self)))  # don't care about the name, just make it unique
        handler = StreamHandler()
        self.logger.addHandler(handler)
        self.logger.addFilter(self._add_line_no)
        handler.setFormatter(Formatter(
            "{levelname} - {message}",
            style="{",
        ))

    # Modifies a logged message to add the line number that processing is at
    # Used as a filter in the logger (but doesn't do any filtering)
    def _add_line_no(self, record):
        record.msg = f"Line {self.line_no}: {record.msg}"
        return True

    # Logs `message` at log level `level` iff `value` is falsy, raising an exception if required
    def _log_assert(self, value, message, level=CRITICAL):
        if not value:
            self.logger.log(level, message)
            if level >= CRITICAL or (level >= ERROR and not self.err_keep_going):
                raise PreprocessingException(message)

    def name_type(self, name):
        if name.startswith("$"):
            return "register"
        elif name.startswith("."):
            return "directive"
        else:
            return "instruction"
        
    def is_register(self, value: str):
        if value in reserved_word_lists["registers"]:
            return True
        if value[1:].isnumeric() and int(value[1:]) < 32:
            return True
        return False
    
    def strip_name(self, name: str):
        return name.lower().lstrip(".$@!")

    # Perform a bunch of checks on the macro name and value.
    # Doesn't strictly parse the value but instead uses heuristics/crude parsing because it's
    # easier to give meaningful error messages this way (and parsing is complex and fragile).
    def check_macro(self, name: str, value: str):
        # Check that the name uses legal characters
        self._log_assert(
            MACRO_NAME_RE.match(name),
            f"Macro name '{name}' is not valid. Macro names must have this format:\n" +
            "  <$ or @ or ! or . or nothing><letter or _><0 or more letters, numbers, and/or _>\n" +
            "  e.g. $NAME e.g. NAME_1 e.g. _123ABC e.g. @BIG_ARRAY",
            ERROR
        )

        # Check that the name is uppercase and doesn't conflict
        self._log_assert(
            not any(c.islower() for c in name),
            f"Macro name '{name}' is not uppercase. All caps macro names are encouraged.",
            WARNING
        )

        self._log_assert(
            name.lower() not in reserved_words,
            f"Macro name '{name}' conflicts with a MIPS {self.name_type(name)} name.",
            ERROR
        )

        self._log_assert(
            name not in self.macros,
            f"A macro with name '{name}' is already defined. Redefinition of macros is not allowed.",
            ERROR
        )

        # Check for similarity (equality w/o case and prefix) to other symbols
        name_stripped = self.strip_name(name)
        if name_stripped in reserved_words_stripped:
            self.logger.warning(
                f"Macro name '{name}' is similar to the MIPS " +
                f"{self.name_type(reserved_words_stripped[name_stripped])} " +
                f"'{reserved_words_stripped[name_stripped]}'."
            )
        if name_stripped in self.macros_stripped:
            self.logger.warning(
                f"Macro name '{name}' is similar to the existing macro(s): " +
                f"{self.macros_stripped[name_stripped]}."
            )

        self._log_assert(
            name not in self.labels,
            f"Macro name '{name}' conflicts with an existing label.",
            ERROR
        )

        # Check that the value is valid and matches the name prefix
        if name.startswith("!"):
            # Raw macro, allow anything
            return

        # check for a comment or string (as those could break things)
        self._log_assert(
            not DETECT_COMMENT_OR_STR_RE.search(value),
            f"Non-raw macro value '{value}' contains a string or comment.\n  "
            "Comments in macros can break things by commenting out everything after them where " +
            "they're used.\n  " +
            "If you are trying to define a string you should use the ! prefix for a raw macro " +
            "e.g. #define !STR_1 \"hello\".",
            ERROR
        )

        if name.startswith("$"):
            self._log_assert(
                self.is_register(value),
                f"Value '{value}' of register macro is not a valid register.",
                ERROR
            )
        elif name.startswith("."):
            self._log_assert(
                value in reserved_word_lists["directives"],
                f"Value '{value}' of directive macro is not a valid directive.",
                ERROR
            )
        elif name.startswith("@"):
            # there are a bunch of possible address formats
            # BACKLOG: write a regex for them
            # in the meantime, just check that it's not a register or number
            self._log_assert(
                not value.startswith("$"),
                f"Value '{value}' of address macro looks like a register, did you mean ({value})?",
                ERROR
            )
            self._log_assert(
                not NUMBER_RE.match(value),
                f"Value '{value}' of address macro looks like a number, this probably isn't right.",
                WARNING
            )
        else:
            self._log_assert(
                IMMEDIATE_RE.match(value),
                f"Immediate macro value '{value}' isn't a valid single immediate.\n  "
                "If you are trying to define a compound mathematical expression you should use "
                "mipsy's built-in syntax e.g. X = 1 + 2.\n  " +
                "Because #defines use text substitution, compound immediate macros won't work " +
                "everywhere you'd expect them to.\n  " +
                "If you *really* know what you're doing you can use the ! prefix to perform a " +
                "raw substitution with no sanity checking e.g. #define !X 1 + 2.",
                ERROR
            )

    def parse_macro(self, comment: str):
        if comment.startswith("#define "):
            try:
                _, name, val = comment.split(maxsplit=2)
            except ValueError:
                self.logger.error(
                    f"Macro '{comment}' failed to parse. Check that it has a name and value.\n  " +
                    "The correct format is #define <name> <value>."
                )
                exit(1)
            
            self.check_macro(name, val.strip())
            # print(f"{name=}, {val=}")
            self.macros[name] = val
            self.macros_stripped[self.strip_name(name)].append(name)
        elif comment.startswith("#defineuntil "):
            try:
                _, label, name, val = comment.split(maxsplit=3)
            except ValueError:
                self.logger.error(
                    f"Macro '{comment}' failed to parse. Check that it has a label, name and " +
                    "value.\n  The correct format is #defineuntil <label> <name> <value>."
                )
                exit(1)
            # make sure the label is valid
            self._log_assert(
                LABEL_RE.match(label),
                f"Scoped macro label '{label}' is not a valid label name. Make sure you're not " +
                "including the ':' used only in the label definition.",
                ERROR
            )
            # make sure we're not already past the label
            self._log_assert(
                label not in self.labels,
                f"Scoped macro '{comment}' is defined after its finishing label '{label}'.",
                ERROR
            )
            self.check_macro(name, val.strip())
            # print(f"{label=}, {name=}, {val=}")
            self.macros[name] = val
            self.macros_stripped[self.strip_name(name)].append(name)
            self.label_watches[label].append(name)

    # token_end is the index of the first character after the token
    # i.e. the first character that didn't match.
    def _finish_token(self, token_end: int):
        token = self.program[self.token_start:token_end]
        if TOKEN_RE.match(token):
            # attempt to parse a label
            if token.endswith(":"):
                label = token[:-1]
                self._log_assert(
                    label not in self.macros,
                    f"Label name '{label}' conflicts with an existing macro.",
                    ERROR
                )
                self.labels.append(label)

                # undefine any #defineuntil <this label>
                for macro_name in self.label_watches[label]:
                    del self.macros[macro_name]
                    macro_name_stripped = self.strip_name(macro_name)
                    macro_name_stripped_matches = self.macros_stripped[macro_name_stripped]
                    macro_name_stripped_matches.remove(macro_name)
                    if not macro_name_stripped_matches:
                        del self.macros_stripped[macro_name_stripped]      
                del self.label_watches[label]
            
            # get the macro value for the token if one exists
            replacement = self.macros[token] if token in self.macros else token
            self.tokens.append((token, (self.token_start, token_end), replacement))

            # replace the token in the output code
            self.new_program += self.program[self.new_program_up_to:self.token_start]
            self.new_program += replacement
            self.new_program_up_to = token_end
        self.token_start = token_end

    # Tokenise and replace in a single pass.
    def process(self, program: str):
        # Initialise attrs
        self.program = program
        self.new_program = ""
        self.new_program_up_to = 0
        self.macros = {}
        self.macros_stripped = defaultdict(list)
        self.label_watches = defaultdict(list)
        self.tokens = []
        self.labels = []
        self.token_start = 0
        self.line_no = 1
        
        # Uses a state machine to ignore comments, strings, and chars.
        state = State.CODE
        for i, c in enumerate(self.program): 
            if state == State.CODE:
                if not PSEUDO_TOKEN_RE.match(self.program[self.token_start:i + 1]):
                    self._finish_token(i)

                if c == '"':
                    state = State.STRING
                elif c == "#":
                    # attempt to parse a #define
                    comment = self.program[i:].split("\n")[0]
                    self.parse_macro(comment)

                    state = State.COMMENT
                elif c == "'":
                    state = State.CHAR
            elif state == State.STRING:
                if c == '"':
                    state = State.CODE
                elif c == "\\":
                    state = State.STRING_ESC
            elif state == State.STRING_ESC:
                # consume a character
                state = State.STRING
            elif state == State.CHAR:
                if c == "\\":
                    state = State.CHAR_2
                else:
                    state = State.CHAR_END
            elif state == State.CHAR_2:
                # consume a character
                state = State.CHAR_END
            elif state == State.CHAR_END:
                state = State.CODE
                if c != "'":
                    self.logger.warning(
                        f"Expected closing single quote, got {repr(c)}. " +
                        "Ignoring the rest of the line."
                    )
                    # Treat as a comment and skip until the next newline
                    state = State.COMMENT if c != "\n" else State.CODE

            elif state == State.COMMENT:
                if c == "\n":
                    state = State.CODE
            
            if c == "\n":
                self.line_no += 1

        if self.token_start < len(self.program):
            self._finish_token(len(self.program))
        if self.new_program_up_to < len(self.program):
            self.new_program += self.program[self.new_program_up_to:len(self.program)]
        
        # make sure all the #defineuntils are done
        for label, macros in self.label_watches.items():
            for macro in macros:
                self.logger.warning(
                    f"The scoped macro '{macro}' wasn't closed because its finishing label " +
                    f"'{label}' was never seen. Check that label exists and is spelled correctly."
                )

        return self.new_program

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

if __name__ == '__main__':
    import argparse

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
