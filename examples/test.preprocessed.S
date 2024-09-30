# A comment
# and another

#![tabsize(8)]

#defineuntil end THING 1
#define THING_2 0x456
#define $REG $v0
#define @ADDR 10($v0)
#define !OP syscall
#define .DRCTV .text

main:				# int main(void) {

	la	$a0, prompt	# printf("Enter a number: ");
	li	$v0, 4
	syscall

	li	$v0, 1	# scanf("%d", number);
	syscall

	li	$v0, 1;
	li	$v0, 3;syscall;

	li$v0,1;
	li $v0, 3;				syscall ;

	x = 10&7 * 0x3 | (5 / 2) + 2 ^ 3 -~(1) * 088976 % 000430 - 0o4 + 0b101010

	li	$v0, 11
	li	$a0, 'a'
	syscall

	li	$v0, 11
	li	$a0, '"'
	syscall

	li	$v0, 11
	li	$a0, '\0'
	syscall

	li	$v0, 11
	li	$a0, '\"'
	syscall

	li	$v0, 11
	li	$a0, '''
	syscall

	li	$v0, 11
	li	$a0, '\''
	syscall

	li	$v0, 11
	li	$a0, '\\'
	syscall

	li	$v0, 11
	li	$a0, '
' # why is this a thing????
	syscall

	li	$t7, 10
	sw	$t7, 10($v0)

	li	$s2, 780
	add	$s1, $s2, 8
	beq	$s1, 3,	end

end:
	li	$v0, 0
	jr	$ra		# return 0

	.data
prompt:
	.asciiz "Enter a number: "

multiline:
	.asciiz "some text
		 and some more"
evil1:
	.asciiz "a \"not very nice\" \n string\t \\ :("
evil2:
	.asciiz"a # string: 'hello'"why: .asciiz "hi??"
same.line: .asciiz "hi"

numbers:
	.word 1, 2, 3, 4

	.text
eof:
	syscall