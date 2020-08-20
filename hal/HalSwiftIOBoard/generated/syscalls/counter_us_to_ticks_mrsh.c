/* auto-generated by gen_syscalls.py, don't edit */
#if __GNUC__ > 4 || (__GNUC__ == 4 && __GNUC_MINOR__ >= 6)
#pragma GCC diagnostic push
#endif
#ifdef __GNUC__
#pragma GCC diagnostic ignored "-Wstrict-aliasing"
#endif
#include <syscalls/counter.h>

extern u32_t z_vrfy_counter_us_to_ticks(const struct device * dev, u64_t us);
uintptr_t z_mrsh_counter_us_to_ticks(uintptr_t arg0, uintptr_t arg1, uintptr_t arg2,
		uintptr_t arg3, uintptr_t arg4, uintptr_t arg5, void *ssf)
{
	_current->syscall_frame = ssf;
	(void) arg3;	/* unused */
	(void) arg4;	/* unused */
	(void) arg5;	/* unused */
	union { struct { uintptr_t lo, hi; } split; u64_t val; } parm0;
	parm0.split.lo = arg1;
	parm0.split.hi = arg2;
	u32_t ret = z_vrfy_counter_us_to_ticks(*(const struct device **)&arg0, parm0.val)
;
	return (uintptr_t) ret;
}

#if __GNUC__ > 4 || (__GNUC__ == 4 && __GNUC_MINOR__ >= 6)
#pragma GCC diagnostic pop
#endif