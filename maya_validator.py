import maya.cmds as cmds

class AssetValidator:
    
    def __init__(self):
        self.logs = []
    
    def log(self, message, success=True):
        """
        Logs messages to the UI log field and console.
        
        :param message: Message to log.
        :param success: Boolean indicating success or failure.
        """
        status = "SUCCESS: " if success else "FAIL: "
        self.logs.append((status + message, success))
        cmds.scrollField(self.log_field, e=True, insertText=f'{status + message}\n')

    def is_group(self, nodeName):
        """
        Checks if a node is a group.
        
        :param nodeName: Name of the node to check.
        :return: Boolean indicating if the node is a group.
        """
        try:
            children = cmds.listRelatives(nodeName, children=True)
            for child in children:
                if not cmds.ls(child, transforms=True):
                    return False
            return True
        except:
            return False
    
    def model_check(self):
        """
        Checks model file prefixes and transforms.
        """
        grps = [x for x in cmds.ls(l=True) if self.is_group(x)]
        for grp in grps:
            grp_short = grp.split('|')[-1]
            if grp_short.startswith('L_') or grp_short.startswith('R_'):
                prefix = grp_short[0:2]
                nodes = cmds.listRelatives(grp, ad=True, type='transform', f=True)
                for node in nodes:
                    node_short = node.split('|')[-1]
                    msg = ''
                    if not node_short[0:2] == prefix:
                        msg += 'Fail Prefix: %s\n' % node
                    if cmds.getAttr('%s.translateX' % node):
                        msg += 'Fail translateX: %s\n' % node
                    if cmds.getAttr('%s.translateY' % node):
                        msg += 'Fail translateY: %s\n' % node
                    if cmds.getAttr('%s.translateZ' % node):
                        msg += 'Fail translateZ: %s\n' % node
                    if cmds.getAttr('%s.rotateX' % node):
                        msg += 'Fail rotateX: %s\n' % node
                    if cmds.getAttr('%s.rotateY' % node):
                        msg += 'Fail rotateY: %s\n' % node
                    if cmds.getAttr('%s.rotateZ' % node):
                        msg += 'Fail rotateZ: %s\n' % node
                    if not cmds.getAttr('%s.scaleX' % node) == 1:
                        msg += 'Fail scaleX: %s\n' % node
                    if not cmds.getAttr('%s.scaleY' % node) == 1:
                        msg += 'Fail scaleY: %s\n' % node
                    if not cmds.getAttr('%s.scaleZ' % node) == 1:
                        msg += 'Fail scaleZ: %s\n' % node
                    if msg:
                        msg = '\n =============== CHECK  FAILS ===============\n' + msg + '============================================'
                        print(msg)
                        self.log(msg, success=False)
                    else:
                        self.log(f'{node} passed all checks.')

    def unlock_normals(self):
        """
        Unlocks normals for all geometries in the scene.
        """
        geos = cmds.ls(geometry=True)
        for geo in geos:
            cmds.polyNormalPerVertex(geo, unFreezeNormal=True)
        self.log("Normals unlocked for all geometries.")

    def soften_edges(self):
        """
        Softens edges for all geometries in the scene.
        """
        geos = cmds.ls(geometry=True)
        for geo in geos:
            cmds.polySoftEdge(geo, angle=180)
        self.log("Edges softened for all geometries.")

    # def check_mesh_names(self):
    #     """
    #     Checks if mesh names follow the naming convention based on their position along the X axis.
    #     """
    #     meshes = cmds.ls(type='mesh')
    #     for mesh in meshes:
    #         bounding_box = cmds.exactWorldBoundingBox(mesh)
    #         if bounding_box[0] < 0 and not mesh.endswith('_R'):
    #             self.log(f"{mesh} on -X axis should end with '_R'", success=False)
    #         if bounding_box[3] > 0 and not mesh.endswith('_L'):
    #             self.log(f"{mesh} on +X axis should end with '_L'", success=False)
    #     self.log("Mesh names checked.")

    def freeze_and_reset_transforms(self):
        """
        Freezes and resets transforms for all geometries in the scene.
        """
        geos = cmds.ls(geometry=True)
        # Freeze transformations
        cmds.makeIdentity(geos, apply=True, translate=True, rotate=True, scale=True, normal=False)
        self.log("Transforms frozen for all geometries.")
        # Reset transformations
        for geo in geos:
            cmds.setAttr(f'{geo}.translate', 0, 0, 0)
            cmds.setAttr(f'{geo}.rotate', 0, 0, 0)
            cmds.setAttr(f'{geo}.scale', 1, 1, 1)
        self.log("Transforms reset for all geometries.")

    def delete_history(self):
        """
        Deletes history for all geometries in the scene.
        """
        geos = cmds.ls(geometry=True)
        cmds.delete(geos, constructionHistory=True)
        self.log("History deleted for all geometries.")

    def remove_unused_materials(self):
        """
        Removes unused materials from the scene.
        """
        # Get all shading groups
        shading_groups = cmds.ls(type='shadingEngine')
        
        # Get all materials
        all_materials = cmds.ls(materials=True)
        
        # Get used materials
        used_materials = set()
        for sg in shading_groups:
            connections = cmds.listConnections(sg, type='mesh')
            if connections:
                materials = cmds.listConnections(sg + ".surfaceShader")
                if materials:
                    used_materials.update(materials)
        
        # Find unused materials
        unused_materials = set(all_materials) - used_materials
        
        # Delete unused materials
        if unused_materials:
            cmds.delete(list(unused_materials))
            self.log(f"Unused materials removed: {unused_materials}")
        else:
            self.log("No unused materials to remove.")

    def remove_namespaces(self):
        """
        Removes all namespaces from the scene except 'UI' and 'shared'.
        """
        namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        for ns in namespaces:
            if ns not in ['UI', 'shared']:
                cmds.namespace(removeNamespace=ns, mergeNamespaceWithRoot=True)
        self.log("Namespaces removed.")

    def validator(self):
        """
        Runs all validation methods.
        """
        self.model_check()
        self.unlock_normals()
        self.soften_edges()
        # self.check_mesh_names()
        self.freeze_and_reset_transforms()
        self.delete_history()
        self.remove_unused_materials()
        self.remove_namespaces()
        self.log("All validations completed.")

    def create_ui(self):
        """
        Creates the Maya UI for the Asset Validator.
        """
        if cmds.window("assetValidatorWindow", exists=True):
            cmds.deleteUI("assetValidatorWindow")
        
        window = cmds.window("assetValidatorWindow", title="Asset Validator", widthHeight=(250, 600))
        cmds.columnLayout(adjustableColumn=True)
        
        cmds.button(label="Model Check", command=lambda x: self.model_check())
        cmds.button(label="Unlock Normals", command=lambda x: self.unlock_normals())
        cmds.button(label="Soften Edges", command=lambda x: self.soften_edges())
        # cmds.button(label="Check Mesh Names", command=lambda x: self.check_mesh_names())
        cmds.button(label="Freeze Reset Transforms", command=lambda x: self.freeze_and_reset_transforms())
        cmds.button(label="Delete History", command=lambda x: self.delete_history())
        cmds.button(label="Remove Unused Materials", command=lambda x: self.remove_unused_materials())
        cmds.button(label="Remove Namespaces", command=lambda x: self.remove_namespaces())
        cmds.button(label="Run All Validations", command=lambda x: self.validator())
        
        self.log_field = cmds.scrollField(editable=False, wordWrap=True, height=200)
        
        cmds.showWindow(window)

# Create an instance of the AssetValidator and show the UI
asset_validator = AssetValidator()
asset_validator.create_ui()
