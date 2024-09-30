## MIPS Macro Preprocessor
A MIPS assembly macro preprocessor made for the [mipsy](https://github.com/insou22/mipsy) emulator.

This is designed with many of the same philosophies as mipsy, aiming to make code
written for it easy to read and debug, and to catch many common macro mistakes.

## Features
- Macro substitution (`#define`)
    - Substitution is done properly (by tokenisation), not just by crude find-and-replace
- Extensive checking of macro names and values
    - Appropriate prefixes for macro names (e.g. '$' for registers, see the usage section for details)
      are enforced to maintain code readability
- Helpful warning and error messages
- Scoped macros (`#defineuntil <label>`)
- Zero dependencies (other than Python 3.8+)
- Robust tokenisation/parsing strategy that shouldn't totally break if
  mipsy gains support for new features

### Planned Features
- Removal/replacement of macro comments
- Automatic comment alignment (macro substitution misaligns comments currently)
- Ability to use a macro in another macro
- Editor support (maybe)

### Missing Features
- Function-like macros
- Multiline macro values
- `#undef`, `#ifdef` etc.
- Substitution of label names (I can't imagine why you'd ever want to do this)

## Installation
### Install from PyPI:
```sh
pip install mipsy-macro
```

This will install the package and the `mipsy-macro` command.
### CSE Machine Notes:
If you're installing this on a CSE machine it's a bit trickier since you can't install globally. Instead, do the following:
```sh
# install into your home directory
pip install mipsy-macro --target ~/mipsy-macro
# symlink the script to make it accessible from $PATH
mkdir -p ~/bin
ln -s ~/mipsy-macro/bin/mipsy-macro ~/bin/mipsy-macro
```

### Installation Check:
If everything is installed correctly you should be able to run `mipsy-macro -h` and get a help message.

## Usage
To use the preprocessor, run `mipsy-macro <input filename> -o <output filename>`. For detailed info about options, run `mipsy-macro -h`.

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

## Example
```
# Create a register macro ($ prefix). Replaces all future occurrences of $COOL_REGISTER with $s0.
#define $COOL_REGISTER $s0

# Create an address macro (@ prefix).
#define @ADDR numbers($s0)

# Create an immediate macro (no prefix). Mipsy already supports defining constants using the
# e.g. VAL = 3 + 4 * 5 syntax. You should usually use that instead of this, it's better!
#define INIT 4

# Create a directive keyword macro (. prefix). You probably won't need to use this, but it's there.
#define .DRCTV .byte

# This is a raw macro (! prefix), no sanity checking of values is performed.
# They're occasionally useful for defining full statements (instructions, directives etc.).
# Don't use these unless you really know what you're doing, things will break if you're not careful.
#define !RET jr        $ra

main:
# These are scoped macros. They are removed when their label (`main__end` in this case) is reached.
# This is particularly useful for giving names to registers used in a function.
#defineuntil main__end $X $t0
#defineuntil main__end $Y $t1

  li        $X, INIT                   # x = 4;
  li        $Y, 123                    # y = 123;
  move      $COOL_REGISTER, $X         # cool_reg = x;
  sw        $Y, @ADDR                  # numbers[cool_reg] = y;

# $X and $Y go out of scope here, so occurrences of them after this label won't be replaced,
# and they'll be able to be redefined as something else.
main__end:
  li        $v0, 0
  !RET                                 # return 0;

  .data
prompt:
  .asciiz "Enter a number: "
numbers:
  .DRCTV 0, 1, 2, 3, 4, 5, 6, 7        # char numbers[8] = { 0, 1, ... 7 };
```