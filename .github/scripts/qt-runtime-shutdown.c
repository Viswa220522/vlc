/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Workaround for the pinned MinGW 12 runtime in the portable validation build.
 * A libstdc++ static destructor calls pthread_key_delete during DLL process
 * detach. Its write lock can wait for reader threads Windows already killed.
 * Normal key deletion and FreeLibrary cleanup must retain their behavior.
 * Windows reclaims the keys when terminating the process.
 *
 * See https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-best-practices
 * and https://sourceforge.net/p/mingw-w64/mailman/message/59353887/
 */
#include <windows.h>
#include <pthread.h>

int __real_pthread_key_delete(pthread_key_t key);

int __wrap_pthread_key_delete(pthread_key_t key)
{
    typedef BOOLEAN (WINAPI *ShutdownProbe)(void);
    HMODULE ntdll = GetModuleHandleW(L"ntdll.dll");
    ShutdownProbe shutdown = ntdll == NULL ? NULL :
        (ShutdownProbe)(void *)GetProcAddress(ntdll, "RtlDllShutdownInProgress");
    if (shutdown != NULL && shutdown())
        return 0;
    return __real_pthread_key_delete(key);
}
