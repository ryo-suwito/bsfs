#include "bsfs.h"
#include <stdio.h>
#include <string.h>
#include <assert.h>

void test_basic_operations() {
    printf("Testing basic BSFS operations...\n");
    
    // Initialize OpenSSL
    if (RAND_status() != 1) {
        printf("FAILED: OpenSSL not properly initialized\n");
        return;
    }
    
    // Generate master key
    uint8_t master_key[BSFS_AES_KEY_SIZE];
    if (RAND_bytes(master_key, BSFS_AES_KEY_SIZE) != 1) {
        printf("FAILED: Could not generate master key\n");
        return;
    }
    
    // Initialize tenant
    bsfs_tenant_t tenant;
    if (bsfs_tenant_init(&tenant, "test_tenant.blob", master_key) != 0) {
        printf("FAILED: Could not initialize tenant\n");
        return;
    }
    
    printf("✓ Tenant initialized\n");
    
    // Test file write
    uuid_t file_id;
    uuid_generate(file_id);
    
    const char *test_data = "Hello, BSFS! This is a test file with some content.";
    size_t test_size = strlen(test_data);
    
    if (bsfs_write_file(&tenant, file_id, (const uint8_t*)test_data, test_size) != 0) {
        printf("FAILED: Could not write file\n");
        bsfs_tenant_cleanup(&tenant);
        return;
    }
    
    printf("✓ File written successfully\n");
    
    // Test file read
    uint8_t *read_data;
    size_t read_size;
    
    if (bsfs_read_file(&tenant, file_id, &read_data, &read_size) != 0) {
        printf("FAILED: Could not read file\n");
        bsfs_tenant_cleanup(&tenant);
        return;
    }
    
    printf("✓ File read successfully\n");
    
    // Verify data
    if (read_size != test_size || memcmp(read_data, test_data, test_size) != 0) {
        printf("FAILED: Data verification failed\n");
        printf("Expected: %s\n", test_data);
        printf("Got: %.*s\n", (int)read_size, read_data);
        free(read_data);
        bsfs_tenant_cleanup(&tenant);
        return;
    }
    
    printf("✓ Data verification passed\n");
    free(read_data);
    
    // Test file update (atomic)
    const char *updated_data = "Updated content! This should replace the old content atomically.";
    size_t updated_size = strlen(updated_data);
    
    if (bsfs_write_file(&tenant, file_id, (const uint8_t*)updated_data, updated_size) != 0) {
        printf("FAILED: Could not update file\n");
        bsfs_tenant_cleanup(&tenant);
        return;
    }
    
    printf("✓ File updated successfully\n");
    
    // Read updated file
    if (bsfs_read_file(&tenant, file_id, &read_data, &read_size) != 0) {
        printf("FAILED: Could not read updated file\n");
        bsfs_tenant_cleanup(&tenant);
        return;
    }
    
    // Verify updated data
    if (read_size != updated_size || memcmp(read_data, updated_data, updated_size) != 0) {
        printf("FAILED: Updated data verification failed\n");
        free(read_data);
        bsfs_tenant_cleanup(&tenant);
        return;
    }
    
    printf("✓ Updated data verification passed\n");
    free(read_data);
    
    // Test file deletion
    if (bsfs_delete_file(&tenant, file_id) != 0) {
        printf("FAILED: Could not delete file\n");
        bsfs_tenant_cleanup(&tenant);
        return;
    }
    
    printf("✓ File deleted successfully\n");
    
    // Verify file is gone
    if (bsfs_read_file(&tenant, file_id, &read_data, &read_size) == 0) {
        printf("FAILED: File should not exist after deletion\n");
        free(read_data);
        bsfs_tenant_cleanup(&tenant);
        return;
    }
    
    printf("✓ File deletion verified\n");
    
    bsfs_tenant_cleanup(&tenant);
    printf("✓ All basic operations passed!\n\n");
}

