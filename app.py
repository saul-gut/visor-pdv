from flask import Flask, jsonify, request, send_file, Response
import json
import pandas as pd
from io import StringIO

app = Flask(__name__)

FILE_CANDIDATA = "candidata.geojson"
FILE_INICIAL = "inicial.geojson"


# ===============================
# CARGAR GEOJSON UNA SOLA VEZ
# ===============================
def load_geojson(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

data_candidata = load_geojson(FILE_CANDIDATA)
data_inicial = load_geojson(FILE_INICIAL)


# ===============================
# DATA POR BBOX
# ===============================
@app.route("/data")
def data():
    bbox = request.args.get("bbox")

    data_c = data_candidata
    data_i = data_inicial

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

    data = data_candidata if layer == "candidata" else data_inicial

    if layer == "candidata":
        key = "USER_id_simulado"
        file_path = FILE_CANDIDATA
    else:
        key = "USER_Numero_identificación"
        file_path = FILE_INICIAL

    cambios = 0

    for f in data["features"]:
        feature_id = f["properties"].get(key)
        if feature_id in ids:
            f["properties"]["APLICA"] = aplica
            cambios += 1

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    return jsonify({"status": "ok", "updated": cambios})


# ===============================
# EXPORT
# ===============================
@app.route("/export")
def export():
    rows = []

    for f in data_candidata["features"]:
        row = f["properties"].copy()
        row["CAPA"] = "CANDIDATA"
        rows.append(row)

    for f in data_inicial["features"]:
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


@app.route("/")
def index():
    return send_file("index.html")


if __name__ == "__main__":
    app.run(debug=True)
