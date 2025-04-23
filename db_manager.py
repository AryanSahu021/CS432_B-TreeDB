# db_manager.py
import os
from typing import Dict, Optional, List
from table import Table

class Database:
    def __init__(self, name: str):
        self.name = name
        self.tables: Dict[str, Table] = {}
        self.db_dir = f"{name}_db"
        
        # Create database directory if it doesn't exist
        os.makedirs(self.db_dir, exist_ok=True)
    
    def create_table(self, name: str, columns: Dict[str, type], primary_key: str) -> bool:
        """Create a new table in the database."""
        if name in self.tables:
            return False
        
        self.tables[name] = Table(name, columns, primary_key)
        return True
    
    def delete_table(self, name: str) -> bool:
        """Delete a table from the database."""
        if name not in self.tables:
            return False
        
        # Remove the table file if it exists
        table_file = os.path.join(self.db_dir, f"{name}.pkl")
        if os.path.exists(table_file):
            os.remove(table_file)
        
        del self.tables[name]
        return True
    
    def get_table(self, name: str) -> Optional[Table]:
        """Get a table by name."""
        return self.tables.get(name)
    
    def list_tables(self) -> List[str]:
        """List all tables in the database."""
        return list(self.tables.keys())
    
    def persist(self) -> None:
        """Persist all tables to disk."""
        # First ensure the database directory exists
        os.makedirs(self.db_dir, exist_ok=True)
        
        # Save each table
        for table_name, table in self.tables.items():
            table.serialized_file = os.path.join(self.db_dir, f"{table_name}.pkl")
            table.persist()

    def load(self) -> bool:
        """Load all tables from disk."""
        try:
            # Clear existing tables
            self.tables.clear()
            
            # Get all .pkl files in the db directory
            if not os.path.exists(self.db_dir):
                return False
                
            table_files = [f for f in os.listdir(self.db_dir) if f.endswith('.pkl')]
            
            for table_file in table_files:
                table_name = table_file[:-4]  # Remove .pkl extension
                # Create temp table with proper file path
                temp_table = Table(table_name, {}, '')
                temp_table.serialized_file = os.path.join(self.db_dir, table_file)
                
                if temp_table.load():
                    # Create a new table with the loaded schema
                    self.tables[table_name] = Table(
                        name=temp_table.name,
                        columns=temp_table.columns,
                        primary_key=temp_table.primary_key
                    )
                    # Set the correct serialized file path
                    self.tables[table_name].serialized_file = os.path.join(self.db_dir, table_file)
                    # Copy the loaded index
                    self.tables[table_name].index = temp_table.index
            
            return True
        except Exception as e:
            print(f"Error loading database: {e}")
            return False