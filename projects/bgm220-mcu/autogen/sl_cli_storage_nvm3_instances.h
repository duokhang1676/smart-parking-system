#ifndef SL_CLI_STORAGE_NVM3_INSTANCES_H
#define SL_CLI_STORAGE_NVM3_INSTANCES_H

#include "sl_cli.h"
#include "sl_cli_storage_nvm3.h"

#ifdef __cplusplus
extern "C" {
#endif

//****************************************************************************
// Global functions

cli_storage_nvm3_handle_t sl_cli_storage_nvm3_instances_convert_handle(sl_cli_handle_t cli_handle);
void sl_cli_storage_nvm3_instances_init(void);

#ifdef __cplusplus
}
#endif

#endif // SL_CLI_STORAGE_NVM3_INSTANCES_H