import json
from pathlib import Path
from datetime import datetime
from syftbox.lib import Client, SyftPermission
from types import SimpleNamespace


def fill_template(template_path, current_index, round_size, session, chartData):
    with open(template_path, "r") as file:
        template = file.read()

    filled_template = (
        template.replace("{current_index}", current_index)
        .replace("{round_size}", round_size)
        .replace("{peer_box_session}", session)
        .replace(
            "{dataset_info}",
            """[{
    "timestamp": "2024-10-04T00:30",
    "total_peers": 36,
},{
    "timestamp": "2024-10-04T00:35",
    "total_peers": 36,
}]
""",
        )
        .replace("{chart_data}", chartData)
    )

    return filled_template


session_template = """
        <div class="user-box {}">
            <strong>{}</strong>
            <br>index : {}<br>
        </div>
"""

model_loss_data_template = """
            const chartData = {} 
"""

if __name__ == "__main__":
    client = Client.load()

    observer_data_path: Path = (
        Path(client.datasite_path) / "app_pipelines" / "ring_observer" / "data.json"
    )

    if not observer_data_path.is_file():
        print("Couldn't find data.json in observer path. Finishing the process.'")
        exit()

    with open(str(observer_data_path), "r") as json_file:
        infos = json.load(json_file)

    members = infos["ring"]
    current_member = infos["ring"][infos["current_index"]]
    unique_members = sorted(list(set(infos["ring"])))
    list_of_members = []
    for member in unique_members:
        status = "logged-out"
        if member == current_member:
            status = "logged-in"

        member_info = (status, member, "Hello World")
        list_of_members.append(member_info)

    session = ""
    for peer in list_of_members:
        session += session_template.format(peer[0], peer[1], peer[2])

    chart_file_path = Path("chart_data.json")
    model_loss_chart = {}
    if chart_file_path.is_file():
        with open(str(chart_file_path), "r+") as chart_file:
            old_chart_infos = json.load(chart_file)
            old_chart_infos.append(
                {
                    "iterations": infos["data"]["iterations"],
                    "model_loss": infos["data"]["loss"],
                }
            )
            chart_file.seek(0)
            json.dump(old_chart_infos, chart_file, indent=4)
            chart_file.truncate()
            model_loss_chart = old_chart_infos
    else:
        with open(str(chart_file_path), "w") as chart_file:
            now = datetime.now().strftime("%Y-%m-%dT%H:%M")
            json.dump(
                [
                    {
                        "timestamp": infos["data"]["iterations"],
                        "model_loss": infos["data"]["loss"],
                    }
                ],
                chart_file,
                indent=4,
            )
            model_loss_chart = [{"timestamp": now, "model_loss": infos["data"]["loss"]}]

    public_path = Path(client.datasite_path) / "public/fl_stats.html"
    model_loss = model_loss_data_template.format(str(model_loss_chart))
    with open(str(public_path), "w") as f:
        f.write(
            fill_template(
                "template.txt",
                str(infos["current_index"] + 1),
                str(len(infos["ring"])),
                session,
                model_loss,
            )
        )
