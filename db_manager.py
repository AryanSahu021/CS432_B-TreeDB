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
        for table in self.tables.values():
            table.persist()
    
    def load(self) -> bool:
        """Load all tables from disk."""
        # Get all .pkl files in the db directory
        try:
            table_files = [f for f in os.listdir(self.db_dir) if f.endswith('.pkl')]
            
            for table_file in table_files:
                table_name = table_file[:-4]  # Remove .pkl extension
                temp_table = Table(table_name, {}, '')  # Create temp table to load
                if temp_table.load():
                    # After loading, we can get the actual columns and primary key
                    first_record = temp_table.select_all()[0] if temp_table.select_all() else None
                    if first_record:
                        columns = {k: type(v) for k, v in first_record.items()}
                        # Need to determine primary key - this is a limitation of this simple implementation
                        # In a real system, we would store the schema separately
                        primary_key = list(columns.keys())[0]  # Just use the first column as PK
                        self.tables[table_name] = Table(table_name, columns, primary_key)
                        self.tables[table_name].index = temp_table.index
            return True
        except Exception as e:
            print(f"Error loading database: {e}")
            return False