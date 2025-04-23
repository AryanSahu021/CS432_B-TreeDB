from flask import Flask, request, jsonify, render_template, send_from_directory
from db_manager import Database
import os

app = Flask(__name__)
db = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/database", methods=["POST"])
def select_database():
    data = request.json
    db_name = data.get("name")
    if not db_name:
        return jsonify({"error": "Database name is required"}), 400
    try:
        global db
        db = Database(db_name)
        db.load()
        return jsonify({
            "message": f"Connected to database '{db_name}'",
            "database": db_name
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/database/create", methods=["POST"])
def create_database():
    data = request.json
    db_name = data.get("name")
    if not db_name:
        return jsonify({"error": "Database name is required"}), 400
    try:
        global db
        db = Database(db_name)
        db.persist()  # Create the database
        db.load()  # Load the newly created database
        return jsonify({
            "message": f"Database '{db_name}' created successfully",
            "database": db_name
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.before_request
def check_db():
    if request.endpoint != 'index' and request.endpoint != 'select_database' and db is None:
        return jsonify({"error": "No database selected"}), 400

@app.route("/tables", methods=["GET"])
def list_tables():
    print(db.tables)
    return jsonify(db.list_tables())

@app.route("/table/<table_name>", methods=["GET"])
def get_table(table_name):
    table = db.get_table(table_name)
    if not table:
        return jsonify({"error": "Table not found"}), 404
    
    # Convert column types to strings, handling both type objects and strings
    columns = {}
    for name, type_ in table.columns.items():
        if isinstance(type_, type):
            columns[name] = type_.__name__
        else:
            columns[name] = str(type_)
    
    return jsonify({
        "name": table_name,
        "columns": columns
    })
@app.route("/table/create", methods=["POST"])
def create_table():
    data = request.json
    table_name = data.get("name")
    columns = data.get("columns")
    primary_key = data.get("primary_key")
    if not table_name or not columns or not primary_key:
        return jsonify({"error": "Missing required fields"}), 400
    try:
        column_dict = {col.split(":")[0]: eval(col.split(":")[1]) for col in columns.split(",")}
        db.create_table(table_name, column_dict, primary_key)
        db.persist()  # Save after creating table
        return jsonify({"message": f"Table '{table_name}' created successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/table/<table_name>/delete", methods=["DELETE"])
def delete_table(table_name):
    try:
        db.delete_table(table_name)
        return jsonify({"message": f"Table '{table_name}' deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/table/<table_name>/insert", methods=["POST"])
def insert_record(table_name):
    table = db.get_table(table_name)
    if not table:
        return jsonify({"error": "Table not found"}), 404
    record = request.json
    try:
        table.insert(record)
        db.persist()  # Save after inserting record
        return jsonify({"message": "Record inserted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/table/<table_name>/update", methods=["PUT"])
def update_record(table_name):
    table = db.get_table(table_name)
    if not table:
        return jsonify({"error": "Table not found"}), 404
    data = request.json
    primary_key = data.get("primary_key")
    updates = data.get("updates")
    if not primary_key or not updates:
        return jsonify({"error": "Missing required fields"}), 400
    try:
        table.update(primary_key, updates)
        db.persist()  # Save after updating record
        return jsonify({"message": "Record updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/table/<table_name>/delete_record", methods=["DELETE"])
def delete_record(table_name):
    table = db.get_table(table_name)
    if not table:
        return jsonify({"error": "Table not found"}), 404
    data = request.json
    primary_key = data.get("primary_key")
    if not primary_key:
        return jsonify({"error": "Missing primary key"}), 400
    try:
        table.delete(primary_key)
        return jsonify({"message": "Record deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/table/<table_name>/visualize", methods=["GET"])
def visualize_table(table_name):
    table = db.get_table(table_name)
    if not table:
        return jsonify({"error": "Table not found"}), 404
    try:
        # Save visualization in database directory
        viz_path = os.path.join(db.db_dir, f"{table_name}_index")
        table.visualize_index(viz_path)
        return jsonify({
            "message": "Visualization created successfully",
            "image_path": f"{db.name}_db/{table_name}_index.png"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add a route to serve visualization images
@app.route("/visualizations/<path:filename>")
def serve_visualization(filename):
    return send_from_directory(".", filename)

@app.route("/table/<table_name>/contents", methods=["GET"])
def get_table_contents(table_name):
    table = db.get_table(table_name)
    if not table:
        return jsonify({"error": "Table not found"}), 404
    try:
        records = table.select_all()
        return jsonify(records)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/persist", methods=["POST"])
def persist_db():
    try:
        db.persist()
        return jsonify({"message": "Database persisted to disk"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)