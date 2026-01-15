#include "bsfs.h"
#include <stdio.h>
#include <string.h>
#include <assert.h>

void test_multi_partition() {
    printf("\nTesting Multi-partition support...\n");

    // Create tenant
    uint8_t master_key[32] = {0x1, 0x2, 0x3, 0x4};
    bsfs_tenant_t tenant;
    if (bsfs_tenant_init(&tenant, "test_multi.blob", master_key) != 0) {
        printf("Failed to init tenant\n");
        return;
    }

    // Create enough files to fill the first partition (max 64 files)
    printf("Filling partition 0 (64 files)...\n");
    uuid_t file_ids[70];
    for (int i = 0; i < 64; i++) {
        uuid_generate(file_ids[i]);
        if (bsfs_write_file(&tenant, file_ids[i], (uint8_t*)"data", 4) != 0) {
            printf("Failed to write file %d\n", i);
            return;
        }
    }

    if (tenant.partition_count != 1) {
        printf("Expected 1 partition, got %d\n", tenant.partition_count);
        return;
    }

    // Create 65th file - should trigger new partition
    printf("Writing 65th file (should create partition 1)...\n");
    uuid_generate(file_ids[64]);
    if (bsfs_write_file(&tenant, file_ids[64], (uint8_t*)"data", 4) != 0) {
        printf("Failed to write file 65 (new partition)\n");
        return;
    }

    if (tenant.partition_count != 2) {
        printf("Expected 2 partitions, got %d\n", tenant.partition_count);
        return;
    }

    // Verify we can read file from partition 0
    uint8_t *data;
    size_t size;
    if (bsfs_read_file(&tenant, file_ids[0], &data, &size) != 0) {
        printf("Failed to read file from partition 0\n");
        return;
    }
    free(data);

    // Verify we can read file from partition 1
    if (bsfs_read_file(&tenant, file_ids[64], &data, &size) != 0) {
        printf("Failed to read file from partition 1\n");
        return;
    }
    free(data);

    bsfs_tenant_cleanup(&tenant);

    // Re-open to verify persistence
    printf("Re-opening tenant to verify discovery...\n");
    if (bsfs_tenant_init(&tenant, "test_multi.blob", master_key) != 0) {
        printf("Failed to re-init tenant\n");
        return;
    }

    if (tenant.partition_count != 2) {
        printf("Expected 2 partitions after reload, got %d\n", tenant.partition_count);
        return;
    }

    bsfs_tenant_cleanup(&tenant);
    printf("✓ Multi-partition test passed!\n");
}

int main() {
    test_multi_partition();
    return 0;
}
