#include "bsfs.h"
#include <stdio.h>
int main() { 
    printf("sizeof(bsfs_bat_t): 0\n", sizeof(bsfs_bat_t));
    printf("sizeof(bsfs_bat_header_t): 0\n", sizeof(bsfs_bat_header_t));
    printf("sizeof(bsfs_file_entry_t): 0\n", sizeof(bsfs_file_entry_t));
    printf("64 * sizeof(bsfs_file_entry_t): 0\n", 64 * sizeof(bsfs_file_entry_t));
    printf("BSFS_BLOCKS_PER_PARTITION * sizeof(uint16_t): 0\n", 1024 * sizeof(uint16_t));
    return 0;
}