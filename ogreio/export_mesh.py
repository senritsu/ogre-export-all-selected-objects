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


import ogrexml

from bpy.props import *
from ogreio.ogre_mesh import *

class ExportOGREMesh(bpy.types.Operator):
    '''Save an OGRE XML Mesh File'''

    bl_idname = "export.ogre_xml"
    bl_label = 'Export OGRE XML'

    #  Testing - These are only used when invoked without specifying a filepath (not via the GUI)
    if bpy.app.build_platform.split(':')[0] == 'Windows':
        defaultFileName = "C:/dev/KnightsOfZen/resources/test.mesh.xml"
    else:
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
        wm = context.window_manager
        wm.add_fileselect(self)
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

        # Open the file for writing:
        writer = open(filename, "w")

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


        subMeshIndex = 0
        for obj in selectedObjects:
            # Generate the faces and split into submeshes based on material
            mesh = obj.data
            submeshes = self.getSubMeshes(mesh).values()

            for materialIndex,submesh in enumerate(submeshes):

                # Create the submesh node
                submesh_attributes = {
                    "usesharedvertices" : "false",
                    "use32bitindexes" : "false",
                    "operationtype" : "triangle_list"
                }

                if (len(mesh.materials) > 0):
                    submesh_attributes["material"] = mesh.materials[materialIndex].name

                submesh_node = ogrexml.submesh(**submesh_attributes)

                submeshes_node[2].append(submesh_node)

                submesh_node[2].append(submesh.getFacesXML())
                submesh_node[2].append(submesh.getGeometryXML())


                submeshname_node = ogrexml.submeshname(name="{0}.{1}".format(obj.name,mesh.materials[materialIndex].name),
                    index = str(subMeshIndex))
                subMeshIndex += 1

                submeshnames_node[2].append(submeshname_node)

        # Write the XML file
        #self.logfile.write(str(mesh_node))
        writer.write(bpyml.toxml([mesh_node]))

        # Close the file:
        writer.close()

def menu_func(self, context):
    self.layout.operator(ExportOGREMesh.bl_idname, text="OGRE XML Mesh (.mesh.xml)")

def register():
    bpy.types.INFO_MT_file_export.append(menu_func)

def unregister():
    bpy.types.INFO_MT_file_export.remove(menu_func)

if __name__ == "__main__":
    register()

finished = set()
finished.add("FINISHED")
info = set()
info.add("INFO")

running_modal = set()
running_modal.add("RUNNING_MODAL")