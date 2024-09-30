## MIPS Macro Preprocessor
A macro preprocessor made for the mipsy emulator (though it might work for others).

It is designed with many of the same philosophies as mipsy, aiming to make code
written for it easy to read and debug, and to catch many common macro mistakes.

## Features
- Macro substitution (`#define`)
    - Substitution is done after tokenisation, not just by crude find-and-replace
- Extensive checking of macro names and values
    - Appropriate prefixes for macro names (e.g. '$' for registers, see the usage section for details)
      are enforced to maintain code readability
- Helpful warning and error messages
- Scoped macros (`#defineuntil <label>`)
- Zero dependencies (other than Python 3.8+)
- Robust tokenisation/parsing strategy that shouldn't totally break if
  mipsy's syntax is expanded.

### Planned Features
- Proper packaging
- Removal/replacement of macro comments
- Substitution of tokens inside macros
- Editor support (maybe)

### Missing Features
- Function-like macros
- Multiline macro values
- `#undef`, `#ifdef` etc.
- Substitution of label names (I can't imagine why you'd ever want to do this)

## Installation
TODO

## Usage
*TODO: change after packaging is done.*
To run the preprocessor, run `macro.py <input filename> -o <output filename>`.

The format for a macro definition is `#define <name> <value>`.
The preprocessor enforces the use of prefixes on macro names as follows:
```
1. Immediates: [none]                     e.g. #define NAME 123
2. Registers: $                           e.g. #define $NAME $sp
3. Addresses (including labels): @        e.g. #define @NAME whatever_label($t0) 
4. Directives: .                          e.g. #define .NAME .word
5. Other/raw e.g. instruction, string: !  e.g. #define !NAME move $t0, $t1
```
Any occurrence of the macro name (incl. prefix) as a token (i.e. as its own word) *after* the macro definition will be replaced with the macro value.

Scoped macros can be used as follows: `#defineuntil <label> <name> <value>`. Scoped macros work the same way as regular macros, but they will be undefined automatically when `<label>` is reached (after which they can be redefined). This can be used e.g. to define `$IDX` differently in different loops/functions.

## Examples
TODO, see `./examples` for now.