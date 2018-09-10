## TODO ##
- [x] Make it work  
- [x] Multi-threading  
- [ ] ~~Change thread affinity / multi-process for better performance~~  
  
### How to implement thread affinity changing ###
 * https://docs.microsoft.com/en-us/windows/desktop/api/processthreadsapi/nf-processthreadsapi-getcurrentthread
 * https://docs.microsoft.com/en-us/windows/desktop/api/processthreadsapi/nf-processthreadsapi-openthread
 * https://docs.microsoft.com/zh-cn/windows/desktop/api/winbase/nf-winbase-setthreadaffinitymask
 * sys/syscall.h syscall(SYS_gettid)
 * pthread.h pthread_setaffinity_np (?)
