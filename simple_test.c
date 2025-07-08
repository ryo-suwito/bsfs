#include "bsfs.h"
#include <stdio.h>

int main() {
    printf("Simple BSFS Test\n");
    
    // Test basic initialization
    uint8_t master_key[32] = {0};
    for (int i = 0; i < 32; i++) {
        master_key[i] = i;
    }
    
    printf("Master key initialized\n");
    
    bsfs_tenant_t tenant;
    printf("About to init tenant\n");
    
    if (bsfs_tenant_init(&tenant, "simple_test.blob", master_key) != 0) {
        printf("FAILED: Could not initialize tenant\n");
        return 1;
    }
    
    printf("Tenant initialized successfully\n");
    
    bsfs_tenant_cleanup(&tenant);
    printf("Test completed\n");
    
    return 0;
}