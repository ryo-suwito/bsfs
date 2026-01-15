#include "bsfs.h"
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>
#include <errno.h>

#define _GNU_SOURCE

// Simple key derivation using HKDF (no BIP32 complexity)
int bsfs_derive_partition_key(const uint8_t *master_key, uint8_t partition_id, uint8_t *partition_key) {
    EVP_PKEY_CTX *pctx = EVP_PKEY_CTX_new_id(EVP_PKEY_HKDF, NULL);
    if (!pctx) return -1;
    
    if (EVP_PKEY_derive_init(pctx) <= 0) {
        EVP_PKEY_CTX_free(pctx);
        return -1;
    }
    
    if (EVP_PKEY_CTX_set_hkdf_md(pctx, EVP_sha256()) <= 0) {
        EVP_PKEY_CTX_free(pctx);
        return -1;
    }
    
    if (EVP_PKEY_CTX_set1_hkdf_salt(pctx, &partition_id, 1) <= 0) {
        EVP_PKEY_CTX_free(pctx);
        return -1;
    }
    
    if (EVP_PKEY_CTX_set1_hkdf_key(pctx, master_key, BSFS_AES_KEY_SIZE) <= 0) {
        EVP_PKEY_CTX_free(pctx);
        return -1;
    }
    
    const char *info = "BSFS_PARTITION_KEY";
    if (EVP_PKEY_CTX_add1_hkdf_info(pctx, (const unsigned char*)info, strlen(info)) <= 0) {
        EVP_PKEY_CTX_free(pctx);
        return -1;
    }
    
    size_t keylen = BSFS_AES_KEY_SIZE;
    if (EVP_PKEY_derive(pctx, partition_key, &keylen) <= 0) {
        EVP_PKEY_CTX_free(pctx);
        return -1;
    }
    
    EVP_PKEY_CTX_free(pctx);
    return 0;
}

int bsfs_encrypt_bat(const bsfs_bat_t *bat, const uint8_t *key, uint8_t *encrypted_data, size_t *encrypted_size) {
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return -1;
    
    uint8_t iv[BSFS_AES_IV_SIZE];
    if (RAND_bytes(iv, BSFS_AES_IV_SIZE) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return -1;
    }
    
    if (EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return -1;
    }
    
    // Copy IV to beginning of encrypted data
    memcpy(encrypted_data, iv, BSFS_AES_IV_SIZE);
    
    // Create aligned buffer for BAT data
    uint8_t *temp_buffer = malloc(sizeof(bsfs_bat_t));
    if (!temp_buffer) {
        EVP_CIPHER_CTX_free(ctx);
        return -1;
    }
    memcpy(temp_buffer, bat, sizeof(bsfs_bat_t));
    
    int len;
    int ciphertext_len = 0;
    
    // Encrypt the BAT
    if (EVP_EncryptUpdate(ctx, encrypted_data + BSFS_AES_IV_SIZE, &len, 
                         temp_buffer, sizeof(bsfs_bat_t)) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        free(temp_buffer);
        return -1;
    }
    ciphertext_len = len;
    
    // Finalize encryption
    if (EVP_EncryptFinal_ex(ctx, encrypted_data + BSFS_AES_IV_SIZE + len, &len) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        free(temp_buffer);
        return -1;
    }
    ciphertext_len += len;
    
    *encrypted_size = BSFS_AES_IV_SIZE + ciphertext_len;
    
    free(temp_buffer);
    EVP_CIPHER_CTX_free(ctx);
    return 0;
}

