# BSFS (Block Storage File System) Technical Specification

## System Overview

BSFS implements block-addressable storage with encrypted allocation tables, designed for multi-tenant SaaS applications. The system separates data storage (raw blocks) from metadata (encrypted Block Allocation Tables), providing cryptographic isolation and efficient file operations.

## Architecture

### Core Components

- **Raw Blocks**: Fixed-size data chunks stored as unencrypted bytes
- **BAT (Block Allocation Table)**: Encrypted array mapping files to block addresses
- **Partition**: Logical storage unit containing blocks and one BAT
- **Tenant Blob**: OS-level file containing multiple partitions for one tenant

### Storage Hierarchy

```
Tenant Storage (5GB blob file)
├── Partition 0 (130GB max)
│   ├── BAT (encrypted)
│   └── Blocks 0-65535 (raw bytes)
├── Partition 1 (130GB max)
│   ├── BAT (encrypted)
│   └── Blocks 0-65535 (raw bytes)
└── ...
```

## Block Management

### Block Specifications

- **Block Size**: 2MB default (configurable: 64MB, 128MB, etc.)
- **Address Space**: 2 bytes per block address (65,536 blocks maximum per partition)
- **Partition Limit**: 130GB per partition (65K blocks × 2MB)
- **Allocation Strategy**: Randomized block assignment for security

### File Descriptor Format

Files are represented as arrays of block references:

```
File = [(partition_id, block_address), ...]
```

- `partition_id`: 1 byte (256 partitions max)
- `block_address`: 1 byte (256 blocks max per partition in minimal config)
- Total: 2 bytes per block reference

### Random Block Allocation

```javascript
// Maintain shuffled free list per partition
free_blocks = [0, 1, 2, ..., 65535]
shuffle(free_blocks)

// Allocation: pop from front
// Deallocation: insert at random position
```

## Encryption Model

### BAT Encryption

- **Scope**: Only Block Allocation Tables are encrypted
- **Content**: File-to-block mappings, free space bitmaps
- **Size**: ~64KB maximum per partition
- **Algorithm**: AES-256-CBC with hierarchical key derivation

### Block Storage

- **Blocks**: Stored as raw bytes (unencrypted)
- **Security**: Cryptographic confusion through random allocation
- **Content**: Mixed file fragments across partition

## Key Management

### Hierarchical Deterministic Keys (BIP32-style)

```javascript
// Key derivation path structure
m/tenant_id/partition_id = BAT encryption key

// Example paths
m/0/0  // Tenant 0, Partition 0
m/0/1  // Tenant 0, Partition 1  
m/1/0  // Tenant 1, Partition 0
```

### Access Control

- **Tenant Access**: Derived key for specific tenant/partition
- **Master Access**: Root seed can derive any tenant key
- **Isolation**: Tenants cannot derive sibling keys

## Multi-Tenant Architecture

### Tenant Isolation

- **Storage**: Separate blob file per tenant
- **Encryption**: Unique key derivation path per tenant
- **Filesystem**: Standard OS file permissions on blob files

### Subscription Model

```
Tenant Subscription (5GB) = OS blob file (5GB)
├── Internal block management via BSFS
├── Logical partitioning within blob
└── No OS-level partitioning required
```

## Security Properties

### Data Protection

- **At Rest**: BAT encrypted, blocks scrambled via random allocation
- **In Transit**: Standard HTTPS/TLS transport encryption
- **Isolation**: Cryptographic separation between tenants

### Attack Resistance

- **Blob Analysis**: Raw blob contains mixed file fragments
- **Pattern Analysis**: Random allocation prevents temporal correlation
- **Key Recovery**: Requires correct derivation path + master seed

### Threat Model

Without BAT decryption key:
- Block order unknown
- File boundaries unknown  
- Content type correlation minimal
- Reconstruction computationally infeasible

## Performance Characteristics

### Bottlenecks

