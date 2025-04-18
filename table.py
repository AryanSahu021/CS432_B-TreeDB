# table.py
import pickle
from typing import Dict, List, Tuple, Optional, Any
from bplustree import BPlusTree

class Table:
    def __init__(self, name: str, columns: Dict[str, type], primary_key: str):
        self.name = name
        self.columns = columns
        self.primary_key = primary_key
        self.index = BPlusTree(degree=3)  # Using our B+ Tree implementation
        self.serialized_file = f"{name}.pkl"
    
    def insert(self, record: Dict[str, Any]) -> bool:
        """Insert a record into the table."""
        if not all(col in record for col in self.columns):
            raise ValueError("Missing columns in record")
        
        pk_value = record[self.primary_key]
        if self.index.search(pk_value):
            return False  # Primary key already exists
        
        self.index.insert(pk_value, record)
        return True
    
    def select(self, primary_key_value) -> Optional[Dict[str, Any]]:
        """Select a record by primary key."""
        return self.index.get(primary_key_value)
    
    def update(self, primary_key_value, new_values: Dict[str, Any]) -> bool:
        """Update a record by primary key."""
        record = self.select(primary_key_value)
        if not record:
            return False
        
        for col, value in new_values.items():
            if col in record and col != self.primary_key:
                record[col] = value
        
        return self.index.update(primary_key_value, record)
    
    def delete(self, primary_key_value) -> bool:
        """Delete a record by primary key."""
        return self.index.delete(primary_key_value)
    
    def select_range(self, start_key, end_key) -> List[Dict[str, Any]]:
        """Select records within a range of primary keys."""
        return [value for key, value in self.index.range_query(start_key, end_key)]
    
    def select_all(self) -> List[Dict[str, Any]]:
        """Select all records in the table."""
        return [value for key, value in self.index.get_all()]
    
    def persist(self) -> None:
        """Persist the table to disk."""
        with open(self.serialized_file, 'wb') as f:
            pickle.dump({
                'name': self.name,
                'columns': self.columns,
                'primary_key': self.primary_key,
                'data': self.index.get_all()
            }, f)
    
    def load(self) -> bool:
        """Load the table from disk."""
        try:
            with open(self.serialized_file, 'rb') as f:
                data = pickle.load(f)
                self.name = data['name']
                self.columns = data['columns']
                self.primary_key = data['primary_key']
                
                # Rebuild the index
                self.index = BPlusTree(degree=3)
                for key, value in data['data']:
                    self.index.insert(key, value)
            return True
        except FileNotFoundError:
            return False
    
    def visualize_index(self) -> None:
        """Visualize the B+ tree index."""
        self.index.visualize_tree(f"{self.name}_index")