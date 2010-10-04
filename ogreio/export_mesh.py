__author__ = ["Tony Richards"]
__url__ = ("www.indiezen.org", "www.blender.org", "www.ogre3d.org")
__version__ = "0.1.0"
__bpydoc__ = """\

OGRE XML Mesh Exporter

This script Exports an OGRE XML Mesh file.

"""
import struct
import os
import time
import traceback

import bpy
import bpyml

bpyml.tag_module("ogrexml", ("mesh", "submeshes", "submesh", "submeshnames", 
    "submeshname", "faces", "face", "geometry", "vertexbuffer", "vertex",
    "position", "normal", "texcoord"))
import ogrexml

from bpy.props import *
from ogre_mesh import *

class ExportOGREMesh(bpy.types.Operator):
    '''Save an OGRE XML Mesh File'''

    bl_idname = "export.ogre_xml"
    bl_label = 'Export OGRE XML'

    # testing
    defaultFileName = "/home/sgtflame/dev/koz/resources/test.mesh.xml"
    #defaultFileName = "test.mesh.xml"
    
    filepath = StringProperty(name="File Path", description="Filepath used for exporting the X3D file", maxlen= 1024, default= defaultFileName)
    #check_existing = BoolProperty(name="Check Existing", description="Check and warn on overwriting existing files", default=True, options={'HIDDEN'})
    xml_to_mesh = StringProperty(name="OgreXMLConverter", description="Path to OgreXMLConverter", maxlen=1024, default="/usr/local/bin/OgreXMLConverter")

    def execute(self, context):
        filepath = self.properties.filepath

        # Open a log file
        logfilename = filepath + ".log"
        self.logfile = open(logfilename, "w")

        try:
            self.writeMesh(filepath)
        except:
            traceback.print_exc(file=self.logfile)

        # Close the log
        self.logfile.close()

        return finished

    def invoke(self, context, event):
        import os
        if not self.properties.is_property_set("filepath"):
            self.properties.filepath = os.path.splitext(bpy.data.filepath)[0] + ".mesh.xml"

        context.manager.add_fileselect(self)
        return running_modal


    def getSubMeshes(self, mesh):
        '''Split the mesh into subMeshes.'''
        faces = mesh.faces

        # Create a list to contain all of the submeshes
        submeshes = {}

        self.logfile.write("Processing %i faces\n" % (len(faces)))

        # Enumerate through the faces
        for i, face in enumerate(faces):
            # Get or create the submesh
            submesh = submeshes.get(face.material_index)
            if submesh == None:
                submesh = OgreSubMesh(mesh, self)
                submeshes[face.material_index] = submesh

            if len(face.vertices) == 3: #tri
                submesh.addFace(OgreFace(submesh, i, face.vertices, [0, 1, 2]))
            else: # quad
                # Split into triangles
                # Handle the first triangle
                submesh.addFace(OgreFace(submesh, i, face.vertices, [0, 1, 2]))
                # Handle the second triangle
                submesh.addFace(OgreFace(submesh, i, face.vertices, [0, 2, 3]))

        self.logfile.write("Returning %i submeshes\n" % (len(submeshes)))

        return submeshes

    def writeMesh(self, filename):
        '''Save the currently selected Blender mesh to a xml file.'''

        if filename.lower().endswith('.mesh.mesh.xml'):
            filename = filename[:-14]
            filename += ".mesh.xml"

        if not filename.lower().endswith('.mesh.xml'):
            filename += '.mesh.xml'

        self.logfile.write("Exporting to %s\n" % (filename))

        # A shortcut might be:
        # scene = bpy.context.scene
        # selectedObject = scene.objects.active

        # Find all of the selected objects
        selectedObjects = []
        for obj in bpy.data.objects:
            if obj.select:
                selectedObjects.append(obj)

        # For now, one and only one objects can be selected
        if len(selectedObjects) != 1:
            print("Error, only one object can be selected.")
            self.logfile.close()
            return

        # Open the file for writing:
        writer = open(filename, "w")

        # HACK only export the first selected object
        object = selectedObjects[0]
        mesh = object.data

        # Create the general layout of the file
        # <mesh>
        #     <submeshes>
        #     </submeshes>
        #     <submeshnames>
        #     </submeshnames>
        # </mesh>
        mesh_node = ogrexml.mesh()
        submeshes_node = ogrexml.submeshes()
        submeshnames_node = ogrexml.submeshnames()

        mesh_node[2].append(submeshes_node)
        mesh_node[2].append(submeshnames_node)

        # Generate the faces and split into submeshes based on material
        submeshes = self.getSubMeshes(mesh).values()

        for subMeshIndex, submesh in enumerate(submeshes):

            # Create the submesh node
            submesh_attributes = {
                "usesharedvertices" : "false", 
                "use32bitindexes" : "false", 
                "operationtype" : "triangle_list"
            }

            if (len(mesh.materials) > 0):
                submesh_attributes["material"] = mesh.materials[subMeshIndex].name

            submesh_node = ogrexml.submesh(**submesh_attributes)

            submeshes_node[2].append(submesh_node)

            submesh_node[2].append(submesh.getFacesXML())
            submesh_node[2].append(submesh.getGeometryXML())

            subMeshIndex = 0
            submeshname_node = ogrexml.submeshname(name=mesh.materials[subMeshIndex].name,
                index = str(subMeshIndex))

            submeshnames_node[2].append(submeshname_node)

        # Write the XML file
        #self.logfile.write(str(mesh_node))
        writer.write(bpyml.toxml([mesh_node]))

        # Close the file:
        writer.close()

def menu_func(self, context):
    self.layout.operator(ExportOGREMesh.bl_idname, text="OGRE XML Mesh (.mesh.xml)")

def needsToRegister():
    maj, min, build = bpy.app.version
    if (maj > 2):
        return False
    if (maj == 2):
        if (min > 53):
            return False
        if (min < 53):
            return True
        if (build == 0):
            return True
        return False
    return True
        
        

def register():
    if needsToRegister():
        bpy.types.register(ExportOGREMesh)
    bpy.types.INFO_MT_file_export.append(menu_func)

def unregister():
    if needsToRegister():
        bpy.types.unregister(ExportOGREMesh)
    bpy.types.INFO_MT_file_export.remove(menu_func)

if __name__ == "__main__":
    register()

finished = set()
finished.add("FINISHED")
info = set()
info.add("INFO")

running_modal = set()
running_modal.add("RUNNING_MODAL")