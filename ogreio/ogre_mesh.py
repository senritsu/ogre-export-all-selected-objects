

import bpy
import ogrexml

class OgreSubMesh():
    
    def __init__(self, mesh, exporter):
        self.mesh = mesh
        self.logfile = exporter.logfile

        # Create a list to contain all of the OgreFace for this OgreSubMesh
        self.faces = []

        # List of OgreVertex objects
        self.vertices = []

        # Map from the blender vertex index to a list of OgreVertex objects
        # that have the same coordinates (but possibly different uv coords)
        self.vertex_map = {}

    def addFace(self, face):
        self.faces.append(face)

        for i, blender_vertex in enumerate(face.vertices):
            self.logfile.write("Face %i vertex %i co %s " % 
                (len(self.faces), blender_vertex.index, str(blender_vertex.co)))
            uv_coords = face.getUVCoords(i)
            
            self.logfile.write("UV: %s\n" % (str(uv_coords)))
            # Construct a temporary OgreVertex
            ogre_vertex = OgreVertex(self, blender_vertex, uv_coords)

            # Loop through the possible vertices
            possible_vertices = self.vertex_map.get(blender_vertex.index)
            if possible_vertices == None:
                possible_vertices = []
                self.vertex_map[blender_vertex.index] = possible_vertices
            for posible_vertex in possible_vertices:
                # If a match was found, use it, otherwise create a new vertex
                if possible_vertex == ogre_vertex:
                    face.vertex_index[i] = possible_vertex.vertex_index
                    return
                
            # If a match wasn't found, this is a new vertex
            ogre_vertex.vertex_index = len(self.vertices)
            self.vertices.append(ogre_vertex)
            face.vertex_indices[i] = ogre_vertex.vertex_index

    def getFacesXML(self):
        faces_node = ogrexml.faces(count=len(self.faces))

        for face in self.faces:
            faces_node[2].append(face.getXML())

        return faces_node

    def getGeometryXML(self):
        geometry_node = ogrexml.geometry(vertexcount=len(self.vertices))
        vertexbuffer_attributes = {
            "texture_coords" : len(self.mesh.uv_textures),
            "positions" : "true",
            #"normals" : "true", 
        }
        # HACK Shouldn't assume 2 texture coordinates
        for i, uv_texture in enumerate(self.mesh.uv_textures):
            vertexbuffer_attributes["texture_coord_dimensions_" + str(i)] = "2"

        vertexbuffer_node = ogrexml.vertexbuffer(**vertexbuffer_attributes)
        geometry_node[2].append(vertexbuffer_node)

        for vertex in self.vertices:
            vertex_node = ogrexml.vertex()
            vertexbuffer_node[2].append(vertex_node)
            position = {
                'x' : vertex.blender_vertex.co.x,
                'y' : vertex.blender_vertex.co.y,
                'z' : vertex.blender_vertex.co.z
            }
            vertex_node[2].append(ogrexml.position(**position))
            #normal = {
            #    'x' : vertex.blender_vertex.normal.x,
            #    'y' : vertex.blender_vertex.normal.y,
            #    'z' : vertex.blender_vertex.normal.z
            #}
            #vertex_node[2].append(ogrexml.normal(**normal))
            
            for uv_coord in vertex.uv_coords:
                texcoord = {
                    'u' : uv_coord[0],
                    'v' : 1.0 - uv_coord[1]
                }
                vertex_node[2].append(ogrexml.texcoord(**texcoord))

        return geometry_node
        
        
class OgreFace():

    def __init__(self, submesh, face_number, vertices, indices):
        # submesh is the parent OgreSubMesh
        # face_number is the blender face number
        # vertices is all of the vertices in this face
        # indices are the indexes of the vertices which this face should use
        self.submesh = submesh
        self.face_number = face_number
        self.indices = indices
        self.vertices = []
        for i in indices:
            self.vertices.append(submesh.mesh.vertices[vertices[i]])
        # vertex_indices will be populated later; assume triangle
        self.vertex_indices = [0, 0, 0]

    def getUVCoords(self, vertex_index):
        uv_coords = []
        for uvi, uv_texture in enumerate(self.submesh.mesh.uv_textures):
            uv = uv_texture.data[self.face_number].uv
            # TODO Don't assume uv only has two coordinates
            u = uv[self.indices[vertex_index]][0]
            v = uv[self.indices[vertex_index]][1]
            uv_coords.append((u, v))
        return uv_coords
    
    def getXML(self):
        args = {}
        for n, vertex in enumerate(self.vertices):
            args["v" + str(n + 1)] = self.vertex_indices[n]
        return ogrexml.face(**args)


class OgreVertex():
    
    def __init__(self, submesh, blender_vertex, uv_coords):
        self.submesh = submesh
        self.blender_vertex = blender_vertex
        self.uv_coords = uv_coords

        # The vertex index will be set later
        self.vertex_index = 0

    def __eq__(self, obj):
        if len(self.uv_coords) != len(obj.uv_coords):
            return False
        
        for i, uv_coord in uv_coords:
            if abs(uv_coord[0] - self.uv_coords[i][0]) > 0.0000001 :
                return False
            if abs(uv_coord[1] - self.uv_coords[i][1]) > 0.0000001 :
                return False
            
        return True

    