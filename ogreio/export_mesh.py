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

import bpy
import bpyml

bpyml.tag_module("ogrexml", ("mesh", "submeshes", "submesh", "submeshnames", 
    "submeshname", "faces", "face", "geometry", "vertexbuffer", "vertex",
    "position", "normal", "texcoord"))
import ogrexml

from bpy.props import *

def getSelectedMesh():
    selectedObjects = []
    for obj in bpy.data.objects:
        if obj.select:
            selectedObjects.append(obj)

    # For now, one and only one objects can be selected
    if len(selectedObjects) != 1:
        print("Error, only one object can be selected.")
        logfile.close()
        return

    # HACK only export the first selected object
    object = selectedObjects[0]
    mesh = object.data
    return mesh

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
        self.writeMesh(filepath)
        return finished

    def invoke(self, context, event):
        import os
        if not self.properties.is_property_set("filepath"):
            self.properties.filepath = os.path.splitext(bpy.data.filepath)[0] + ".mesh.xml"

        context.manager.add_fileselect(self)
        return running_modal

    def generateGeometryNode(self, mesh_data, vertex_face_index):
        ''' Generate a geometry_node for the provided submesh'''
        vertices = mesh_data.vertices.items()

        geometry_node = ogrexml.geometry(vertexcount=len(vertices))

        vertexbuffer_attributes = {
            "texture_coords" : len(mesh_data.uv_textures),
            "positions" : "true",
            "normals" : "true", 
        }
        # HACK Shouldn't assume 2 texture coordinates
        for i, uv_texture in enumerate(mesh_data.uv_textures):
            vertexbuffer_attributes["texture_coord_dimensions_" + str(i)] = "2"

        vertexbuffer_node = ogrexml.vertexbuffer(**vertexbuffer_attributes)
        geometry_node[2].append(vertexbuffer_node)

        # Populate the vertex buffer node with all of the vertices
        for vertex_number, vdata in enumerate(vertices):
            vindex = vdata[0]
            vcoord = vdata[1].co
            vnormal = vdata[1].normal
            
            # Create the vertex, position, normal, and zero or more texcoord nodes
            vertex_node = ogrexml.vertex()
            vertexbuffer_node[2].append(vertex_node)

            position_node = ogrexml.position(x=vcoord.x, y=vcoord.y, z=vcoord.z)
            normal_node = ogrexml.normal(x=vnormal.x, y=vnormal.y, z=vnormal.z)

            vertex_node[2].append(position_node)
            vertex_node[2].append(normal_node)

            # Handle texture coordinate nodes
            for uv_texture in mesh_data.uv_textures:
                face_number, vertex_index = vertex_face_index[vertex_number]
                uv = uv_texture.data[face_number].uv
                u = uv[vertex_index][0]
                v = uv[vertex_index][1]
                texcoord_node = ogrexml.texcoord(u = u, v = v)
                vertex_node[2].append(texcoord_node)

        return geometry_node

    def generateFacesNode(self, submesh):
        '''Generate a faces_node for the provided submesh'''
        faces = submesh.faces
        
        # Create a list to contain all of the generated face_nodes
        # We need to do this because we do not know how many faces
        # there are since we have to tesselate quads into tris
        faces_list = []

        # Create a dictionary of vertex_number : (face_number, vertex_index)
        # This dictionary will be used by generateGeometryNode()
        # so that as it iterates through the vertices, it can get to a
        # face / vertex for that face in order to get the texture uv
        vertex_face_index = {}

        # Enumerate through the faces
        for i, face in enumerate(faces):
            if len(face.vertices) == 3: #tri
                args = {}
                for n, vertex in enumerate(face.vertices):
                    args["v" + str(n + 1)] = vertex
                    vertex_face_index[vertex] = (i, n)
                face_node = ogrexml.face(**args)
                faces_list.append(face_node)
            else: # quad
                # Split into triangles
                # Handle the first triangle
                args = {}
                vertices = [face.vertices[0], face.vertices[1], face.vertices[2]]
                for n, vertex in enumerate(vertices):
                    args["v" + str(n + 1)] = vertex
                    vertex_face_index[vertex] = (i, n)
                face_node = ogrexml.face(**args)
                faces_list.append(face_node)
                # Handle the second triangle
                args = {}
                vertices = [face.vertices[0], face.vertices[2], face.vertices[3]]
                for n, vertex in enumerate(vertices):
                    args["v" + str(n + 1)] = vertex
                    vertex_face_index[vertex] = (i, n)
                face_node = ogrexml.face(**args)
                faces_list.append(face_node)

        faces_node = ogrexml.faces(count=len(faces_list))
        for face_node in faces_list:
            faces_node[2].append(face_node)
        return faces_node, vertex_face_index

    def writeMesh(self, filename):
        '''Save the currently selected Blender mesh to a xml file.'''

        # Open a log file
        logfilename = filename + ".log"
        self.logfile = open(logfilename, "w")
        
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

        # can there be more than one submesh?
        # for now, lets assume not
        submesh = mesh

        submesh_node = ogrexml.submesh(material=submesh.materials[0].name, 
            usesharedvertices="false", 
            use32bitindexes="false", 
            operationtype="triangle_list")

        submeshes_node[2].append(submesh_node)

        # Generate the faces
        faces_node, vertex_face_index = self.generateFacesNode(submesh)
        submesh_node[2].append(faces_node)

        # Generate the geometry
        geometry_node = self.generateGeometryNode(submesh, vertex_face_index)
        submesh_node[2].append(geometry_node)

        # todo loop through the submeshes again, but for now
        # just assume there's only one submesh
        subMeshIndex = 0
        submeshname_node = ogrexml.submeshname(name=submesh.name,
            index = str(subMeshIndex))

        submeshnames_node[2].append(submeshname_node)
        
        # Write the XML file
        writer.write(bpyml.toxml([mesh_node]))

        # Close the file:
        writer.close()
        
        # Close the log
        self.logfile.close()

def menu_func(self, context):
    self.layout.operator(ExportOGREMesh.bl_idname, text="OGRE XML Mesh (.mesh.xml)")

def register():
    bpy.types.register(ExportOGREMesh)
    bpy.types.INFO_MT_file_export.append(menu_func)

def unregister():
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