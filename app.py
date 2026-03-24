from flask import Flask, jsonify, request, send_file, Response
import json
import pandas as pd
from io import StringIO

app = Flask(__name__)

FILE_CANDIDATA = "candidata.geojson"
FILE_INICIAL = "inicial.geojson"


def load_geojson(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_geojson(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


# ===============================
# DATA POR BBOX (MEJORA GRANDE)
# ===============================
@app.route("/data")
def data():
    bbox = request.args.get("bbox")

    data_c = load_geojson(FILE_CANDIDATA)
    data_i = load_geojson(FILE_INICIAL)

    if bbox:
        xmin, ymin, xmax, ymax = map(float, bbox.split(","))

        def filter_geojson(data):
            filtered = []
            for f in data["features"]:
                x, y = f["geometry"]["coordinates"]
                if xmin <= x <= xmax and ymin <= y <= ymax:
                    filtered.append(f)
            return {"type": "FeatureCollection", "features": filtered}

        data_c = filter_geojson(data_c)
        data_i = filter_geojson(data_i)

    return jsonify({
        "candidata": data_c,
        "inicial": data_i
    })


# ===============================
# UPDATE
# ===============================
@app.route("/update", methods=["POST"])
def update():
    req = request.json

    layer = req.get("layer")
    ids = req.get("ids", [])
    aplica = req.get("aplica")

    file_path = FILE_CANDIDATA if layer == "candidata" else FILE_INICIAL
    data = load_geojson(file_path)

    if layer == "candidata":
        key = "USER_id_simulado"
    else:
        key = "USER_Numero_identificación"

    cambios = 0

    for f in data["features"]:
        feature_id = f["properties"].get(key)

        if feature_id in ids:
            f["properties"]["APLICA"] = aplica
            cambios += 1

    save_geojson(file_path, data)

    return jsonify({
        "status": "ok",
        "updated": cambios
    })


# ===============================
# EXPORT CSV
# ===============================
@app.route("/export")
def export():
    data_c = load_geojson(FILE_CANDIDATA)
    data_i = load_geojson(FILE_INICIAL)

    rows = []

    for f in data_c["features"]:
        row = f["properties"].copy()
        row["CAPA"] = "CANDIDATA"
        rows.append(row)

    for f in data_i["features"]:
        row = f["properties"].copy()
        row["CAPA"] = "INICIAL"
        rows.append(row)

    df = pd.DataFrame(rows)

    output = StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=pdv.csv"}
    )


# ===============================
# INDEX
# ===============================
@app.route("/")
def index():
    return send_file("index.html")


if __name__ == "__main__":
    app.run(debug=True)
