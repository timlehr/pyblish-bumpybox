import os

import hou

import pyblish.api
import clique


class CollectHoudini(pyblish.api.ContextPlugin):
    """ Collects from all supported Houdini nodes. """

    order = pyblish.api.CollectorOrder

    def process(self, context):

        # Find nodes by class.
        nodes = []

        node_type = hou.nodeType("Driver/ifd")
        nodes.extend(node_type.instances())

        node_type = hou.nodeType(hou.ropNodeTypeCategory(), "alembic")
        nodes.extend(node_type.instances())

        node_type = hou.nodeType(hou.ropNodeTypeCategory(), "dop")
        nodes.extend(node_type.instances())

        node_type = hou.nodeType(hou.ropNodeTypeCategory(), 'geometry')
        nodes.extend(node_type.instances())

        # Categorize nodes based on whether they are in a network box starting
        # with "farm".
        nodes_local = list(nodes)
        for box in hou.node("out").networkBoxes():
            if box.name().startswith("farm"):
                for node in box.nodes():
                    if node in nodes_local:
                        nodes_local.remove(node)

        # Creating instances per node.
        for node in nodes:

            instance = context.create_instance(name=node.name())
            instance.data["publish"] = not node.isBypassed()
            instance.add(node)

            # Determine node type specifics.
            node_type = ""
            category = ""
            output_parm = ""

            if node.type().name() == "ifd":
                node_type = "mantra"
                category = "img"
                output_parm = "vm_picture"

                # Rendering *.ifd files.
                if node.parm("soho_outputmode").eval():
                    output_parm = "soho_diskfile"

            if node.type().name() == "alembic":
                node_type = "alembic"
                category = "cache"
                output_parm = "filename"

            if node.type().name() == "dop":
                node_type = "dynamics"
                category = "cache"
                output_parm = "dopoutput"

            if node.type().name() == "geometry":
                node_type = "geometry"
                category = "cache"
                output_parm = "sopoutput"

            # Get expected output files.
            files = []
            if node.parm("trange").eval() == 0:
                frame = int(hou.frame())
                files.append(node.parm(output_parm).evalAtFrame(frame))
            else:
                start = node.parm("f1").eval()
                end = node.parm("f2").eval()
                step = node.parm("f3").eval()
                for frame in range(int(start), int(end) + 1, int(step)):
                    files.append(node.parm(output_parm).evalAtFrame(frame))

            # Get extension
            ext = os.path.splitext(files[0])[1]
            # Special case for *.bgeo.sc files since it was two "extensions".
            if files[0].endswith(".bgeo.sc"):
                ext = ".bgeo.sc"

            # Create output collection.
            collections = clique.assemble(files, minimum_items=1)[0]
            collection = None
            for col in collections:
                if col.format("{tail}") == ext:
                    collection = col

            instance.data["collection"] = collection

            # Assigning families.
            families = [node_type, category, ext[1:]]
            if node in nodes_local:
                families += ["local"]
            else:
                families += ["farm"]

            instance.data["families"] = families

            # Create existing files instance.
            existing_files = []
            for f in collection:
                if os.path.exists(f):
                    existing_files.append(f)

            existing_collection = clique.Collection(head=collection.head,
                                                    tail=collection.tail,
                                                    padding=collection.padding)
            for f in existing_files:
                existing_collection.add(f)

            if existing_files:
                name = os.path.basename(existing_collection.format())
                instance = context.create_instance(name=name)

                instance.data["collection"] = existing_collection
                instance.data["families"] = [category, ext[1:]]
                instance.data["publish"] = False
                instance.data["component_name"] = node.name()
