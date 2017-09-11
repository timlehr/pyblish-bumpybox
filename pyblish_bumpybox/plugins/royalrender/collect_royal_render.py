import pyblish.api


class CollectNukeWritesRoyalRender(pyblish.api.ContextPlugin):
    """Collect all write nodes."""

    order = pyblish.api.CollectorOrder + 0.1
    label = "Writes Royal Render"
    hosts = ["nuke"]
    targets = ["process.royalrender"]

    def process(self, context):
        import nuke

        for item in context.data["instances"]:
            instance = context.create_instance(item.data["name"])
            for key, value in item.data.iteritems():
                instance.data[key] = value

            instance.data["label"] += " - royalrender"
            instance.data["families"] = ["write", "royalrender"]
            for node in item:
                instance.add(node)

            # Adding/Checking publish attribute
            if "process_royalrender" not in node.knobs():
                knob = nuke.Boolean_Knob(
                    "process_royalrender", "Process RoyalRender"
                )
                knob.setValue(False)
                node.addKnob(knob)

            value = bool(node["process_royalrender"].getValue())
            instance.data["publish"] = value