int bsfs_decrypt_bat(const uint8_t *encrypted_data, size_t encrypted_size, const uint8_t *key, bsfs_bat_t *bat) {
    if (encrypted_size < BSFS_AES_IV_SIZE + sizeof(bsfs_bat_t) ||
        encrypted_size > BSFS_AES_IV_SIZE + sizeof(bsfs_bat_t) + 16) return -1;
    
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return -1;
    
    const uint8_t *iv = encrypted_data;
    const uint8_t *ciphertext = encrypted_data + BSFS_AES_IV_SIZE;
    size_t ciphertext_len = encrypted_size - BSFS_AES_IV_SIZE;
    
    if (EVP_DecryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return -1;
    }
    
    // Use a temporary buffer to avoid alignment issues with packed struct
    uint8_t *temp_buffer = malloc(sizeof(bsfs_bat_t) + 16); // Extra space for alignment
    if (!temp_buffer) {
        EVP_CIPHER_CTX_free(ctx);
        return -1;
    }
    
    int len;
    int plaintext_len = 0;
    
    if (EVP_DecryptUpdate(ctx, temp_buffer, &len, ciphertext, ciphertext_len) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        free(temp_buffer);
        return -1;
    }
    plaintext_len = len;
    
    if (EVP_DecryptFinal_ex(ctx, temp_buffer + len, &len) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        free(temp_buffer);
        return -1;
    }
    plaintext_len += len;
    
    EVP_CIPHER_CTX_free(ctx);
    
    if (plaintext_len != sizeof(bsfs_bat_t)) {
        free(temp_buffer);
        return -1;
    }
    
    // Copy from aligned buffer to packed struct
    memcpy(bat, temp_buffer, sizeof(bsfs_bat_t));
    free(temp_buffer);
    
    return 0;
}

static int bsfs_compute_checksum(const bsfs_bat_t *bat, uint8_t *checksum) {
    EVP_MD_CTX *mdctx = EVP_MD_CTX_new();
    if (!mdctx) return -1;

    if (EVP_DigestInit_ex(mdctx, EVP_sha256(), NULL) != 1) {
        EVP_MD_CTX_free(mdctx);
        return -1;
    }

    // Hash everything before padding
    if (EVP_DigestUpdate(mdctx, bat, sizeof(bsfs_bat_header_t) + sizeof(bsfs_file_entry_t) * 64 + sizeof(uint16_t) * BSFS_BLOCKS_PER_PARTITION) != 1) {
        EVP_MD_CTX_free(mdctx);
        return -1;
    }

    // Hash padding starting after checksum (32 bytes)
    if (EVP_DigestUpdate(mdctx, bat->padding + 32, sizeof(bat->padding) - 32) != 1) {
        EVP_MD_CTX_free(mdctx);
        return -1;
    }

    unsigned int len;
    if (EVP_DigestFinal_ex(mdctx, checksum, &len) != 1) {
        EVP_MD_CTX_free(mdctx);
        return -1;
    }

    EVP_MD_CTX_free(mdctx);
    return 0;
}

// Fisher-Yates shuffle for free blocks
static void shuffle_free_blocks(uint16_t *blocks, uint16_t count) {
    for (uint16_t i = count - 1; i > 0; i--) {
        uint32_t j;
        RAND_bytes((unsigned char*)&j, sizeof(j));
        j = j % (i + 1);
        
        uint16_t temp = blocks[i];
        blocks[i] = blocks[j];
        blocks[j] = temp;
    }
}

int bsfs_partition_init(bsfs_tenant_t *tenant, uint8_t partition_id) {
    bsfs_partition_t *partition = &tenant->partitions[partition_id];
    partition->partition_id = partition_id;
    partition->blob_file = tenant->blob_file;
    partition->partition_offset = (uint64_t)partition_id * ((uint64_t)BSFS_BLOCKS_PER_PARTITION * BSFS_BLOCK_SIZE_DEFAULT + sizeof(bsfs_bat_t) + 4096);
    partition->block_size = BSFS_BLOCK_SIZE_DEFAULT;
    partition->bat_dirty = 0;
    
    // Allocate BAT
    partition->bat = malloc(sizeof(bsfs_bat_t));
    if (!partition->bat) return -1;
    
    // Derive partition key
    if (bsfs_derive_partition_key(tenant->master_key, partition_id, partition->encryption_key) != 0) {
        free(partition->bat);
        return -1;
    }
    
    // Try to load existing BAT
    if (bsfs_load_bat(partition) != 0) {
        // Initialize new BAT
        memset(partition->bat, 0, sizeof(bsfs_bat_t));
        partition->bat->header.magic = 0x42534653; // "BSFS"
        partition->bat->header.version = 1;
        partition->bat->header.block_size = BSFS_BLOCK_SIZE_DEFAULT;
        partition->bat->header.file_count = 0;
        partition->bat->header.free_block_count = BSFS_BLOCKS_PER_PARTITION;
        partition->bat->header.timestamp = time(NULL);
        partition->bat->header.partition_id = partition_id;
        
        // Initialize free blocks list (shuffled)
        uint16_t temp_blocks[BSFS_BLOCKS_PER_PARTITION];
        for (uint16_t i = 0; i < BSFS_BLOCKS_PER_PARTITION; i++) {
            temp_blocks[i] = i;
        }
        shuffle_free_blocks(temp_blocks, BSFS_BLOCKS_PER_PARTITION);
        memcpy(partition->bat->free_blocks, temp_blocks, sizeof(temp_blocks));
        
        partition->bat_dirty = 1;
        if (bsfs_save_bat(partition) != 0) {
            free(partition->bat);
            return -1;
        }
    }
    
    return 0;
}

