// Match the application entry symbol expected by the Qt iOS platform plugin.
#ifdef KIOKU_ENTRY
#ifdef KIOKU_ENTRY_EXTERN_C
extern "C" int KIOKU_ENTRY(int, char **);
#endif
#define main KIOKU_ENTRY
#endif
#include "../src/main.mm"