void test_large_file() {
    printf("Testing large file (multi-block)...\n");
    
    uint8_t master_key[BSFS_AES_KEY_SIZE];
    RAND_bytes(master_key, BSFS_AES_KEY_SIZE);
    
    bsfs_tenant_t tenant;
    if (bsfs_tenant_init(&tenant, "test_large.blob", master_key) != 0) {
        printf("FAILED: Could not initialize tenant\n");
        return;
    }
    
    // Create 5MB test data (spans multiple 2MB blocks)
    size_t large_size = 5 * 1024 * 1024;
    uint8_t *large_data = malloc(large_size);
    if (!large_data) {
        printf("FAILED: Could not allocate test data\n");
        bsfs_tenant_cleanup(&tenant);
        return;
    }
    
    // Fill with pattern
    for (size_t i = 0; i < large_size; i++) {
        large_data[i] = (uint8_t)(i % 256);
    }
    
    uuid_t file_id;
    uuid_generate(file_id);
    
    if (bsfs_write_file(&tenant, file_id, large_data, large_size) != 0) {
        printf("FAILED: Could not write large file\n");
        free(large_data);
        bsfs_tenant_cleanup(&tenant);
        return;
    }
    
    printf("✓ Large file written (5MB)\n");
    
    // Read back and verify
    uint8_t *read_data;
    size_t read_size;
    
    if (bsfs_read_file(&tenant, file_id, &read_data, &read_size) != 0) {
        printf("FAILED: Could not read large file\n");
        free(large_data);
        bsfs_tenant_cleanup(&tenant);
        return;
    }
    
    if (read_size != large_size || memcmp(read_data, large_data, large_size) != 0) {
        printf("FAILED: Large file verification failed\n");
        printf("Expected size: %zu, Got size: %zu\n", large_size, read_size);
        free(large_data);
        free(read_data);
        bsfs_tenant_cleanup(&tenant);
        return;
    }
    
    printf("✓ Large file verification passed\n");
    
    free(large_data);
    free(read_data);
    bsfs_tenant_cleanup(&tenant);
    printf("✓ Large file test passed!\n\n");
}

void test_multiple_files() {
    printf("Testing multiple files...\n");
    
    uint8_t master_key[BSFS_AES_KEY_SIZE];
    RAND_bytes(master_key, BSFS_AES_KEY_SIZE);
    
    bsfs_tenant_t tenant;
    if (bsfs_tenant_init(&tenant, "test_multi.blob", master_key) != 0) {
        printf("FAILED: Could not initialize tenant\n");
        return;
    }
    
    // Create 10 test files
    uuid_t file_ids[10];
    char test_contents[10][100];
    
    for (int i = 0; i < 10; i++) {
        uuid_generate(file_ids[i]);
        snprintf(test_contents[i], sizeof(test_contents[i]), 
                "This is test file #%d with unique content!", i);
        
        if (bsfs_write_file(&tenant, file_ids[i], 
                           (const uint8_t*)test_contents[i], 
                           strlen(test_contents[i])) != 0) {
            printf("FAILED: Could not write file #%d\n", i);
            bsfs_tenant_cleanup(&tenant);
            return;
        }
    }
    
    printf("✓ 10 files written\n");
    
    // Read and verify all files
    for (int i = 0; i < 10; i++) {
        uint8_t *read_data;
        size_t read_size;
        
        if (bsfs_read_file(&tenant, file_ids[i], &read_data, &read_size) != 0) {
            printf("FAILED: Could not read file #%d\n", i);
            bsfs_tenant_cleanup(&tenant);
            return;
        }
        
        if (read_size != strlen(test_contents[i]) || 
            memcmp(read_data, test_contents[i], read_size) != 0) {
            printf("FAILED: File #%d verification failed\n", i);
            free(read_data);
            bsfs_tenant_cleanup(&tenant);
            return;
        }
        
        free(read_data);
    }
    
    printf("✓ All 10 files verified\n");
    
    bsfs_tenant_cleanup(&tenant);
    printf("✓ Multiple files test passed!\n\n");
}

int main() {
    printf("BSFS Test Suite\n");
    printf("===============\n\n");
    
    test_basic_operations();
    test_large_file();
    test_multiple_files();
    
    printf("All tests completed!\n");
    return 0;
}