# Create a register macro ($ prefix). Replaces all future occurrences of $COOL_REGISTER with $s0.
#define $COOL_REGISTER $s0

# Create an address macro (@ prefix).
#define @ADDR numbers($s0)

# Create an immediate macro (no prefix). Mipsy already supports defining constants using the
# e.g. VAL = 3 + 4 * 5 syntax. You should usually use that instead of this, it's better!
#define INIT 4

# Create a directive macro (. prefix). You probably won't need to use this, but it's available.
#define .DRCTV .byte

# This is a raw macro (with ! prefix), no sanity checking of values is performed.
# They're occasionally useful for defining full statements (instructions, directives etc.).
# Don't use these unless you really know what you're doing, things will break if you're not careful.
#define !RET jr	$ra

main:
# These are scoped macros. They are removed when their label (`main__end` in this case) is reached.
# This is particularly useful for giving names to registers used in a function.
#defineuntil main__end $X $t0
#defineuntil main__end $Y $t1

	li	$t0, 4		# x = 4;
	li	$t1, 123			# y = 123;
	move	$s0, $t0	# cool_reg = x;
	sw	$t1, numbers($s0)		# numbers[cool_reg] = y;

# $X and $Y go out of scope here, so occurrences of them after this label won't be replaced,
# and they'll be able to be redefined as something else.
main__end:
	li	$v0, 0
	jr	$ra				# return 0;

	.data
prompt:
	.asciiz "Enter a number: "
numbers:
	.byte 0, 1, 2, 3, 4, 5, 6, 7	# char numbers[8] = { 0, 1, ... 7 };
