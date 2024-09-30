# A comment
# and another

#![tabsize(8)]

#define thing 123 + 456
#define thING2 123
#define moVe 123
#define $SP $rb
#define main 456
#define _3 3

main:				# int main(void) {

	la	$a0, prompt	# printf("Enter a number: ");
	li	$v0, 4
	syscall

end:
	li	$v0, 0
	jr	$ra		# return 0

	.data
prompt:
	.asciiz "Enter a number: "
