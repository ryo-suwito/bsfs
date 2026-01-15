import ctypes
from ctypes import c_char_p, c_uint8, c_size_t, c_int, POINTER, Structure, byref, create_string_buffer
import os
import uuid

# Define structures
class BSFS_BlockRef(Structure):
    _pack_ = 1
    _fields_ = [
        ("partition_id", c_uint8),
        ("block_id", c_uint8 * 2) # uint16_t
    ]

class BSFS_FileEntry(Structure):
    _pack_ = 1
    _fields_ = [
        ("file_id", c_uint8 * 16),
        ("file_size", c_uint8 * 4), # uint32_t
        ("block_count", c_uint8 * 2), # uint16_t
        ("blocks", BSFS_BlockRef * 256)
    ]

# Opaque pointer for bsfs_tenant_t
class BSFS_Tenant(Structure):
    pass

class BSFS:
    def __init__(self, lib_path="./libbsfs.so", blob_path="test_python.blob", master_key=b'x'*32):
        if not os.path.exists(lib_path):
            # Try looking in current directory
            lib_path = os.path.abspath(lib_path)

        self.lib = ctypes.CDLL(lib_path)
        self.tenant = BSFS_Tenant()
        self.blob_path = blob_path.encode('utf-8')
        self.master_key = master_key

        # Define function signatures
        self.lib.bsfs_tenant_init.argtypes = [POINTER(BSFS_Tenant), c_char_p, POINTER(c_uint8)]
        self.lib.bsfs_tenant_init.restype = c_int

        self.lib.bsfs_tenant_cleanup.argtypes = [POINTER(BSFS_Tenant)]
        self.lib.bsfs_tenant_cleanup.restype = None

        self.lib.bsfs_write_file.argtypes = [POINTER(BSFS_Tenant), POINTER(c_uint8), POINTER(c_uint8), c_size_t]
        self.lib.bsfs_write_file.restype = c_int

        self.lib.bsfs_read_file.argtypes = [POINTER(BSFS_Tenant), POINTER(c_uint8), POINTER(POINTER(c_uint8)), POINTER(c_size_t)]
        self.lib.bsfs_read_file.restype = c_int

        # Initialize tenant
        key_buf = (c_uint8 * 32)(*self.master_key)
        if self.lib.bsfs_tenant_init(byref(self.tenant), self.blob_path, key_buf) != 0:
            raise RuntimeError("Failed to initialize BSFS tenant")

    def close(self):
        self.lib.bsfs_tenant_cleanup(byref(self.tenant))

    def write_file(self, file_id_uuid, data):
        if isinstance(file_id_uuid, str):
            file_id_uuid = uuid.UUID(file_id_uuid)

        file_id_bytes = (c_uint8 * 16)(*file_id_uuid.bytes)
        data_bytes = (c_uint8 * len(data))(*data)

        if self.lib.bsfs_write_file(byref(self.tenant), file_id_bytes, data_bytes, len(data)) != 0:
            raise RuntimeError("Failed to write file")

    def read_file(self, file_id_uuid):
        if isinstance(file_id_uuid, str):
            file_id_uuid = uuid.UUID(file_id_uuid)

        file_id_bytes = (c_uint8 * 16)(*file_id_uuid.bytes)
        data_ptr = POINTER(c_uint8)()
        size = c_size_t()

        if self.lib.bsfs_read_file(byref(self.tenant), file_id_bytes, byref(data_ptr), byref(size)) != 0:
            raise RuntimeError("Failed to read file")

        # Copy data to Python bytes
        result = bytes(data_ptr[:size.value])

        # Free memory allocated by C library
        # Note: In a real wrapper, we should expose a free function or use libc free
        # For now, we rely on OS to reclaim if we don't expose free.
        # But wait, bsfs.c allocates with malloc. We must free it.
        # We can link libc to free it.
        libc = ctypes.CDLL("libc.so.6")
        libc.free(data_ptr)

        return result

if __name__ == "__main__":
    print("Testing Python wrapper...")
    bsfs = BSFS()

    fid = uuid.uuid4()
    data = b"Hello from Python!"

    print(f"Writing file {fid}...")
    bsfs.write_file(fid, data)

    print("Reading file...")
    read_data = bsfs.read_file(fid)
    print(f"Read: {read_data}")

    assert data == read_data

    bsfs.close()
    print("Python test passed!")