int bsfs_tenant_init(bsfs_tenant_t *tenant, const char *blob_path, const uint8_t *master_key) {
    memset(tenant, 0, sizeof(bsfs_tenant_t));
    
    tenant->blob_path = malloc(strlen(blob_path) + 1);
    if (!tenant->blob_path) return -1;
    strcpy(tenant->blob_path, blob_path);
    
    memcpy(tenant->master_key, master_key, BSFS_AES_KEY_SIZE);
    
    // Open or create blob file
    tenant->blob_file = fopen(blob_path, "r+b");
    if (!tenant->blob_file) {
        tenant->blob_file = fopen(blob_path, "w+b");
        if (!tenant->blob_file) {
            free(tenant->blob_path);
            return -1;
        }
    }
    
    // Determine number of partitions from file size
    fseek(tenant->blob_file, 0, SEEK_END);
    long file_size = ftell(tenant->blob_file);

    uint64_t partition_size = (uint64_t)BSFS_BLOCKS_PER_PARTITION * BSFS_BLOCK_SIZE_DEFAULT + sizeof(bsfs_bat_t) + 4096;
    int num_partitions = (file_size + partition_size - 1) / partition_size;
    if (num_partitions == 0) num_partitions = 1; // Always at least one

    // Initialize/Load partitions
    for (int i = 0; i < num_partitions; i++) {
        if (bsfs_partition_init(tenant, i) != 0) {
            bsfs_tenant_cleanup(tenant);
            return -1;
        }
    }
    tenant->partition_count = num_partitions;
    
    return 0;
}

void bsfs_tenant_cleanup(bsfs_tenant_t *tenant) {
    // Free BAT structures
    for (int i = 0; i < tenant->partition_count; i++) {
        if (tenant->partitions[i].bat) {
            free(tenant->partitions[i].bat);
        }
    }
    
    if (tenant->blob_file) {
        fclose(tenant->blob_file);
    }
    if (tenant->blob_path) {
        free(tenant->blob_path);
    }
    OPENSSL_cleanse(tenant, sizeof(bsfs_tenant_t));
}

