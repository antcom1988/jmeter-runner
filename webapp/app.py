import os
import subprocess
import uuid
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

ALLOWED_EXTENSION = ".jmx"


def resolve_jmeter_bin(value):
    """Accept either a jmeter executable or the base image's bin directory."""
    candidate = Path(value)
    return str(candidate / "jmeter") if candidate.is_dir() else str(candidate)


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        WORKSPACE=Path(os.environ.get("WORKSPACE", "/srv")),
        JMETER_BIN=os.environ.get("JMETER_BIN", "jmeter"),
        MAX_CONTENT_LENGTH=20 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    workspace = Path(app.config["WORKSPACE"])
    plans_dir = workspace / "plans"
    runs_dir = workspace / "runs"
    plans_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)
    runs = {}

    def get_run(run_id):
        run = runs.get(run_id)
        if not run:
            abort(404)
        return run

    def run_payload(run):
        status = "running"
        return_code = run["process"].poll()
        if return_code is not None:
            status = "completed" if return_code == 0 else "failed"
        report_index = run["report_dir"] / "index.html"
        return {
            "id": run["id"],
            "plan": run["plan"],
            "status": status,
            "exitCode": return_code,
            "reportUrl": f"/reports/{run['id']}/index.html" if report_index.exists() else None,
            "logUrl": f"/api/runs/{run['id']}/log",
        }

    @app.get("/")
    def dashboard():
        return render_template("index.html")

    @app.get("/api/test-plans")
    def list_test_plans():
        return jsonify(sorted(item.name for item in plans_dir.glob("*.jmx") if item.is_file()))

    @app.post("/api/uploads")
    def upload_test_plan():
        uploaded = request.files.get("file")
        if not uploaded or not uploaded.filename:
            return jsonify(error="A .jmx file is required."), 400
        filename = secure_filename(uploaded.filename)
        if not filename.lower().endswith(ALLOWED_EXTENSION):
            return jsonify(error="Only .jmx files can be uploaded."), 400
        uploaded.save(plans_dir / filename)
        return jsonify(file=filename), 201

    @app.post("/api/runs")
    def start_run():
        data = request.get_json(silent=True) or {}
        plan_name = secure_filename(str(data.get("plan", "")))
        plan_path = plans_dir / plan_name
        if not plan_name or plan_path.suffix.lower() != ALLOWED_EXTENSION or not plan_path.is_file():
            return jsonify(error="Selected .jmx test plan was not found."), 404

        run_id = uuid.uuid4().hex
        run_dir = runs_dir / run_id
        report_dir = run_dir / "report"
        run_dir.mkdir(parents=True)
        log_path = run_dir / "jmeter.log"
        results_path = run_dir / "results.jtl"
        log_file = log_path.open("w", encoding="utf-8")
        command = [
            resolve_jmeter_bin(app.config["JMETER_BIN"]), "-n", "-t", str(plan_path), "-l", str(results_path),
            "-e", "-o", str(report_dir),
        ]
        try:
            process = subprocess.Popen(command, stdout=log_file, stderr=subprocess.STDOUT, text=True)
        except OSError as exc:
            log_file.close()
            return jsonify(error=f"Unable to start JMeter: {exc}"), 500
        runs[run_id] = {
            "id": run_id,
            "plan": plan_name,
            "process": process,
            "log_path": log_path,
            "report_dir": report_dir,
        }
        return jsonify(run_payload(runs[run_id])), 202

    @app.get("/api/runs")
    def list_runs():
        return jsonify([run_payload(run) for run in runs.values()])

    @app.get("/api/runs/<run_id>")
    def run_status(run_id):
        return jsonify(run_payload(get_run(run_id)))

    @app.get("/api/runs/<run_id>/log")
    def run_log(run_id):
        run = get_run(run_id)
        content = run["log_path"].read_text(encoding="utf-8") if run["log_path"].exists() else ""
        return jsonify(log=content)

    @app.get("/reports/<run_id>/<path:filename>")
    def report_file(run_id, filename):
        return send_from_directory(get_run(run_id)["report_dir"], filename)

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8080)
