#ifndef BSFS_H
#define BSFS_H

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <uuid/uuid.h>
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/kdf.h>
#include <openssl/crypto.h>

#define BSFS_BLOCK_SIZE_DEFAULT (2 * 1024 * 1024)  // 2MB
#define BSFS_BLOCKS_PER_PARTITION 1024
#define BSFS_MAX_PARTITIONS 256
#define BSFS_AES_KEY_SIZE 32  // 256 bits
#define BSFS_AES_IV_SIZE 16   // 128 bits
#define BSFS_UUID_SIZE 16
#define BSFS_MAX_FILE_BLOCKS 256

// Block reference: partition_id (1 byte) + block_id (2 bytes)
typedef struct {
    uint8_t partition_id;
    uint16_t block_id;
} __attribute__((packed)) bsfs_block_ref_t;

// File entry in BAT (binary format)
typedef struct {
    uuid_t file_id;
    uint32_t file_size;       // Actual file size in bytes
    uint16_t block_count;
    bsfs_block_ref_t blocks[BSFS_MAX_FILE_BLOCKS];
} __attribute__((packed)) bsfs_file_entry_t;

// BAT header (binary format)
typedef struct {
    uint32_t magic;           // 0x42534653 "BSFS"
    uint32_t version;         // 1
    uint32_t block_size;      // 2MB default
    uint32_t file_count;      // Number of files
    uint32_t free_block_count; // Number of free blocks
    uint64_t timestamp;       // Creation/modification time
    uint8_t partition_id;     // This partition's ID
    uint8_t reserved[7];      // Padding
} __attribute__((packed)) bsfs_bat_header_t;

// Complete BAT structure (encrypted as single blob)
typedef struct {
    bsfs_bat_header_t header;
    bsfs_file_entry_t files[64];  // Max files per partition
    uint16_t free_blocks[BSFS_BLOCKS_PER_PARTITION];  // Shuffled free list
    uint8_t padding[1024];  // Reduced padding
} __attribute__((packed)) bsfs_bat_t;

// Partition structure
typedef struct {
    uint8_t partition_id;
    FILE *blob_file;
    uint64_t partition_offset;
    uint32_t block_size;
    uint8_t encryption_key[BSFS_AES_KEY_SIZE];
    bsfs_bat_t *bat;
    int bat_dirty;
} bsfs_partition_t;

// Tenant context
typedef struct {
    char *blob_path;
    FILE *blob_file;
    uint8_t master_key[BSFS_AES_KEY_SIZE];
    bsfs_partition_t partitions[BSFS_MAX_PARTITIONS];
    int partition_count;
} bsfs_tenant_t;

// Function declarations
int bsfs_tenant_init(bsfs_tenant_t *tenant, const char *blob_path, const uint8_t *master_key);
void bsfs_tenant_cleanup(bsfs_tenant_t *tenant);
int bsfs_partition_init(bsfs_tenant_t *tenant, uint8_t partition_id);
int bsfs_derive_partition_key(const uint8_t *master_key, uint8_t partition_id, uint8_t *partition_key);
int bsfs_encrypt_bat(const bsfs_bat_t *bat, const uint8_t *key, uint8_t *encrypted_data, size_t *encrypted_size);
int bsfs_decrypt_bat(const uint8_t *encrypted_data, size_t encrypted_size, const uint8_t *key, bsfs_bat_t *bat);
int bsfs_allocate_blocks(bsfs_partition_t *partition, uint16_t count, uint16_t *block_ids);
int bsfs_free_blocks(bsfs_partition_t *partition, const uint16_t *block_ids, uint16_t count);
int bsfs_write_file(bsfs_tenant_t *tenant, const uuid_t file_id, const uint8_t *data, size_t size);
int bsfs_read_file(bsfs_tenant_t *tenant, const uuid_t file_id, uint8_t **data, size_t *size);
int bsfs_delete_file(bsfs_tenant_t *tenant, const uuid_t file_id);
int bsfs_save_bat(bsfs_partition_t *partition);
int bsfs_load_bat(bsfs_partition_t *partition);

#endif // BSFS_H