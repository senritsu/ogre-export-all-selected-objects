"""OGRE Mesh and Scene Exporters

   @author Tony Richards

    Additional contributors and testers:
        jonim8or
"""

if "init_data" in locals():
    init_data
    reload(ogre_mesh)
    reload(export_mesh)
else:
    import bpyml
    bpyml.tag_module("ogrexml", ("mesh", "submeshes", "submesh", "submeshnames", 
        "submeshname", "faces", "face", "geometry", "vertexbuffer", "vertex",
        "position", "normal", "texcoord"))
    from ogreio import ogre_mesh
    from ogreio import export_mesh

def register():
    export_mesh.register()
    
def unregister():
    export_mesh.unregister()

init_data = True
