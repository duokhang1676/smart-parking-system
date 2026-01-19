#include "sl_cli_handles.h"
#include "sl_cli_storage_nvm3_instances.h"

#include "sl_cli_storage_nvm3_config_inst.h"

//****************************************************************************
// Macros

#if !defined(min)
#define min(a,b) ((a < b) ? a : b)
#endif

//****************************************************************************
// Variables

// The default handle is used for cli commands that do not specify instances.
static cli_storage_nvm3_handle_t default_handle = NULL;


// Instance variables for inst
static cli_storage_nvm3_t inst_instance;


//****************************************************************************
// Global functions.

cli_storage_nvm3_handle_t sl_cli_storage_nvm3_instances_convert_handle(sl_cli_handle_t cli_handle)
{
  
  if (inst_instance.cli_handle == cli_handle) {
    return &inst_instance;
  }
  
  return default_handle;
}

void sl_cli_storage_nvm3_instances_init(void)
{
  // Initialize inst
  default_handle = &inst_instance;
  inst_instance.cli_handle           = SL_CLI_STORAGE_NVM3_INST_CLI_HANDLE;
  inst_instance.prompt               = SL_CLI_STORAGE_NVM3_INST_PROMPT;
  inst_instance.end_string           = SL_CLI_STORAGE_NVM3_INST_END_STRING;
  inst_instance.key_offset           = SL_CLI_STORAGE_NVM3_INST_KEY_OFFSET;
  inst_instance.key_count            = SL_CLI_STORAGE_NVM3_INST_KEY_COUNT;
  inst_instance.execute_while_define = SL_CLI_STORAGE_NVM3_INST_EXECUTE;
  // Some simple configuration calculations
  inst_instance.key_offset           = min(inst_instance.key_offset, SL_CLI_STORAGE_NVM3_KEY_COUNT - 1);
  inst_instance.key_count            = min(inst_instance.key_count, SL_CLI_STORAGE_NVM3_KEY_COUNT - inst_instance.key_offset);
  inst_instance.key_next             = inst_instance.key_offset;
  // Initialize the instance.
  sl_cli_storage_nvm3_init(&inst_instance);
  
}
