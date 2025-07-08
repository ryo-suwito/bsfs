#include "bsfs.h"
#include <stdio.h>

int main() {
    printf("sizeof(bsfs_bat_t): %zu\n", sizeof(bsfs_bat_t));
    printf("sizeof(bsfs_bat_header_t): %zu\n", sizeof(bsfs_bat_header_t));
    printf("sizeof(bsfs_file_entry_t): %zu\n", sizeof(bsfs_file_entry_t));
    printf("sizeof(bsfs_block_ref_t): %zu\n", sizeof(bsfs_block_ref_t));
    printf("sizeof(uuid_t): %zu\n", sizeof(uuid_t));
    printf("64 * sizeof(bsfs_file_entry_t): %zu\n", 64 * sizeof(bsfs_file_entry_t));
    printf("BSFS_BLOCKS_PER_PARTITION * sizeof(uint16_t): %zu\n", 1024 * sizeof(uint16_t));
    printf("Total calculated: %zu\n", sizeof(bsfs_bat_header_t) + 64 * sizeof(bsfs_file_entry_t) + 1024 * sizeof(uint16_t) + 1024);
    return 0;
}