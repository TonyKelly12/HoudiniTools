import hou
import os
import re


class RedshiftMaterialTool:
    def __init__(self):
        self.project_path = hou.text.expandString("$HIP")
        self.tex_path = os.path.join(self.project_path, "tex")
        self.texture_extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".tif",
            ".tiff",
            ".exr",
            ".hdr",
            ".tx",
        ]
        self.texture_types = {
            "basecolor": ["basecolor", "diffuse", "albedo", "col", "color", "diff"],
            "roughness": ["roughness", "rough", "rgh"],
            "metallic": ["metallic", "metal", "mtl"],
            "normal": ["normal", "nrm", "norm"],
            "bump": ["bump", "bmp"],
            "displacement": ["displacement", "disp", "displace", "height"],
            "emission": ["emission", "emissive", "emit"],
            "ao": ["ao", "ambient", "occlusion"],
        }

    def check_redshift_installation(self):
        """Check if Redshift is properly installed and configured"""
        # Print Houdini version info for debugging
        print(f"Houdini Version: {hou.applicationVersionString()}")

        # List all available node types for debugging
        all_material_nodes = [
            nt.name() for nt in hou.nodeTypeCategories()["Vop"].nodeTypes().values()
        ]
        redshift_nodes = [n for n in all_material_nodes if "redshift" in n.lower()]
        print(f"Available Redshift nodes: {redshift_nodes}")

        try:
            # Check if we can access the /mat context
            if hou.node("/mat") is None:
                # Create the /mat context if it doesn't exist
                hou.node("/").createNode("mat")

            # Check if redshift_vopnet exists (this is what we'll use)
            if "redshift_vopnet" in redshift_nodes:
                print("Found redshift_vopnet node type - will use this for materials")
                return True, "Redshift appears to be properly installed."
            else:
                raise Exception("Could not find redshift_vopnet node type")

        except Exception as e:
            return False, f"Redshift check failed: {str(e)}"

    def scan_textures(self):
        """Scan the texture folder and organize textures by material sets"""
        material_sets = {}

        # Check if tex directory exists
        if not os.path.exists(self.tex_path):
            print(f"Texture directory not found: {self.tex_path}")
            return {}

        # Walk through the tex directory
        for root, dirs, files in os.walk(self.tex_path):
            # Group files first to detect UDIM patterns
            file_groups = self._group_udim_files(files)

            for file_or_group in file_groups:
                # Check if this is a single file or a UDIM group
                is_udim = isinstance(file_or_group, dict)

                if is_udim:
                    # Handle UDIM texture group
                    udim_group = file_or_group
                    base_file = udim_group["base_file"]
                    udim_files = udim_group["files"]

                    # Process the base file name (without the UDIM part)
                    file_ext = os.path.splitext(base_file)[1].lower()
                    if file_ext in self.texture_extensions:
                        # Extract material name and texture type
                        material_name = self._extract_material_name(base_file)
                        texture_type = self._identify_texture_type(base_file)

                        if material_name and texture_type:
                            # Extract mesh name from path
                            rel_path = os.path.relpath(root, self.tex_path)
                            parts = rel_path.split(os.sep)

                            if len(parts) > 0 and parts[0] != ".":
                                mesh_name = parts[0]  # First folder is mesh name

                                # Create keys for organization
                                if mesh_name not in material_sets:
                                    material_sets[mesh_name] = {}

                                if material_name not in material_sets[mesh_name]:
                                    material_sets[mesh_name][material_name] = {}

                                # Store the UDIM pattern and first file as a reference
                                first_file = os.path.join(root, udim_files[0])
                                material_sets[mesh_name][material_name][
                                    texture_type
                                ] = {
                                    "is_udim": True,
                                    "pattern": base_file,  # This is now the pattern with <UDIM> in it
                                    "sample_file": first_file,
                                    "path": root,
                                }
                else:
                    # Handle regular (non-UDIM) texture
                    file = file_or_group
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in self.texture_extensions:
                        file_path = os.path.join(root, file)

                        # Skip if this is part of a UDIM sequence (we've already processed it)
                        if self._is_udim_file(file):
                            continue

                        # Extract material name from path
                        rel_path = os.path.relpath(file_path, self.tex_path)
                        parts = rel_path.split(os.sep)

                        if len(parts) > 1:
                            mesh_name = parts[0]  # First folder is mesh name
                            # Extract material name from filename
                            material_name = self._extract_material_name(file)
                            texture_type = self._identify_texture_type(file)

                            if material_name and texture_type:
                                # Create keys for organization
                                if mesh_name not in material_sets:
                                    material_sets[mesh_name] = {}

                                if material_name not in material_sets[mesh_name]:
                                    material_sets[mesh_name][material_name] = {}

                                # Store the texture path
                                material_sets[mesh_name][material_name][
                                    texture_type
                                ] = {"is_udim": False, "file_path": file_path}

        return material_sets

    def _group_udim_files(self, files):
        """Group files that are part of UDIM sequences and regular files"""
        result = []
        udim_groups = {}

        # First pass: identify UDIM patterns and group files
        for file in files:
            if self._is_udim_file(file):
                # Extract the base pattern and UDIM value
                base_pattern, udim_value = self._extract_udim_info(file)

                if base_pattern not in udim_groups:
                    udim_groups[base_pattern] = {
                        "base_file": self._udim_pattern_to_redshift(base_pattern),
                        "files": [],
                    }

                udim_groups[base_pattern]["files"].append(file)
            else:
                # Regular file, just add it
                result.append(file)

        # Add the UDIM groups to the result
        result.extend(udim_groups.values())

        return result

    def _is_udim_file(self, filename):
        """Check if a file is part of a UDIM sequence"""
        # UDIM pattern: typically has a 4-digit number like 1001, 1002, etc.
        udim_pattern = r".*?[\._](?:u\d+_v\d+|[0-9]{4})[\._].*"
        mari_pattern = r".*?[\._](?:u\d+_v\d+)[\._].*"  # Mari-style UDIMs
        zbrush_pattern = r".*?[\._](?:[0-9]{4})[\._].*"  # ZBrush-style UDIMs

        return (
            re.match(udim_pattern, filename, re.IGNORECASE)
            or re.match(mari_pattern, filename, re.IGNORECASE)
            or re.match(zbrush_pattern, filename, re.IGNORECASE)
        )

    def _extract_udim_info(self, filename):
        """Extract the base pattern and UDIM value from a filename"""
        # Try different UDIM naming conventions

        # Mari-style: texture_u1_v1_diffuse.exr
        mari_match = re.match(
            r"(.*?)[\._](u\d+_v\d+)([\._].*)", filename, re.IGNORECASE
        )
        if mari_match:
            prefix, udim, suffix = mari_match.groups()
            # Convert to a pattern with <UDIM> placeholder
            return f"{prefix}.<UDIM>{suffix}", udim

        # ZBrush/Standard UDIM: texture_1001_diffuse.exr
        zbrush_match = re.match(
            r"(.*?)[\._]([0-9]{4})([\._].*)", filename, re.IGNORECASE
        )
        if zbrush_match:
            prefix, udim, suffix = zbrush_match.groups()
            # Convert to a pattern with <UDIM> placeholder
            return f"{prefix}.<UDIM>{suffix}", udim

        # If no pattern is found, return the filename (shouldn't happen if _is_udim_file is correct)
        return filename, None

    def _udim_pattern_to_redshift(self, pattern):
        """Convert a UDIM pattern to Redshift's expected format"""
        # Redshift uses <UDIM> tag in the file path
        return pattern

    def _extract_material_name(self, filename):
        """Extract material name from filename"""
        # Remove extension
        base = os.path.splitext(filename)[0]

        # Remove UDIM part if present
        base = re.sub(r"[\._](?:u\d+_v\d+|[0-9]{4})[\._]", "_", base)

        # Common naming patterns (e.g., "materialName_basecolor")
        pattern = (
            r"^(.*?)(?:_(?:" + "|".join(sum(self.texture_types.values(), [])) + "))$"
        )
        match = re.match(pattern, base, re.IGNORECASE)

        if match:
            return match.group(1)

        # If no pattern match, just return the base name
        return base

    def _identify_texture_type(self, filename):
        """Identify texture type from filename"""
        # Remove UDIM part if present
        clean_name = re.sub(r"[\._](?:u\d+_v\d+|[0-9]{4})[\._]", "_", filename.lower())
        base = os.path.splitext(clean_name)[0].lower()

        for tex_type, keywords in self.texture_types.items():
            for keyword in keywords:
                if f"_{keyword}" in base.lower() or base.lower().endswith(f"{keyword}"):
                    return tex_type

        # Default to basecolor if can't identify
        if any(base.lower().endswith(ext) for ext in self.texture_extensions):
            return "basecolor"

        return None

    def check_material_exists(self, mat_context, material_name):
        """Check if material already exists in the given material context"""
        if mat_context is None:
            return None

        # Check for existing material
        for node in mat_context.children():
            if node.name() == material_name or node.name() == f"RS_{material_name}":
                return node

        return None

    def create_material_context(self):
        """Create or get the material context, safely handling errors"""
        try:
            # Get or create the /mat context first
            if hou.node("/mat") is None:
                hou.node("/").createNode("mat", "mat")

            return hou.node("/mat")

        except Exception as e:
            raise Exception(f"Failed to create material context: {str(e)}")

    def create_redshift_material(self, mat_context, material_name, textures):
        """Create a Redshift material with the given textures"""
        if mat_context is None:
            print("No valid material context found")
            return None

        # Create material node using redshift_vopnet
        rs_mat_name = f"RS_{material_name}"

        try:
            # Create the redshift_vopnet node
            rs_mat = mat_context.createNode("redshift_vopnet", rs_mat_name)
            print(f"Successfully created material node: {rs_mat.path()}")

            # Find the automatically created material nodes
            material_node = None
            redshift_material_node = None

            # Look for automatically created nodes
            for child in rs_mat.children():
                if child.type().name() == "redshift::StandardMaterial":
                    material_node = child
                    print(f"Found existing StandardMaterial node: {child.name()}")
                elif child.type().name() == "redshift_material":
                    redshift_material_node = child
                    print(f"Found existing redshift_material node: {child.name()}")

            # Create nodes if they don't exist
            if material_node is None:
                material_node = rs_mat.createNode(
                    "redshift::StandardMaterial", "StandardMaterial"
                )
                print(f"Created StandardMaterial node")

            if redshift_material_node is None:
                redshift_material_node = rs_mat.createNode(
                    "redshift_material", "redshift_material"
                )
                print(f"Created redshift_material node")

            # Connect StandardMaterial to redshift_material if not already connected
            try:
                # Check if already connected
                if redshift_material_node.input(0) is None:
                    # Connect StandardMaterial to redshift_material
                    redshift_material_node.setInput(0, material_node, 0)
                    print(f"Connected StandardMaterial to redshift_material")
            except Exception as e:
                print(
                    f"Warning: Failed to connect StandardMaterial to redshift_material: {str(e)}"
                )

            # Process all texture types (except normal, bump, and displacement)
            for tex_type, tex_info in textures.items():
                if tex_type in ["normal", "bump", "displacement"]:
                    # Skip these - handle them separately
                    continue

                # Create texture node
                try:
                    tex_node = self._create_texture_node(rs_mat, tex_type, tex_info)

                    # Connect texture to material based on type
                    try:
                        if tex_type == "basecolor":
                            material_node.setNamedInput("base_color", tex_node, 0)
                            print(f"Connected basecolor texture")
                        elif tex_type == "roughness":
                            material_node.setNamedInput("refl_roughness", tex_node, 0)
                            print(f"Connected roughness texture")
                        elif tex_type == "metallic":
                            material_node.setNamedInput("metalness", tex_node, 0)
                            print(f"Connected metallic texture")
                        elif tex_type == "emission":
                            material_node.setNamedInput("emission_color", tex_node, 0)
                            print(f"Connected emission texture")
                        elif tex_type == "ao":
                            material_node.setNamedInput("overall_color", tex_node, 0)
                            print(f"Connected ambient occlusion texture")
                    except Exception as e:
                        print(
                            f"Warning: Failed to connect {tex_type} texture: {str(e)}"
                        )
                except Exception as e:
                    print(
                        f"Warning: Failed to create {tex_type} texture node: {str(e)}"
                    )

            # Handle normal and bump maps
            bump_node = None

            if "normal" in textures or "bump" in textures:
                try:
                    # Create bump map node
                    bump_node = rs_mat.createNode("redshift::BumpMap", "bump_map")

                    # Process normal map
                    if "normal" in textures:
                        normal_tex = self._create_texture_node(
                            rs_mat, "normal", textures["normal"]
                        )

                        # Set to normal map mode
                        try:
                            # First try standard parameter name
                            if bump_node.parm("inputType") is not None:
                                bump_node.parm("inputType").set(1)  # 1 = Normal Map
                            # Try alternative parameter name
                            elif bump_node.parm("input_type") is not None:
                                bump_node.parm("input_type").set(1)
                        except Exception as e:
                            print(
                                f"Warning: Could not set bump node to normal map mode: {str(e)}"
                            )

                        # Set Input Map Type to Tangent-Space Normal
                        try:
                            # Try standard parameter name
                            if bump_node.parm("inputMapType") is not None:
                                bump_node.parm("inputMapType").set(
                                    1
                                )  # 1 = Tangent-Space Normal
                            # Try alternative parameter name
                            elif bump_node.parm("input_map_type") is not None:
                                bump_node.parm("input_map_type").set(1)
                            # Try another alternative - some Redshift versions use different naming
                            elif bump_node.parm("normal_map_type") is not None:
                                bump_node.parm("normal_map_type").set(1)
                            print("Set normal map to Tangent-Space Normal")
                        except Exception as e:
                            print(f"Warning: Could not set normal map type: {str(e)}")

                        # Connect normal texture to bump node
                        bump_node.setInput(0, normal_tex, 0)
                        print(f"Connected normal map to bump node")

                    # Process bump map
                    if "bump" in textures:
                        bump_tex = self._create_texture_node(
                            rs_mat, "bump", textures["bump"]
                        )

                        if "normal" in textures:
                            # If we already have a normal map, connect bump to input 1
                            bump_node.setInput(1, bump_tex, 0)
                            print(f"Connected bump map to bump node input 1")
                        else:
                            # Otherwise, set to bump map mode and connect to input 0
                            try:
                                bump_node.parm("inputType").set(0)  # 0 = Bump Map
                            except Exception:
                                try:
                                    bump_node.parm("input_type").set(0)
                                except Exception as e:
                                    print(
                                        f"Warning: Could not set bump node to bump map mode: {str(e)}"
                                    )

                            bump_node.setInput(0, bump_tex, 0)
                            print(f"Connected bump map to bump node input 0")

                    # REMOVED: Connect bump node to material_node
                    # material_node.setNamedInput("bump_input", bump_node, 0)

                    # Connect bump node to redshift_material
                    redshift_material_node.setInput(2, bump_node, 0)
                    print(f"Connected bump node to redshift_material")
                except Exception as e:
                    print(f"Warning: Failed to process normal/bump maps: {str(e)}")

            # Handle displacement
            if "displacement" in textures:
                try:
                    # Create texture node
                    disp_tex = self._create_texture_node(
                        rs_mat, "displacement", textures["displacement"]
                    )

                    # Create displacement node
                    disp_node = rs_mat.createNode(
                        "redshift::Displacement", "displacement"
                    )

                    # Connect texture to displacement node
                    disp_node.setInput(0, disp_tex, 0)
                    print(f"Connected displacement texture to displacement node")

                    # Connect displacement node to redshift_material
                    redshift_material_node.setInput(1, disp_node, 0)
                    print(f"Connected displacement node to redshift_material")
                except Exception as e:
                    print(f"Warning: Failed to process displacement map: {str(e)}")

            # Make sure redshift_material is the output
            try:
                # Find the output node
                output_node = None
                for child in rs_mat.children():
                    if child.type().name() == "subnet_output":
                        output_node = child
                        break

                # Create output node if it doesn't exist
                if output_node is None:
                    output_node = rs_mat.createNode("subnet_output", "output")

                # Connect redshift_material to output
                output_node.setInput(0, redshift_material_node, 0)
                print(f"Connected redshift_material to output node")
            except Exception as e:
                print(f"Warning: Failed to set up output connection: {str(e)}")

            # Layout the network
            try:
                rs_mat.layoutChildren()
            except Exception as e:
                print(f"Warning: Could not layout children: {str(e)}")

            return rs_mat
        except Exception as e:
            if "rs_mat" in locals():
                try:
                    rs_mat.destroy()
                except:
                    pass
            raise Exception(f"Error creating material: {str(e)}")

    def _create_texture_node(self, mat_builder, tex_type, texture_info):
        """Create a texture node with the given texture info"""
        try:
            # Create TextureSampler node
            texture_node = mat_builder.createNode(
                "redshift::TextureSampler", f"{tex_type}_texture"
            )

            # Set texture file path
            if isinstance(texture_info, dict) and "is_udim" in texture_info:
                if texture_info["is_udim"]:
                    # UDIM texture
                    udim_pattern = texture_info["pattern"]
                    filepath = os.path.join(texture_info["path"], udim_pattern)
                    texture_node.parm("tex0").set(filepath)

                    # Try to enable UDIM support if the parameter exists
                    if texture_node.parm("tex0_udim") is not None:
                        texture_node.parm("tex0_udim").set(1)
                else:
                    # Regular texture
                    texture_node.parm("tex0").set(texture_info["file_path"])
            else:
                # Legacy format - just a path
                texture_node.parm("tex0").set(texture_info)

            # Set appropriate color space
            if texture_node.parm("tex0_colorSpace") is not None:
                if tex_type in ["basecolor", "emission"]:
                    texture_node.parm("tex0_colorSpace").set("sRGB")
                else:
                    texture_node.parm("tex0_colorSpace").set("Raw")

            # Set up channel extraction for certain texture types
            if tex_type in ["roughness", "metallic", "ao", "displacement"]:
                # Set to use a specific color channel (typically R)
                if texture_node.parm("tex0_useColorChannel") is not None:
                    texture_node.parm("tex0_useColorChannel").set(1)
                if texture_node.parm("tex0_channel") is not None:
                    texture_node.parm("tex0_channel").set(0)  # Use R channel

            print(f"Created {tex_type} texture node")
            return texture_node

        except Exception as e:
            raise Exception(f"Error creating texture node for {tex_type}: {str(e)}")

    def run(self):
        """Main function to run the material creation tool"""
        try:
            # First check if Redshift is properly installed
            rs_ok, rs_message = self.check_redshift_installation()
            if not rs_ok:
                raise Exception(f"Redshift check failed: {rs_message}")

            print("Redshift check: OK")

            # Get material context
            try:
                mat_context = self.create_material_context()
            except Exception as e:
                raise Exception(f"Failed to create material context: {str(e)}")

            # Scan textures
            material_sets = self.scan_textures()

            if not material_sets:
                print("No valid texture sets found")
                return

            # Create materials
            created_count = 0
            existed_count = 0

            for mesh_name, materials in material_sets.items():
                print(f"Processing materials for mesh: {mesh_name}")

                for material_name, textures in materials.items():
                    # Check if material already exists
                    existing_mat = self.check_material_exists(
                        mat_context, material_name
                    )

                    if existing_mat:
                        print(f"  Material already exists: {material_name}")
                        existed_count += 1
                    else:
                        try:
                            # Create new material
                            new_mat = self.create_redshift_material(
                                mat_context, material_name, textures
                            )
                            if new_mat:
                                print(f"  Created new material: {material_name}")
                                created_count += 1
                        except Exception as e:
                            print(
                                f"  Error creating material {material_name}: {str(e)}"
                            )

            print(
                f"Summary: Created {created_count} new materials, {existed_count} already existed"
            )

            # Layout nodes in material context
            mat_context.layoutChildren()

        except Exception as e:
            error_message = f"Error running Redshift Material Tool: {str(e)}"
            print(error_message)
            hou.ui.displayMessage(error_message, severity=hou.severityType.Error)


# When running the tool, execute it directly
RedshiftMaterialTool().run()
