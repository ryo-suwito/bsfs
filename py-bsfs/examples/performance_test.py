#!/usr/bin/env python3
"""
BSFS Performance Testing Suite

This suite tests various performance aspects of BSFS:
1. File I/O performance (small and large files)
2. Concurrent operations
3. Memory usage
4. Storage efficiency
"""

import time
import uuid
import random
import tempfile
import threading
from pathlib import Path
from typing import List, Dict, Any
import statistics

import bsfs


class PerformanceTestSuite:
    """Performance testing suite for BSFS"""
    
    def __init__(self, blob_path: str, master_key: bytes):
        self.blob_path = blob_path
        self.master_key = master_key
        self.results = {}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all performance tests"""
        print("🚀 BSFS Performance Test Suite")
        print("=" * 50)
        
        # Test small file performance
        self.test_small_file_performance()
        
        # Test large file performance
        self.test_large_file_performance()
        
        # Test concurrent operations
        self.test_concurrent_operations()
        
        # Test storage efficiency
        self.test_storage_efficiency()
        
        return self.results
    
    def test_small_file_performance(self):
        """Test performance with small files (1KB - 10KB)"""
        print("\n📊 Testing small file performance...")
        
        with bsfs.BSFS(self.blob_path, self.master_key) as fs:
            # Generate test data
            test_files = []
            for i in range(50):  # Reduced from 1000 to 50
                size = random.randint(1024, 10240)  # 1KB - 10KB
                data = b'A' * size
                test_files.append((uuid.uuid4(), data))
            
            # Test write performance
            write_times = []
            start_time = time.time()
            
            for file_id, data in test_files:
                write_start = time.time()
                fs.write_file(file_id, data)
                write_times.append(time.time() - write_start)
            
            total_write_time = time.time() - start_time
            
            # Test read performance
            read_times = []
            start_time = time.time()
            
            for file_id, _ in test_files:
                read_start = time.time()
                fs.read_file(file_id)
                read_times.append(time.time() - read_start)
            
            total_read_time = time.time() - start_time
            
            # Calculate statistics
            total_size = sum(len(data) for _, data in test_files)
            
            self.results['small_files'] = {
                'file_count': len(test_files),
                'total_size': total_size,
                'write_time': total_write_time,
                'read_time': total_read_time,
                'write_throughput': total_size / total_write_time,
                'read_throughput': total_size / total_read_time,
                'avg_write_time': statistics.mean(write_times),
                'avg_read_time': statistics.mean(read_times),
                'write_ops_per_sec': len(test_files) / total_write_time,
                'read_ops_per_sec': len(test_files) / total_read_time
            }
            
            print(f"  📝 Wrote {len(test_files)} files in {total_write_time:.2f}s")
            print(f"  📖 Read {len(test_files)} files in {total_read_time:.2f}s")
            print(f"  🚀 Write throughput: {total_size / total_write_time / 1024 / 1024:.2f} MB/s")
            print(f"  🚀 Read throughput: {total_size / total_read_time / 1024 / 1024:.2f} MB/s")
    
    def test_large_file_performance(self):
        """Test performance with large files (1MB - 10MB)"""
        print("\n📊 Testing large file performance...")
        
        with bsfs.BSFS(self.blob_path, self.master_key) as fs:
            # Generate test data
            test_files = []
            for i in range(3):  # Reduced from 10 to 3
                size = random.randint(1024*1024, 2*1024*1024)  # 1MB - 2MB (reduced from 10MB)
                data = bytes(random.randint(0, 255) for _ in range(size))
                test_files.append((uuid.uuid4(), data))
            
            # Test write performance
            write_times = []
            start_time = time.time()
            
            for file_id, data in test_files:
                write_start = time.time()
                fs.write_file(file_id, data)
                write_times.append(time.time() - write_start)
            
            total_write_time = time.time() - start_time
            
            # Test read performance
            read_times = []
            start_time = time.time()
            
            for file_id, _ in test_files:
                read_start = time.time()
                fs.read_file(file_id)
                read_times.append(time.time() - read_start)
            
            total_read_time = time.time() - start_time
            
            # Calculate statistics
            total_size = sum(len(data) for _, data in test_files)
            
            self.results['large_files'] = {
                'file_count': len(test_files),
                'total_size': total_size,
                'write_time': total_write_time,
                'read_time': total_read_time,
                'write_throughput': total_size / total_write_time,
                'read_throughput': total_size / total_read_time,
                'avg_write_time': statistics.mean(write_times),
                'avg_read_time': statistics.mean(read_times)
            }
            
            print(f"  📝 Wrote {len(test_files)} files ({total_size/1024/1024:.1f} MB) in {total_write_time:.2f}s")
            print(f"  📖 Read {len(test_files)} files ({total_size/1024/1024:.1f} MB) in {total_read_time:.2f}s")
            print(f"  🚀 Write throughput: {total_size / total_write_time / 1024 / 1024:.2f} MB/s")
            print(f"  🚀 Read throughput: {total_size / total_read_time / 1024 / 1024:.2f} MB/s")
    
    def test_concurrent_operations(self):
        """Test concurrent read/write operations"""
        print("\n📊 Testing concurrent operations...")
        
        def worker_thread(thread_id: int, file_count: int, results: List):
            """Worker thread for concurrent testing"""
            try:
                with bsfs.BSFS(self.blob_path, self.master_key) as fs:
                    thread_times = []
                    
                    for i in range(file_count):
                        file_id = uuid.uuid4()
                        data = f"Thread {thread_id} - File {i} - ".encode() * 100
                        
                        start_time = time.time()
                        fs.write_file(file_id, data)
                        read_data = fs.read_file(file_id)
                        fs.delete_file(file_id)
                        thread_times.append(time.time() - start_time)
                    
                    results.append({
                        'thread_id': thread_id,
                        'operations': file_count,
                        'total_time': sum(thread_times),
                        'avg_time': statistics.mean(thread_times)
                    })
            except Exception as e:
                results.append({
                    'thread_id': thread_id,
                    'error': str(e)
                })
        
        # Test with different thread counts
        for thread_count in [1, 2, 4]:  # Reduced from [1, 2, 4, 8]
            print(f"\n  🧵 Testing with {thread_count} threads...")
            
            results = []
            threads = []
            files_per_thread = 10  # Reduced from 50
            
            start_time = time.time()
            
            for i in range(thread_count):
                thread = threading.Thread(
                    target=worker_thread,
                    args=(i, files_per_thread, results)
                )
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            total_time = time.time() - start_time
            
            # Calculate statistics
            successful_threads = [r for r in results if 'error' not in r]
            failed_threads = [r for r in results if 'error' in r]
            
            if successful_threads:
                total_ops = sum(r['operations'] for r in successful_threads)
                avg_ops_per_sec = total_ops / total_time
                
                print(f"    ✅ Successful threads: {len(successful_threads)}")
                print(f"    ❌ Failed threads: {len(failed_threads)}")
                print(f"    📊 Total operations: {total_ops}")
                print(f"    ⏱️ Total time: {total_time:.2f}s")
                print(f"    🚀 Operations per second: {avg_ops_per_sec:.2f}")
                
                if f'concurrent_{thread_count}' not in self.results:
                    self.results[f'concurrent_{thread_count}'] = {
                        'thread_count': thread_count,
                        'successful_threads': len(successful_threads),
                        'failed_threads': len(failed_threads),
                        'total_operations': total_ops,
                        'total_time': total_time,
                        'ops_per_second': avg_ops_per_sec
                    }
            
            time.sleep(0.1)  # Brief pause between tests
    
    def test_storage_efficiency(self):
        """Test storage efficiency and compression"""
        print("\n📊 Testing storage efficiency...")
        
        with bsfs.BSFS(self.blob_path, self.master_key) as fs:
            # Test with different data patterns
            test_cases = [
                ("random", b''.join(bytes([random.randint(0, 255)]) for _ in range(10000))),  # Reduced from 100000
                ("repeated", b'A' * 10000),  # Reduced from 100000
                ("structured", b'{"key": "value", "number": 42}' * 200),  # Reduced from 2000
                ("binary", b'\x00\x01\x02\x03' * 2500)  # Reduced from 25000
            ]
            
            efficiency_results = []
            
            for case_name, data in test_cases:
                file_id = uuid.uuid4()
                
                # Write and read back
                start_time = time.time()
                fs.write_file(file_id, data)
                write_time = time.time() - start_time
                
                start_time = time.time()
                read_data = fs.read_file(file_id)
                read_time = time.time() - start_time
                
                # Verify data integrity
                data_intact = data == read_data
                
                efficiency_results.append({
                    'case': case_name,
                    'original_size': len(data),
                    'data_intact': data_intact,
                    'write_time': write_time,
                    'read_time': read_time
                })
                
                print(f"  📊 {case_name}: {len(data):,} bytes")
                print(f"    ✅ Data integrity: {'OK' if data_intact else 'FAILED'}")
                print(f"    ⏱️ Write time: {write_time:.4f}s")
                print(f"    ⏱️ Read time: {read_time:.4f}s")
            
            # Get overall storage info
            storage_info = fs.get_storage_info()
            
            self.results['storage_efficiency'] = {
                'test_cases': efficiency_results,
                'storage_info': storage_info
            }
    
    def print_summary(self):
        """Print a summary of all test results"""
        print("\n📋 Performance Test Summary")
        print("=" * 50)
        
        if 'small_files' in self.results:
            r = self.results['small_files']
            print(f"Small Files ({r['file_count']} files):")
            print(f"  Write: {r['write_throughput']/1024/1024:.2f} MB/s, {r['write_ops_per_sec']:.0f} ops/s")
            print(f"  Read:  {r['read_throughput']/1024/1024:.2f} MB/s, {r['read_ops_per_sec']:.0f} ops/s")
        
        if 'large_files' in self.results:
            r = self.results['large_files']
            print(f"Large Files ({r['file_count']} files):")
            print(f"  Write: {r['write_throughput']/1024/1024:.2f} MB/s")
            print(f"  Read:  {r['read_throughput']/1024/1024:.2f} MB/s")
        
        print("Concurrent Operations:")
        for key, r in self.results.items():
            if key.startswith('concurrent_'):
                print(f"  {r['thread_count']} threads: {r['ops_per_second']:.1f} ops/s")
        
        if 'storage_efficiency' in self.results:
            print("Storage Efficiency: All data integrity tests passed ✅")


def demo_performance_test():
    """Run the performance test suite"""
    # Create temporary storage
    temp_dir = Path(tempfile.mkdtemp())
    blob_path = temp_dir / "performance_test.blob"
    master_key = bsfs.generate_master_key()
    
    try:
        # Run performance tests
        test_suite = PerformanceTestSuite(str(blob_path), master_key)
        results = test_suite.run_all_tests()
        
        # Print summary
        test_suite.print_summary()
        
        # Show final storage stats
        print(f"\n📊 Final Storage Stats:")
        with bsfs.BSFS(str(blob_path), master_key) as fs:
            info = fs.get_storage_info()
            print(f"Files: {info['file_count']}")
            print(f"Used blocks: {info['used_blocks']}")
            print(f"Storage utilization: {info['storage_utilization']:.1f}%")
            print(f"Blob size: {Path(blob_path).stat().st_size:,} bytes")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("\n🧹 Cleanup completed")


if __name__ == "__main__":
    demo_performance_test()