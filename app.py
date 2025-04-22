from flask import Flask, request, jsonify, render_template
from db_manager import Database

app = Flask(__name__)
db = Database("my_database")
db.load()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/tables", methods=["GET"])
def list_tables():
    return jsonify(db.list_tables())

@app.route("/table/<table_name>", methods=["GET"])
def get_table(table_name):
    table = db.get_table(table_name)
    if not table:
        return jsonify({"error": "Table not found"}), 404
    return jsonify({"name": table_name, "columns": table.columns})

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
        table.visualize_index()
        return jsonify({"message": f"Visualization saved as {table_name}_index.png"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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