#!/usr/bin/env python3
"""
BSFS JSON CRUD Demo - Demonstrates how to use BSFS for JSON document storage

This example shows how to:
1. Store JSON documents in BSFS
2. Create, Read, Update, Delete (CRUD) operations
3. Query and filter documents
4. Handle collections of documents
"""

import json
import uuid
import tempfile
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

import bsfs


class JsonBSFSStore:
    """A JSON document store built on top of BSFS"""
    
    def __init__(self, blob_path: str, master_key: bytes):
        self.blob_path = blob_path
        self.master_key = master_key
        self.fs = bsfs.BSFS(blob_path, master_key)
        
        # Special UUID for storing document index
        self.index_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
        
        # Load or create document index
        self.index = self._load_index()
    
    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """Load the document index from BSFS"""
        try:
            index_data = self.fs.read_file(self.index_id)
            return json.loads(index_data.decode())
        except bsfs.BSFSFileNotFoundError:
            # Create new index
            return {}
    
    def _save_index(self):
        """Save the document index to BSFS"""
        index_data = json.dumps(self.index, indent=2).encode()
        self.fs.write_file(self.index_id, index_data)
    
    def create_document(self, collection: str, document: Dict[str, Any]) -> str:
        """Create a new document in the specified collection"""
        doc_id = str(uuid.uuid4())
        
        # Add metadata
        document['_id'] = doc_id
        document['_collection'] = collection
        document['_created_at'] = datetime.now().isoformat()
        document['_updated_at'] = document['_created_at']
        
        # Store document
        doc_data = json.dumps(document, indent=2).encode()
        doc_uuid = uuid.UUID(doc_id)
        self.fs.write_file(doc_uuid, doc_data)
        
        # Update index
        if collection not in self.index:
            self.index[collection] = {}
        
        self.index[collection][doc_id] = {
            'id': doc_id,
            'created_at': document['_created_at'],
            'updated_at': document['_updated_at']
        }
        
        self._save_index()
        
        print(f"✅ Created document {doc_id} in collection '{collection}'")
        return doc_id
    
    def read_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Read a document by ID"""
        try:
            doc_uuid = uuid.UUID(doc_id)
            doc_data = self.fs.read_file(doc_uuid)
            document = json.loads(doc_data.decode())
            return document
        except bsfs.BSFSFileNotFoundError:
            return None
    
    def update_document(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """Update a document with new data"""
        document = self.read_document(doc_id)
        if not document:
            return False
        
        # Apply updates
        document.update(updates)
        document['_updated_at'] = datetime.now().isoformat()
        
        # Save updated document
        doc_data = json.dumps(document, indent=2).encode()
        doc_uuid = uuid.UUID(doc_id)
        self.fs.write_file(doc_uuid, doc_data)
        
        # Update index
        collection = document['_collection']
        if collection in self.index and doc_id in self.index[collection]:
            self.index[collection][doc_id]['updated_at'] = document['_updated_at']
            self._save_index()
        
        print(f"✅ Updated document {doc_id}")
        return True
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID"""
        document = self.read_document(doc_id)
        if not document:
            return False
        
        # Delete from BSFS
        doc_uuid = uuid.UUID(doc_id)
        self.fs.delete_file(doc_uuid)
        
        # Remove from index
        collection = document['_collection']
        if collection in self.index and doc_id in self.index[collection]:
            del self.index[collection][doc_id]
            
            # Remove empty collections
            if not self.index[collection]:
                del self.index[collection]
            
            self._save_index()
        
        print(f"✅ Deleted document {doc_id}")
        return True
    
    def list_collections(self) -> List[str]:
        """List all collections"""
        return list(self.index.keys())
    
    def list_documents(self, collection: str) -> List[Dict[str, Any]]:
        """List all documents in a collection"""
        if collection not in self.index:
            return []
        
        return list(self.index[collection].values())
    
    def find_documents(self, collection: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find documents matching a query"""
        if collection not in self.index:
            return []
        
        results = []
        for doc_id in self.index[collection]:
            document = self.read_document(doc_id)
            if document and self._matches_query(document, query):
                results.append(document)
        
        return results
    
    def _matches_query(self, document: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """Check if document matches query"""
        for key, value in query.items():
            if key not in document:
                return False
            
            if isinstance(value, dict):
                # Support for operators like {"$gt": 10}
                if '$gt' in value:
                    if not (key in document and document[key] > value['$gt']):
                        return False
                elif '$lt' in value:
                    if not (key in document and document[key] < value['$lt']):
                        return False
                elif '$contains' in value:
                    if not (key in document and value['$contains'] in str(document[key])):
                        return False
            else:
                # Exact match
                if document[key] != value:
                    return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        info = self.fs.get_storage_info()
        
        total_docs = sum(len(docs) for docs in self.index.values())
        
        return {
            'total_documents': total_docs,
            'total_collections': len(self.index),
            'collections': {name: len(docs) for name, docs in self.index.items()},
            'storage_info': info
        }
    
    def close(self):
        """Close the BSFS connection"""
        self.fs.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def demo_json_crud():
    """Demonstrate JSON CRUD operations"""
    print("🚀 BSFS JSON CRUD Demo")
    print("=" * 50)
    
    # Create temporary storage
    temp_dir = Path(tempfile.mkdtemp())
    blob_path = temp_dir / "json_demo.blob"
    master_key = bsfs.generate_master_key()
    
    try:
        with JsonBSFSStore(str(blob_path), master_key) as store:
            # Create some sample documents
            print("\n📝 Creating sample documents...")
            
            # Users collection
            user1_id = store.create_document('users', {
                'name': 'Alice Johnson',
                'email': 'alice@example.com',
                'age': 28,
                'role': 'developer'
            })
            
            user2_id = store.create_document('users', {
                'name': 'Bob Smith',
                'email': 'bob@example.com',
                'age': 35,
                'role': 'manager'
            })
            
            # Products collection
            product1_id = store.create_document('products', {
                'name': 'Laptop',
                'price': 999.99,
                'category': 'electronics',
                'stock': 50
            })
            
            product2_id = store.create_document('products', {
                'name': 'Book',
                'price': 19.99,
                'category': 'books',
                'stock': 100
            })
            
            # Orders collection
            order1_id = store.create_document('orders', {
                'user_id': user1_id,
                'product_id': product1_id,
                'quantity': 1,
                'total': 999.99,
                'status': 'pending'
            })
            
            print(f"\n📊 Collections: {store.list_collections()}")
            
            # Read operations
            print("\n📖 Reading documents...")
            user = store.read_document(user1_id)
            print(f"User: {user['name']} ({user['email']})")
            
            product = store.read_document(product1_id)
            print(f"Product: {product['name']} - ${product['price']}")
            
            # Update operations
            print("\n✏️ Updating documents...")
            store.update_document(user1_id, {'age': 29, 'role': 'senior_developer'})
            store.update_document(product1_id, {'stock': 45})
            
            # Query operations
            print("\n🔍 Querying documents...")
            
            # Find all users
            users = store.find_documents('users', {})
            print(f"All users: {len(users)}")
            for user in users:
                print(f"  - {user['name']} ({user['age']} years old)")
            
            # Find expensive products
            expensive_products = store.find_documents('products', {
                'price': {'$gt': 50}
            })
            print(f"Expensive products: {len(expensive_products)}")
            for product in expensive_products:
                print(f"  - {product['name']}: ${product['price']}")
            
            # Find developers
            developers = store.find_documents('users', {
                'role': {'$contains': 'developer'}
            })
            print(f"Developers: {len(developers)}")
            for dev in developers:
                print(f"  - {dev['name']} ({dev['role']})")
            
            # List operations
            print("\n📋 Listing documents...")
            for collection in store.list_collections():
                docs = store.list_documents(collection)
                print(f"{collection}: {len(docs)} documents")
                for doc in docs:
                    print(f"  - {doc['id']} (created: {doc['created_at']})")
            
            # Statistics
            print("\n📊 Storage statistics...")
            stats = store.get_stats()
            print(f"Total documents: {stats['total_documents']}")
            print(f"Total collections: {stats['total_collections']}")
            print(f"Collections: {stats['collections']}")
            print(f"Storage utilization: {stats['storage_info']['storage_utilization']:.1f}%")
            print(f"Used capacity: {stats['storage_info']['used_capacity']:,} bytes")
            
            # Delete operations
            print("\n🗑️ Deleting documents...")
            store.delete_document(order1_id)
            
            # Final stats
            print("\n📊 Final statistics...")
            final_stats = store.get_stats()
            print(f"Remaining documents: {final_stats['total_documents']}")
            print(f"Collections: {final_stats['collections']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if blob_path.exists():
            blob_path.unlink()
        temp_dir.rmdir()
        print("\n🧹 Cleanup completed")


if __name__ == "__main__":
    demo_json_crud()