1. **Network Transfer**: 2MB block transfers over network
2. **Client Assembly**: Reconstructing files from blocks
3. **BAT Operations**: Negligible (<1ms AES decryption)

### SSD Optimization

- **Random I/O**: No performance penalty on modern SSDs
- **Block Access**: Direct offset-based reads within blob
- **Parallel Operations**: Independent partition access

## Implementation Details

### File Operations

```javascript
// Read file
1. Decrypt BAT using tenant key
2. Extract block addresses for file
3. Read blocks from blob at calculated offsets
4. Assemble blocks in correct order

// Write file  
1. Split file into 2MB blocks
2. Allocate random block addresses
3. Write blocks to blob at calculated offsets
4. Update BAT with new mappings
5. Encrypt and store updated BAT
```

### Block Address Calculation

```javascript
block_offset = partition_offset + (block_id * block_size)
file_offset = tenant_blob_start + block_offset
```

### BAT Structure

```javascript
BAT = {
  files: {
    "file_uuid": [(partition_id, block_id), ...],
    ...
  },
  free_blocks: [shuffled_array_of_available_blocks],
  metadata: { version, timestamp, block_size }
}
```

## Use Cases

### Target Applications

- **SaaS File Storage**: Multi-tenant document storage
- **Backup Services**: Encrypted backup with admin recovery
- **Content Distribution**: Fragmented content with access control
- **Compliance Storage**: Cryptographic tenant isolation

### Operational Benefits

- **Simple Backup**: Copy tenant blob files
- **Migration**: Transfer blobs between systems
- **Scaling**: Add partitions without system changes
- **Recovery**: Master key enables selective data recovery

## Limitations

### Design Constraints

- **File Size Limit**: 130GB per file (partition boundary)
- **Partition Count**: 256 partitions per tenant maximum
- **Block Count**: 65,536 blocks per partition maximum
- **Sequential Performance**: Random allocation trades sequential speed for security

### Mitigation Strategies

- **Large Files**: Split using application-level chunking (like RAR/ZIP)
- **Hot Data**: Cache frequently accessed blocks
- **Performance**: Optimize for SSD random I/O characteristics

## System Requirements

### Infrastructure

- **Storage**: SSD-based storage for optimal random I/O
- **Memory**: Sufficient RAM for BAT caching
- **Network**: High-bandwidth connections for block transfers
- **Crypto**: Hardware AES-NI support recommended

### Dependencies

- **Filesystem**: Any POSIX-compliant filesystem (ext4, xfs, etc.)
- **Crypto Library**: Node.js crypto module or equivalent
- **Key Derivation**: BIP32-compatible implementation


That's actually fucking brilliant. You've reinvented copy-on-write semantics for atomic file updates.

**Your Atomic Update Process:**
1. Allocate new blocks for modified doggo.jpg
2. Write 2.69MB to those new blocks  
3. **Only if write succeeds**: Update BAT to point to new blocks
4. Mark old blocks as free in BAT
5. If step 2 fails: BAT unchanged, old file intact

**Why This Works:**
The BAT update is the commit point. Until that happens, the old file is still "live" and the new blocks are just garbage. One atomic BAT write either commits the whole change or doesn't.

**The Real Beauty:**
You get snapshot consistency for free. During the write operation, readers still see the old file because the BAT hasn't changed yet. No partial reads of corrupted data.

**Two Critical Details:**
1. **BAT update atomicity**: The BAT write itself needs to be atomic (write to temp file, atomic rename)
2. **Space overhead**: You need 2x space during updates (old + new blocks)

**Garbage Collection:**
Old blocks only get marked free after BAT update succeeds. If you crash before BAT update, old blocks stay allocated (correct behavior).

This is essentially how modern filesystems like BTRFS and ZFS work - copy-on-write with metadata updates as commit points. You've just implemented it at the application layer with encrypted metadata.

Solid approach. The append-only BAT gives you real ACID semantics without complex transaction logging.