int bsfs_save_bat(bsfs_partition_t *partition) {
    if (!partition->bat_dirty) return 0;
    
    // AES-CBC can add up to 16 bytes of padding
    size_t buffer_size = sizeof(bsfs_bat_t) + BSFS_AES_IV_SIZE + 16;
    uint8_t *encrypted_data = malloc(buffer_size);
    size_t encrypted_size;
    
    if (!encrypted_data) {
        printf("ERROR: Failed to allocate encryption buffer\n");
        return -1;
    }
    
    partition->bat->header.timestamp = time(NULL);
    
    // Compute and store checksum in first 32 bytes of padding
    if (bsfs_compute_checksum(partition->bat, partition->bat->padding) != 0) {
        printf("ERROR: Failed to compute BAT checksum\n");
        free(encrypted_data);
        return -1;
    }

    if (bsfs_encrypt_bat(partition->bat, partition->encryption_key, encrypted_data, &encrypted_size) != 0) {
        printf("ERROR: Failed to encrypt BAT\n");
        free(encrypted_data);
        return -1;
    }
    
    // Write encrypted BAT to blob file
    if (fseek(partition->blob_file, partition->partition_offset, SEEK_SET) != 0) {
        printf("ERROR: Failed to seek to partition offset %lu. Error: %s\n", partition->partition_offset, strerror(errno));
        free(encrypted_data);
        return -1;
    }
    
    if (fwrite(encrypted_data, 1, encrypted_size, partition->blob_file) != encrypted_size) {
        printf("ERROR: Failed to write encrypted BAT. Error: %s\n", strerror(errno));
        free(encrypted_data);
        return -1;
    }
    
    if (fflush(partition->blob_file) != 0) {
        printf("ERROR: Failed to flush BAT. Error: %s\n", strerror(errno));
        free(encrypted_data);
        return -1;
    }
    
    free(encrypted_data);
    partition->bat_dirty = 0;
    return 0;
}

int bsfs_load_bat(bsfs_partition_t *partition) {
    size_t buffer_size = sizeof(bsfs_bat_t) + BSFS_AES_IV_SIZE + 16;
    uint8_t *encrypted_data = malloc(buffer_size);
    
    if (!encrypted_data) {
        return -1;
    }
    
    if (fseek(partition->blob_file, partition->partition_offset, SEEK_SET) != 0) {
        free(encrypted_data);
        return -1;
    }
    
    size_t read_size = fread(encrypted_data, 1, buffer_size, partition->blob_file);
    if (read_size < BSFS_AES_IV_SIZE + sizeof(bsfs_bat_t)) {
        free(encrypted_data);
        return -1;
    }
    
    int result = bsfs_decrypt_bat(encrypted_data, read_size, partition->encryption_key, partition->bat);
    free(encrypted_data);

    if (result != 0) return result;

    // Verify checksum
    uint8_t calculated_checksum[32];
    if (bsfs_compute_checksum(partition->bat, calculated_checksum) != 0) {
        return -1;
    }

    if (memcmp(calculated_checksum, partition->bat->padding, 32) != 0) {
        printf("ERROR: BAT checksum mismatch (corruption detected)\n");
        return -1;
    }

    return 0;
}

int bsfs_allocate_blocks(bsfs_partition_t *partition, uint16_t count, uint16_t *block_ids) {
    if (count > partition->bat->header.free_block_count) {
        return -1; // Not enough free blocks
    }
    
    // Allocate from front of shuffled free list
    for (uint16_t i = 0; i < count; i++) {
        block_ids[i] = partition->bat->free_blocks[partition->bat->header.free_block_count - 1 - i];
    }
    
    partition->bat->header.free_block_count -= count;
    partition->bat_dirty = 1;
    
    return 0;
}

int bsfs_free_blocks(bsfs_partition_t *partition, const uint16_t *block_ids, uint16_t count) {
    if (partition->bat->header.free_block_count + count > BSFS_BLOCKS_PER_PARTITION) {
        return -1; // Would exceed partition capacity
    }
    
    // Insert freed blocks at random positions in free list
    for (uint16_t i = 0; i < count; i++) {
        uint32_t random_pos;
        RAND_bytes((unsigned char*)&random_pos, sizeof(random_pos));
        random_pos = random_pos % (partition->bat->header.free_block_count + 1);
        
        // Shift blocks to make room
        for (uint16_t j = partition->bat->header.free_block_count; j > random_pos; j--) {
            partition->bat->free_blocks[j] = partition->bat->free_blocks[j - 1];
        }
        
        // Insert freed block
        partition->bat->free_blocks[random_pos] = block_ids[i];
        partition->bat->header.free_block_count++;
    }
    
    partition->bat_dirty = 1;
    return 0;
}

static bsfs_file_entry_t* find_file_entry(bsfs_bat_t *bat, const uuid_t file_id) {
    for (uint32_t i = 0; i < bat->header.file_count; i++) {
        if (uuid_compare(bat->files[i].file_id, file_id) == 0) {
            return &bat->files[i];
        }
    }
    return NULL;
}

