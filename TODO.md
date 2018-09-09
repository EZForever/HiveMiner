## TODO ##
- [x] Make it work  
- [ ] Multi-threading  
- [ ] Change thread affinity for better performance  


### How to implement Multi-threading ###
 * Change Job.jobChanged to a bitmask

### How to implement thread affinity changing ###
 * https://docs.microsoft.com/en-us/windows/desktop/api/processthreadsapi/nf-processthreadsapi-getcurrentthread
 * https://docs.microsoft.com/en-us/windows/desktop/api/processthreadsapi/nf-processthreadsapi-openthread
 * https://docs.microsoft.com/zh-cn/windows/desktop/api/winbase/nf-winbase-setthreadaffinitymask
 * sys/syscall.h syscall(SYS_gettid)
 * pthread.h pthread_setaffinity_np (?)
