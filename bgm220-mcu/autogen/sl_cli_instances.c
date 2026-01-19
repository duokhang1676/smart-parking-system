#if defined(SL_COMPONENT_CATALOG_PRESENT)
#include "sl_component_catalog.h"
#endif
#include "sl_cli_instances.h"
#include "sl_cli.h"
#include "sl_string.h"
#include <string.h>
#if defined(SL_CATALOG_KERNEL_PRESENT) && SL_CLI_TICK_ENABLE
#include "cmsis_os2.h"
#include "sl_cmsis_os2_common.h"
#include "sl_assert.h"
#endif // defined(SL_CATALOG_KERNEL_PRESENT)



#include "sl_iostream_handles.h"

//****************************************************************************
// Macros

#define ELEVENTH_ARGUMENT(a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, ...) a11
#define COUNT_ARGUMENTS(...) ELEVENTH_ARGUMENT(dummy, ## __VA_ARGS__, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0)
#define ISEMPTY(...) (COUNT_ARGUMENTS(__VA_ARGS__) == 0)

//****************************************************************************
// Variables

extern const sl_cli_command_entry_t sl_cli_default_command_table[];




const sl_cli_handle_t sl_cli_handles[] = {

};

const uint32_t sl_cli_handles_count = sizeof(sl_cli_handles) / sizeof(sl_cli_handle_t);

//****************************************************************************
// Global functions

void sl_cli_instances_init(void)
{
  sl_cli_instance_parameters_t instance_parameters;

  
}

#if !defined(SL_CATALOG_KERNEL_PRESENT)
bool sl_cli_instances_is_ok_to_sleep(void)
{
  

  return true;
}

void sl_cli_instances_tick(void)
{
#if SL_CLI_TICK_ENABLE
sl_iostream_t *previous = sl_iostream_get_default();

  
  sl_iostream_set_default(previous);
#endif // SL_CLI_TICK_ENABLE
}
#endif