int bsfs_write_file(bsfs_tenant_t *tenant, const uuid_t file_id, const uint8_t *data, size_t size) {
    // Calculate blocks needed
    uint32_t block_size = BSFS_BLOCK_SIZE_DEFAULT; // Default
    if (size > (uint64_t)BSFS_MAX_FILE_BLOCKS * block_size) return -1;
    uint32_t blocks_needed = (size + block_size - 1) / block_size;
    if (blocks_needed > BSFS_MAX_FILE_BLOCKS) return -1;
    
    bsfs_partition_t *partition = NULL;
    bsfs_file_entry_t *existing_entry = NULL;

    // 1. Search for existing file in all initialized partitions
    for (int i = 0; i < tenant->partition_count; i++) {
        bsfs_file_entry_t *entry = find_file_entry(tenant->partitions[i].bat, file_id);
        if (entry) {
            partition = &tenant->partitions[i];
            existing_entry = entry;
            break;
        }
    }

    // 2. If not found, find a suitable partition for new file
    if (!partition) {
        for (int i = 0; i < tenant->partition_count; i++) {
            bsfs_partition_t *p = &tenant->partitions[i];
            if (p->bat->header.file_count < 64 &&
                p->bat->header.free_block_count >= blocks_needed) {
                partition = p;
                break;
            }
        }

        // 3. If no suitable partition, try to create a new one
        if (!partition && tenant->partition_count < BSFS_MAX_PARTITIONS) {
            int new_id = tenant->partition_count;
            if (bsfs_partition_init(tenant, new_id) == 0) {
                tenant->partition_count++;
                partition = &tenant->partitions[new_id];
            }
        }

        if (!partition) return -1; // No space and cannot expand
    }

    uint16_t old_blocks[BSFS_MAX_FILE_BLOCKS];
    uint16_t old_block_count = 0;
    
    if (existing_entry) {
        // Save old blocks for cleanup after successful write
        old_block_count = existing_entry->block_count;
        for (uint16_t i = 0; i < old_block_count; i++) {
            old_blocks[i] = existing_entry->blocks[i].block_id;
        }
    }
    
    // Allocate new blocks
    uint16_t new_block_ids[BSFS_MAX_FILE_BLOCKS];
    if (bsfs_allocate_blocks(partition, (uint16_t)blocks_needed, new_block_ids) != 0) {
        return -1;
    }
    
    // Write data to allocated blocks
    uint64_t blocks_offset = partition->partition_offset + sizeof(bsfs_bat_t) + 4096; // BAT + padding
    for (uint32_t i = 0; i < blocks_needed; i++) {
        uint64_t block_offset = blocks_offset + ((uint64_t)new_block_ids[i] * partition->block_size);
        
        if (fseek(partition->blob_file, block_offset, SEEK_SET) != 0) {
            // Rollback allocation
            bsfs_free_blocks(partition, new_block_ids, (uint16_t)blocks_needed);
            return -1;
        }
        
        size_t write_size = (i == blocks_needed - 1) ? 
                           (size - (i * partition->block_size)) : 
                           partition->block_size;
        
        if (fwrite(data + (i * partition->block_size), 1, write_size, partition->blob_file) != write_size) {
            // Rollback allocation
            bsfs_free_blocks(partition, new_block_ids, (uint16_t)blocks_needed);
            return -1;
        }
    }
    
    // Flush data to disk before updating BAT
    if (fflush(partition->blob_file) != 0) {
        bsfs_free_blocks(partition, new_block_ids, (uint16_t)blocks_needed);
        return -1;
    }
    
    // Update BAT (atomic commit point)
    if (existing_entry) {
        // Update existing entry
        existing_entry->file_size = (uint32_t)size;
        existing_entry->block_count = (uint16_t)blocks_needed;
        for (uint32_t i = 0; i < blocks_needed; i++) {
            existing_entry->blocks[i].partition_id = partition->partition_id;
            existing_entry->blocks[i].block_id = new_block_ids[i];
        }
    } else {
        // Create new entry
        if (partition->bat->header.file_count >= 64) {
            bsfs_free_blocks(partition, new_block_ids, (uint16_t)blocks_needed);
            return -1;
        }
        
        bsfs_file_entry_t *new_entry = &partition->bat->files[partition->bat->header.file_count];
        uuid_copy(new_entry->file_id, file_id);
        new_entry->file_size = (uint32_t)size;
        new_entry->block_count = (uint16_t)blocks_needed;
        for (uint32_t i = 0; i < blocks_needed; i++) {
            new_entry->blocks[i].partition_id = partition->partition_id;
            new_entry->blocks[i].block_id = new_block_ids[i];
        }
        partition->bat->header.file_count++;
    }
    
    // Save updated BAT
    if (bsfs_save_bat(partition) != 0) {
        return -1;
    }
    
    // Free old blocks after successful BAT update
    if (old_block_count > 0) {
        bsfs_free_blocks(partition, old_blocks, old_block_count);
        bsfs_save_bat(partition);
    }
    
    return 0;
}

