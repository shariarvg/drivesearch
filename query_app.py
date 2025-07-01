from flask import Flask, request, jsonify
from search_logic import semantic_search
import query

app = Flask(__name__)

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    query_text = data.get("query", "")
    username = data.get("username")
    k = data.get("k", 5)

    if not query_text or not username:
        return jsonify({"error": "Missing 'query' or 'username'"}), 400

    try:
        results = query.return_file_ids(username=username, query=query_text, k=k)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
