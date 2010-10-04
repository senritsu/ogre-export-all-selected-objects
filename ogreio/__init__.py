"""OGRE Mesh and Scene Exporters

   @author Tony Richards
"""

try:
    init_data
    reload(export_mesh)
    reload(ogre_mesh)
    reload(ogre_test)
except:
    from ogreio import export_mesh
    from ogreio import ogre_mesh
    from ogreio import ogre_test

def register():
    export_mesh.register()
    
def unregister():
    export_mesh.unregister()

init_data = True
