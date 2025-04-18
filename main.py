# main.py
from db_manager import Database
from table import Table
import cmd
import sys

class DBShell(cmd.Cmd):
    intro = "Welcome to the Lightweight DBMS. Type 'help' for commands."
    prompt = "DB> "
    
    def __init__(self, db_name):
        super().__init__()
        self.db = Database(db_name)
        self.db.load()
        self.current_table = None
    
    def do_create_table(self, arg):
        """
        Create a new table: create_table <name> <col1:type1,col2:type2,...> <primary_key>
        Example: create_table users id:int,name:str,age:int id
        """
        args = arg.split()
        if len(args) != 3:
            print("Usage: create_table <name> <col1:type1,col2:type2,...> <primary_key>")
            return
        
        name = args[0]
        columns = {}
        for col_def in args[1].split(','):
            col_name, col_type = col_def.split(':')
            if col_type == 'int':
                col_type = int
            elif col_type == 'str':
                col_type = str
            elif col_type == 'float':
                col_type = float
            else:
                print(f"Unsupported type: {col_type}")
                return
            columns[col_name] = col_type
        
        primary_key = args[2]
        
        if self.db.create_table(name, columns, primary_key):
            print(f"Table '{name}' created successfully.")
        else:
            print(f"Table '{name}' already exists.")
    
    def do_use(self, arg):
        """
        Select a table to work with: use <table_name>
        """
        if not arg:
            print("Usage: use <table_name>")
            return
        
        table = self.db.get_table(arg)
        if table:
            self.current_table = table
            print(f"Using table '{arg}'")
        else:
            print(f"Table '{arg}' not found.")
    
    def do_insert(self, arg):
        """
        Insert a record into the current table: insert <col1=val1,col2=val2,...>
        Example: insert id=1,name="John Doe",age=30
        """
        if not self.current_table:
            print("No table selected. Use 'use <table_name>' first.")
            return
        
        record = {}
        for pair in arg.split(','):
            key, value = pair.split('=')
            col_type = self.current_table.columns[key]
            try:
                if col_type == int:
                    record[key] = int(value)
                elif col_type == float:
                    record[key] = float(value)
                else:  # str
                    record[key] = value.strip('"\'')
            except ValueError:
                print(f"Invalid value for column {key}. Expected {col_type.__name__}.")
                return
        
        if self.current_table.insert(record):
            print("Record inserted successfully.")
        else:
            print("Failed to insert record (duplicate primary key?).")
    
    def do_select(self, arg):
        """
        Select records: select [<primary_key_value> | range <start> <end> | all]
        Examples:
          select 42
          select range 10 20
          select all
        """
        if not self.current_table:
            print("No table selected. Use 'use <table_name>' first.")
            return
        
        args = arg.split()
        if not args:
            print("Usage: select [<primary_key_value> | range <start> <end> | all]")
            return
        
        if args[0] == 'all':
            records = self.current_table.select_all()
            for record in records:
                print(record)
        elif args[0] == 'range' and len(args) == 3:
            try:
                start = int(args[1])
                end = int(args[2])
                records = self.current_table.select_range(start, end)
                for record in records:
                    print(record)
            except ValueError:
                print("Range values must be integers for this implementation.")
        else:
            try:
                key = int(arg) if self.current_table.columns[self.current_table.primary_key] == int else arg
                record = self.current_table.select(key)
                if record:
                    print(record)
                else:
                    print("Record not found.")
            except ValueError:
                print("Invalid key format.")
    
    def do_update(self, arg):
        """
        Update a record: update <primary_key_value> <col1=val1,col2=val2,...>
        Example: update 1 age=31,name="John Smith"
        """
        if not self.current_table:
            print("No table selected. Use 'use <table_name>' first.")
            return
        
        args = arg.split(maxsplit=1)
        if len(args) < 2:
            print("Usage: update <primary_key_value> <col1=val1,col2=val2,...>")
            return
        
        pk_value = args[0]
        new_values = {}
        for pair in args[1].split(','):
            key, value = pair.split('=')
            if key == self.current_table.primary_key:
                print("Cannot update primary key.")
                return
            if key not in self.current_table.columns:
                print(f"Column '{key}' not found.")
                return
            
            col_type = self.current_table.columns[key]
            try:
                if col_type == int:
                    new_values[key] = int(value)
                elif col_type == float:
                    new_values[key] = float(value)
                else:  # str
                    new_values[key] = value.strip('"\'')
            except ValueError:
                print(f"Invalid value for column {key}. Expected {col_type.__name__}.")
                return
        
        if self.current_table.update(pk_value, new_values):
            print("Record updated successfully.")
        else:
            print("Record not found.")
    
    def do_delete(self, arg):
        """
        Delete a record: delete <primary_key_value>
        """
        if not self.current_table:
            print("No table selected. Use 'use <table_name>' first.")
            return
        
        if not arg:
            print("Usage: delete <primary_key_value>")
            return
        
        try:
            key = int(arg) if self.current_table.columns[self.current_table.primary_key] == int else arg
            if self.current_table.delete(key):
                print("Record deleted successfully.")
            else:
                print("Record not found.")
        except ValueError:
            print("Invalid key format.")
    
    def do_list_tables(self, arg):
        """List all tables in the database."""
        tables = self.db.list_tables()
        if tables:
            print("Tables:")
            for table in tables:
                print(f"- {table}")
        else:
            print("No tables in the database.")
    
    def do_visualize(self, arg):
        """Visualize the index of the current table."""
        if not self.current_table:
            print("No table selected. Use 'use <table_name>' first.")
            return
        
        self.current_table.visualize_index()
        print(f"Index visualization saved as '{self.current_table.name}_index.png'")
    
    def do_persist(self, arg):
        """Persist the database to disk."""
        self.db.persist()
        print("Database persisted to disk.")
    
    def do_exit(self, arg):
        """Exit the DB shell."""
        self.db.persist()
        print("Database saved. Goodbye!")
        return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python main.py <database_name>")
        sys.exit(1)
    
    db_name = sys.argv[1]
    DBShell(db_name).cmdloop()