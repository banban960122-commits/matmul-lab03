	.file	"matmul.c"
	.text
	.globl	matmul
	.def	matmul;	.scl	2;	.type	32;	.endef
	.seh_proc	matmul
matmul:
	pushq	%rbp
	.seh_pushreg	%rbp
	movq	%rsp, %rbp
	.seh_setframe	%rbp, 0
	subq	$16, %rsp
	.seh_stackalloc	16
	.seh_endprologue
	movq	%rcx, 16(%rbp)
	movq	%rdx, 24(%rbp)
	movq	%r8, 32(%rbp)
	movl	$0, -4(%rbp)
	jmp	.L2
.L7:
	movl	$0, -8(%rbp)
	jmp	.L3
.L6:
	movl	-4(%rbp), %edx
	movl	%edx, %eax
	addl	%eax, %eax
	addl	%eax, %edx
	movl	-8(%rbp), %eax
	addl	%edx, %eax
	cltq
	leaq	0(,%rax,4), %rdx
	movq	32(%rbp), %rax
	addq	%rdx, %rax
	movl	$0, (%rax)
	movl	$0, -12(%rbp)
	jmp	.L4
.L5:
	movl	-4(%rbp), %edx
	movl	%edx, %eax
	addl	%eax, %eax
	addl	%eax, %edx
	movl	-8(%rbp), %eax
	addl	%edx, %eax
	cltq
	leaq	0(,%rax,4), %rdx
	movq	32(%rbp), %rax
	addq	%rdx, %rax
	movl	(%rax), %r8d
	movl	-4(%rbp), %edx
	movl	%edx, %eax
	addl	%eax, %eax
	addl	%eax, %edx
	movl	-12(%rbp), %eax
	addl	%edx, %eax
	movslq	%eax, %rdx
	movq	16(%rbp), %rax
	addq	%rdx, %rax
	movzbl	(%rax), %eax
	movsbl	%al, %ecx
	movl	-12(%rbp), %edx
	movl	%edx, %eax
	addl	%eax, %eax
	addl	%eax, %edx
	movl	-8(%rbp), %eax
	addl	%edx, %eax
	movslq	%eax, %rdx
	movq	24(%rbp), %rax
	addq	%rdx, %rax
	movzbl	(%rax), %eax
	movsbl	%al, %eax
	imull	%eax, %ecx
	movl	-4(%rbp), %edx
	movl	%edx, %eax
	addl	%eax, %eax
	addl	%eax, %edx
	movl	-8(%rbp), %eax
	addl	%edx, %eax
	cltq
	leaq	0(,%rax,4), %rdx
	movq	32(%rbp), %rax
	addq	%rdx, %rax
	leal	(%r8,%rcx), %edx
	movl	%edx, (%rax)
	addl	$1, -12(%rbp)
.L4:
	cmpl	$2, -12(%rbp)
	jle	.L5
	addl	$1, -8(%rbp)
.L3:
	cmpl	$2, -8(%rbp)
	jle	.L6
	addl	$1, -4(%rbp)
.L2:
	cmpl	$2, -4(%rbp)
	jle	.L7
	nop
	nop
	addq	$16, %rsp
	popq	%rbp
	ret
	.seh_endproc
	.ident	"GCC: (MinGW-W64 x86_64-ucrt-posix-seh, built by Brecht Sanders, r7) 15.2.0"
