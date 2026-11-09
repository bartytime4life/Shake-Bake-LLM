"""Create an offline, recorded-demo inspector; never include user project data."""

import argparse
import base64
import json
from pathlib import Path
import time

from shake_bake.gui import ASSETS, Controller, DEMO


def capture_demo():
    controller = Controller({"starter-demo": DEMO})
    try:
        started = controller.call("start", {"project_id": "starter-demo", "task_kind": "code",
            "task": "Find the executable slice coverage guard. Can it accept fewer reported slices than detected? Provide exact evidence and gaps."})
        deadline = time.monotonic()+5
        while time.monotonic()<deadline:
            result = controller.call("result", started["task_id"])
            if result["state"]!="RUNNING":
                break
            time.sleep(.01)
        if result["state"]!="DONE" or result.get("worker") is not None:
            raise RuntimeError("recorded demo did not complete without a model")
        state = controller.call("state")
        for project in state["projects"]:
            project["path"] = "Bundled inert demo source"
        return {"preview_type":"recorded_demo", "actual_model_inference":False,
                "state":state,"result":result}
    finally:
        controller.close()


def render_preview(record):
    # Escape source/code data so a captured excerpt cannot close the script tag.
    payload=json.dumps(record,ensure_ascii=False).replace("<","\\u003c").replace("\u2028","\\u2028").replace("\u2029","\\u2029")
    css=(ASSETS/"styles.css").read_text()
    script="\n".join((ASSETS/name).read_text() for name in ("app.js", "troubleshoot.js")).replace("</script","<\\/script")
    html=(ASSETS/"index.html").read_text()
    html=html.replace('<link rel="stylesheet" href="styles.css">', '<style>'+css+'</style>')
    html=html.replace('<script src="app.js" defer></script>', '')
    html=html.replace('<script src="troubleshoot.js" defer></script>', '')
    # The recorded artifact is an inert source-brief inspector, not a live locator.
    html=html.replace('id="source-brief-workflow" hidden', 'id="source-brief-workflow"')
    for icon in (ASSETS / "icons").glob("*.svg"):
        inline = "data:image/svg+xml;base64," + base64.b64encode(icon.read_bytes()).decode()
        html = html.replace("icons/" + icon.name, inline)
        script = script.replace("icons/" + icon.name, inline)
    return html.replace('</body>', '<script>window.__SB_RECORDED_PREVIEW__='+payload+';</script><script>'+script+'</script></body>')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--receipt",type=Path)
    args=parser.parse_args()
    if DEMO.resolve() in args.output.resolve().parents:
        parser.error("preview output must be outside the demo source")
    record=capture_demo()
    args.output.write_text(render_preview(record),encoding="utf-8")
    if args.receipt:
        args.receipt.write_text(json.dumps(record,indent=2)+'\n',encoding="utf-8")
    print(json.dumps({"preview_type":record["preview_type"],"evidence_excerpts":len(record["result"]["evidence"]),"actual_model_inference":False}))


if __name__=="__main__":main()
