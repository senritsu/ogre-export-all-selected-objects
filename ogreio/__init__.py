"""OGRE Mesh and Scene Exporters

   @author Tony Richards
"""

try:
    init_data
    reload(export_mesh)
except:
    from ogreio import export_mesh

def register():
    export_mesh.register()
    
def unregister():
    export_mesh.unregister()

init_data = True