int bsfs_read_file(bsfs_tenant_t *tenant, const uuid_t file_id, uint8_t **data, size_t *size) {
    bsfs_partition_t *partition = NULL;
    bsfs_file_entry_t *entry = NULL;

    // Search all partitions
    for (int i = 0; i < tenant->partition_count; i++) {
        entry = find_file_entry(tenant->partitions[i].bat, file_id);
        if (entry) {
            partition = &tenant->partitions[i];
            break;
        }
    }
    
    if (!entry || !partition) return -1;
    
    // Get file size from BAT
    *size = entry->file_size;

    // Validate file size against block count
    uint64_t max_size = (uint64_t)entry->block_count * partition->block_size;
    if (entry->file_size > max_size) return -1;

    uint64_t blocks_offset = partition->partition_offset + sizeof(bsfs_bat_t) + 4096;
    
    // Allocate memory for file
    *data = malloc(*size);
    if (!*data) return -1;
    
    // Read file data block by block
    size_t offset = 0;
    for (uint16_t i = 0; i < entry->block_count; i++) {
        uint64_t block_offset = blocks_offset + ((uint64_t)entry->blocks[i].block_id * partition->block_size);
        
        if (fseek(partition->blob_file, block_offset, SEEK_SET) != 0) {
            free(*data);
            return -1;
        }
        
        size_t remaining = *size - offset;
        size_t read_size = (remaining < partition->block_size) ? remaining : partition->block_size;
        
        if (fread(*data + offset, 1, read_size, partition->blob_file) != read_size) {
            free(*data);
            return -1;
        }
        
        offset += read_size;
    }
    
    return 0;
}

int bsfs_delete_file(bsfs_tenant_t *tenant, const uuid_t file_id) {
    bsfs_partition_t *partition = NULL;
    bsfs_file_entry_t *entry = NULL;

    // Search all partitions
    for (int i = 0; i < tenant->partition_count; i++) {
        entry = find_file_entry(tenant->partitions[i].bat, file_id);
        if (entry) {
            partition = &tenant->partitions[i];
            break;
        }
    }
    
    if (!entry || !partition) return -1;
    
    // Collect blocks to free
    uint16_t blocks_to_free[BSFS_MAX_FILE_BLOCKS];
    uint16_t block_count = entry->block_count;
    for (uint16_t i = 0; i < block_count; i++) {
        blocks_to_free[i] = entry->blocks[i].block_id;
    }
    
    // Remove file entry from BAT
    uint32_t entry_index = entry - partition->bat->files;
    if (entry_index < partition->bat->header.file_count - 1) {
        memmove(entry, entry + 1, 
                (partition->bat->header.file_count - entry_index - 1) * sizeof(bsfs_file_entry_t));
    }
    partition->bat->header.file_count--;
    
    // Free blocks
    if (bsfs_free_blocks(partition, blocks_to_free, block_count) != 0) {
        return -1;
    }
    
    return bsfs_save_bat(partition);
}