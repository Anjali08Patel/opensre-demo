from flask import Flask, request
import json, subprocess, tempfile, os

app = Flask(__name__)

@app.route("/alert", methods=["POST"])
def alert():
    payload = request.get_json(force=True)

    for a in payload.get("alerts", []):

        if a.get("status") != "firing":
            continue

        allowed_alerts = {
            "PodImagePullBackOff",
            "DeploymentReplicasZero",
        }

        if a["labels"].get("alertname") not in allowed_alerts:
            continue

        alert_json = {
            "source": "alertmanager",
            "alertname": a["labels"].get("alertname"),
            "severity": a["labels"].get("severity"),
            "namespace": a["labels"].get("namespace"),
            "pod": a["labels"].get("pod"),
            "deployment": a["labels"].get("deployment", a["labels"].get("pod")),
            "summary": a["annotations"].get("summary", ""),
            "description": a["annotations"].get("description", ""),
            "startsAt": a.get("startsAt"),
            "labels": a["labels"],
        }

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(alert_json, f)
            path = f.name
            print("Alert JSON saved to:", path)
            print(json.dumps(alert_json, indent=2))
        print("HOME:", os.environ.get("HOME"))
        print("USER:", os.environ.get("USER"))
        print("PATH:", os.environ.get("PATH"))
        print("OPENAI_API_KEY exists:", "OPENAI_API_KEY" in os.environ)
        print("OPENAI_API_KEY length:", len(os.environ.get("OPENAI_API_KEY", "")))
        result = subprocess.run(
            [
                "/home/ubuntu/.local/bin/uv",
                "run",
                "--project",
                "/home/ubuntu/opensre-demo/opensre",
                "opensre",
                "investigate",
                "-i",
                path,
            ],
            cwd="/home/ubuntu/opensre-demo/opensre",
            env=os.environ.copy(),
            capture_output=True,
            text=True,
        )

        print("Return code:", result.returncode)
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
    return {"ok": True}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9600)
