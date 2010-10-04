
import bpy


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


def testGunship():
    mesh = getSelectedMesh()
    glass_mat = mesh.materials[0]
    