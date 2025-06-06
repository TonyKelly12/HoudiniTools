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

        print(f"Scanning for textures in: {self.tex_path}")

        # Walk through the tex directory
        for root, dirs, files in os.walk(self.tex_path):
            # Debug info
            udim_files = [f for f in files if self._is_udim_file(f)]
            if udim_files:
                print(f"Found potential UDIM files in {root}: {len(udim_files)} files")
                for f in udim_files[:3]:  # Print first few as examples
                    print(f"  Example UDIM file: {f}")

            # Group files first to detect UDIM patterns
            file_groups = self._group_udim_files(files)

            # Debug info for UDIM groups found
            udim_groups = [g for g in file_groups if isinstance(g, dict)]
            if udim_groups:
                print(f"Identified {len(udim_groups)} UDIM texture groups in {root}")
                for group in udim_groups:
                    print(
                        f"  - UDIM pattern: {group['base_file']} "
                        f"with {len(group['files'])} tiles"
                    )

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
                        "base_file": base_pattern,
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
        # Handle Redshift's UDIM format
        if "<UDIM>" in filename:
            return True

        # Handle Houdini's native format
        if "%(UDIM)d" in filename:
            return True

        # Substance Painter naming convention: name.1001.exr or name.1001
        # Format seen in Houdini: name.1001.exr
        substance_udim = r".*?\.[0-9]{4}(\..+)?$"

        # Standard UDIM (4 digits with separators)
        udim_standard = r".*?([\._])[0-9]{4}([\._].*|$)"

        # Mari-style UDIMs (u#_v#)
        udim_mari = r".*?([\._])u\d+_v\d+([\._].*|$)"

        # Check all patterns with case insensitivity
        return (
            re.match(substance_udim, filename, re.IGNORECASE) is not None
            or re.match(udim_standard, filename, re.IGNORECASE) is not None
            or re.match(udim_mari, filename, re.IGNORECASE) is not None
        )

    def _extract_udim_info(self, filename):
        """Extract the base pattern and UDIM value from a filename"""
        # Check if <UDIM> is already in the filename (Redshift format)
        if "<UDIM>" in filename:
            # Already has Redshift UDIM tag - just return it
            return filename, "<UDIM>"

        # Check if %(UDIM)d is in the filename (Houdini native format)
        if "%(UDIM)d" in filename:
            # Convert from Houdini to Redshift format
            return filename.replace("%(UDIM)d", "<UDIM>"), "<UDIM>"

        # Substance Painter naming convention: name.1001.exr
        substance_match = re.match(
            r"(.*?)\.([0-9]{4})(\..+)?$", filename, re.IGNORECASE
        )
        if substance_match:
            base, udim, ext = substance_match.groups()
            # If ext is None, set it to empty string
            ext = ext or ""
            # Convert to a pattern with <UDIM> placeholder in Redshift format
            return f"{base}.<UDIM>{ext}", udim

        # Try different UDIM naming conventions

        # Mari-style: texture_u1_v1_diffuse.exr
        mari_match = re.match(
            r"(.*?)([\._])(u\d+_v\d+)([\._].*)", filename, re.IGNORECASE
        )
        if mari_match:
            prefix, separator, udim, suffix = mari_match.groups()
            # Convert to dot-based format for Redshift with <UDIM>
            base_name = prefix
            if suffix.startswith("_") or suffix.startswith("."):
                suffix = suffix[1:]
            ext = os.path.splitext(suffix)[1]
            clean_suffix = os.path.splitext(suffix)[0]
            return f"{base_name}_{clean_suffix}.<UDIM>{ext}", udim

        # Mari-style at end of filename: texture_diffuse_u1_v1.exr
        mari_end_match = re.match(
            r"(.*?)([\._])(u\d+_v\d+)(\..+)$", filename, re.IGNORECASE
        )
        if mari_end_match:
            prefix, separator, udim, ext = mari_end_match.groups()
            # Convert to Redshift format
            return f"{prefix}.<UDIM>{ext}", udim

        # ZBrush/Standard UDIM: texture_1001_diffuse.exr
        zbrush_match = re.match(
            r"(.*?)([\._])([0-9]{4})([\._].*)", filename, re.IGNORECASE
        )
        if zbrush_match:
            prefix, separator, udim, suffix = zbrush_match.groups()
            # Convert to Redshift format
            base_name = prefix
            if suffix.startswith("_") or suffix.startswith("."):
                suffix = suffix[1:]
            ext = os.path.splitext(suffix)[1]
            clean_suffix = os.path.splitext(suffix)[0]
            return f"{base_name}_{clean_suffix}.<UDIM>{ext}", udim

        # UDIM at end of filename: texture_diffuse_1001.exr
        udim_end_match = re.match(
            r"(.*?)([\._])([0-9]{4})(\..+)$", filename, re.IGNORECASE
        )
        if udim_end_match:
            prefix, separator, udim, ext = udim_end_match.groups()
            # Convert to Redshift format
            return f"{prefix}.<UDIM>{ext}", udim

        # If no pattern is found, return the filename (shouldn't happen if _is_udim_file is correct)
        return filename, None

    def _extract_material_name(self, filename):
        """Extract material name from filename"""
        # Remove extension
        base = os.path.splitext(filename)[0]

        # Handle Substance Painter naming convention: name.1001.exr
        # Check if there's another dot with 4 digits after it
        substance_match = re.match(r"(.*?)\.([0-9]{4})$", base)
        if substance_match:
            base = substance_match.group(1)

        # Remove UDIM part if present (but preserve the base name)
        # We need to handle the UDIM tag cases separately
        if "%(UDIM)d" in base:
            # For patterns that have the Houdini UDIM tag
            base = base.replace("_%(UDIM)d_", "_").replace(".%(UDIM)d.", ".")
        elif "<UDIM>" in base:
            # For patterns that have the Redshift UDIM tag
            base = base.replace("_<UDIM>_", "_").replace(".<UDIM>.", ".")
        else:
            # For actual UDIM file names with numbers or Mari style
            base = base.replace("_u1_v1_", "_").replace("_u2_v1_", "_")
            # Remove standard UDIM numbers from within the name
            if "." in base:
                parts = base.split(".")
                cleaned_parts = []
                for part in parts:
                    if len(part) == 4 and part.isdigit():
                        continue
                    cleaned_parts.append(part)
                base = ".".join(cleaned_parts)

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
        # Remove extension
        filename_no_ext = os.path.splitext(filename)[0]

        # Remove UDIM numbering (for Substance Painter format: name.1001)
        substance_match = re.match(r"(.*?)\.([0-9]{4})$", filename_no_ext)
        if substance_match:
            filename_no_ext = substance_match.group(1)

        # Remove UDIM parts from the name
        if "%(UDIM)d" in filename_no_ext:
            filename_no_ext = filename_no_ext.replace("_%(UDIM)d_", "_").replace(
                ".%(UDIM)d.", "."
            )
        elif "<UDIM>" in filename_no_ext:
            filename_no_ext = filename_no_ext.replace("_<UDIM>_", "_").replace(
                ".<UDIM>.", "."
            )

        # Handle standard UDIM numbering
        parts = filename_no_ext.split(".")
        clean_parts = []
        for part in parts:
            if len(part) == 4 and part.isdigit():
                continue
            clean_parts.append(part)
        clean_name = ".".join(clean_parts)

        # For Substance Painter naming convention: base_Color, base_Normal, etc.
        for tex_type, keywords in self.texture_types.items():
            for keyword in keywords:
                if f"_{keyword}" in clean_name.lower() or clean_name.lower().endswith(
                    f"{keyword}"
                ):
                    return tex_type

        # Default to basecolor if can't identify
        if any(
            filename_no_ext.lower().endswith(ext) for ext in self.texture_extensions
        ):
            return "basecolor"

        return None

    def check_material_exists(self, mat_context, material_name):
        """Check if material already exists in the given material context"""
        if mat_context is None:
            return None

        # Sanitize material name for checking - remove any UDIM tags or tile numbers
        clean_name = material_name.replace("<UDIM>", "UDIM")
        clean_name = clean_name.replace("%(UDIM)d", "UDIM")

        # Remove UDIM tile numbers at the end (like .1001)
        if "." in clean_name:
            parts = clean_name.split(".")
            if len(parts) >= 2 and parts[-1].isdigit() and len(parts[-1]) == 4:
                # If the last part is a 4-digit number (UDIM), remove it
                clean_name = ".".join(parts[:-1])

        # Check for existing material with various possible names
        for node in mat_context.children():
            node_name = node.name()
            # Remove any RS_ prefix for comparison
            if node_name.startswith("RS_"):
                node_name = node_name[3:]

            # Check if the base names match (ignoring UDIM parts)
            if node_name == clean_name or node_name == material_name:
                return node

            # Also check with RS_ prefix
            if (
                node.name() == f"RS_{clean_name}"
                or node.name() == f"RS_{material_name}"
            ):
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

        # Clean up material name - remove any UDIM tags which cause node creation problems
        clean_material_name = material_name.replace("<UDIM>", "UDIM")
        clean_material_name = clean_material_name.replace("%(UDIM)d", "UDIM")

        # Remove UDIM tile numbers at the end (like .1001)
        if "." in clean_material_name:
            parts = clean_material_name.split(".")
            if len(parts) >= 2 and parts[-1].isdigit() and len(parts[-1]) == 4:
                # If the last part is a 4-digit number (UDIM), remove it
                clean_material_name = ".".join(parts[:-1])

        # Create material node using redshift_vopnet
        rs_mat_name = f"RS_{clean_material_name}"

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
                    # First try standard name
                    try:
                        output_node = rs_mat.createNode("subnet_output", "output")
                    except:
                        try:
                            # Try alternative name used in some Houdini versions
                            output_node = rs_mat.createNode("output", "output")
                        except Exception as e2:
                            print(f"Warning: Could not create output node: {str(e2)}")
                            # Will try to use existing output node

                # Find output node one more time if we couldn't create it
                if output_node is None:
                    for child in rs_mat.children():
                        if child.type().name() == "output" or child.name() == "output":
                            output_node = child
                            break

                # Connect redshift_material to output if we found/created an output node
                if output_node is not None:
                    output_node.setInput(0, redshift_material_node, 0)
                    print(f"Connected redshift_material to output node")
                else:
                    print(
                        "Warning: Could not find or create output node. Material may not work correctly."
                    )
            except Exception as e:
                print(f"Warning: Failed to set up output connection: {str(e)}")

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

                    # Convert %(UDIM)d to <UDIM> if necessary
                    if "%(UDIM)d" in udim_pattern:
                        udim_pattern = udim_pattern.replace("%(UDIM)d", "<UDIM>")

                    # Get the relative path from the project directory
                    rel_path = os.path.relpath(texture_info["path"], self.project_path)

                    # Construct a $HIP-based path
                    if rel_path.startswith("tex"):
                        filepath = f"$HIP/{rel_path}/{udim_pattern}"
                    else:
                        filepath = f"$HIP/{rel_path}/{udim_pattern}"

                    # Replace backslashes with forward slashes for Houdini
                    filepath = filepath.replace("\\", "/")

                    # Set the texture path
                    texture_node.parm("tex0").set(filepath)

                    print(f"Setting UDIM texture path: {filepath}")

                    # For Redshift's UDIM format, we need to enable the UDIM flags
                    # Try all known parameter names to ensure compatibility

                    # 1. Set udim flag
                    try:
                        if texture_node.parm("tex0_udim") is not None:
                            texture_node.parm("tex0_udim").set(1)
                            print("Set tex0_udim parameter")
                    except Exception as e:
                        print(f"Warning: Could not set tex0_udim: {str(e)}")

                    # 2. Set sequence type to UDIM (1)
                    sequence_type_set = False
                    for param_name in ["tex0_sequence_type", "tex0_sequenceType"]:
                        try:
                            if texture_node.parm(param_name) is not None:
                                texture_node.parm(param_name).set(1)  # 1 = UDIM
                                sequence_type_set = True
                                print(f"Set {param_name} parameter to UDIM (1)")
                                break
                        except Exception as e:
                            print(f"Warning: Could not set {param_name}: {str(e)}")

                    # 3. Set "Load as sequence" flag
                    sequence_load_set = False
                    for param_name in ["tex0_load_as_sequence", "tex0_loadAsSequence"]:
                        try:
                            if texture_node.parm(param_name) is not None:
                                texture_node.parm(param_name).set(1)
                                sequence_load_set = True
                                print(f"Set {param_name} parameter")
                                break
                        except Exception as e:
                            print(f"Warning: Could not set {param_name}: {str(e)}")

                    # 4. Check if we set all necessary parameters
                    if sequence_type_set and sequence_load_set:
                        print(f"Successfully configured UDIM sequence for {tex_type}")
                    else:
                        print(
                            f"Warning: Could not fully configure UDIM sequence for {tex_type}"
                        )

                    # 5. Additional debug info - show the Redshift format
                    print(f"UDIM pattern used: {udim_pattern}")
                else:
                    # Regular texture (non-UDIM)
                    # Get the relative path from the project directory
                    rel_path = os.path.relpath(
                        os.path.dirname(texture_info["file_path"]), self.project_path
                    )

                    # Construct a $HIP-based path
                    filename = os.path.basename(texture_info["file_path"])
                    if rel_path.startswith("tex"):
                        filepath = f"$HIP/{rel_path}/{filename}"
                    else:
                        filepath = f"$HIP/{rel_path}/{filename}"

                    # Replace backslashes with forward slashes for Houdini
                    filepath = filepath.replace("\\", "/")

                    texture_node.parm("tex0").set(filepath)
            else:
                # Legacy format - just a path - try to convert to $HIP if possible
                try:
                    path_str = str(texture_info)
                    if os.path.isabs(path_str):
                        rel_path = os.path.relpath(
                            os.path.dirname(path_str), self.project_path
                        )
                        filename = os.path.basename(path_str)
                        filepath = f"$HIP/{rel_path}/{filename}".replace("\\", "/")
                        texture_node.parm("tex0").set(filepath)
                    else:
                        texture_node.parm("tex0").set(texture_info)
                except:
                    # Fall back to original path if conversion fails
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

            # Debug output
            if material_sets:
                print("DEBUG: Found material sets:")
                for mesh_name, materials in material_sets.items():
                    print(f"  Mesh: {mesh_name}")
                    for material_name, textures in materials.items():
                        print(f"    Material: {material_name}")
                        print(f"    Textures: {list(textures.keys())}")
                        # Debug texture paths
                        for tex_type, tex_info in textures.items():
                            if (
                                isinstance(tex_info, dict)
                                and "is_udim" in tex_info
                                and tex_info["is_udim"]
                            ):
                                print(
                                    f"      {tex_type}: {tex_info['pattern']} (UDIM sequence)"
                                )
                            elif isinstance(tex_info, dict) and "file_path" in tex_info:
                                print(f"      {tex_type}: {tex_info['file_path']}")
                            else:
                                print(f"      {tex_type}: {tex_info}")

            # Process material sets by mesh
            for mesh_name, materials in material_sets.items():
                print(f"Processing materials for mesh: {mesh_name}")

                # Group UDIM textures of the same material type together
                consolidated_materials = {}

                for material_name, textures in materials.items():
                    # Clean material name: replace UDIM tags and remove tile numbers
                    base_material_name = material_name.replace("%(UDIM)d", "UDIM")
                    base_material_name = base_material_name.replace("<UDIM>", "UDIM")

                    # Remove UDIM tile numbers at the end (like .1001)
                    if "." in base_material_name:
                        parts = base_material_name.split(".")
                        if (
                            len(parts) >= 2
                            and parts[-1].isdigit()
                            and len(parts[-1]) == 4
                        ):
                            # If the last part is a 4-digit number (UDIM), remove it
                            base_material_name = ".".join(parts[:-1])

                    # For Substance Painter naming convention
                    if "." in base_material_name:
                        parts = base_material_name.split(".")
                        for i, part in enumerate(parts):
                            if part.isdigit() and len(part) == 4:
                                # Found a UDIM number, remove it
                                base_material_name = ".".join(
                                    parts[:i] + parts[i + 1 :]
                                )
                                break

                    # Extract the base material name without texture type
                    # For example: "BarBase_Bar_combo" from "BarBase_Bar_combo_Color.UDIM"
                    for tex_type, keywords in self.texture_types.items():
                        for keyword in keywords:
                            if f"_{keyword}" in base_material_name.lower():
                                # Split at the texture type
                                parts = base_material_name.lower().split(f"_{keyword}")
                                if parts and parts[0]:
                                    base_material_name = parts[0]
                                break

                    # Create base material entry if needed
                    if base_material_name not in consolidated_materials:
                        consolidated_materials[base_material_name] = {}

                    # Merge texture info
                    for tex_type, tex_info in textures.items():
                        if tex_type not in consolidated_materials[base_material_name]:
                            consolidated_materials[base_material_name][
                                tex_type
                            ] = tex_info

                # Debug output
                if consolidated_materials:
                    print("DEBUG: Consolidated materials:")
                    for material_name, textures in consolidated_materials.items():
                        print(f"  Material: {material_name}")
                        print(f"  Textures: {list(textures.keys())}")
                        # Debug texture paths
                        for tex_type, tex_info in textures.items():
                            if (
                                isinstance(tex_info, dict)
                                and "is_udim" in tex_info
                                and tex_info["is_udim"]
                            ):
                                print(
                                    f"    {tex_type}: {tex_info['pattern']} (UDIM sequence)"
                                )
                            elif isinstance(tex_info, dict) and "file_path" in tex_info:
                                print(f"    {tex_type}: {tex_info['file_path']}")
                            else:
                                print(f"    {tex_type}: {tex_info}")

                # Create the consolidated materials
                for material_name, textures in consolidated_materials.items():
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

            # Print summary
            print(
                f"Summary: Created {created_count} new materials, {existed_count} already existed"
            )

            # Layout nodes in material context
            try:
                mat_context.layoutChildren()
            except Exception as e:
                print(f"Warning: Could not layout children: {str(e)}")

        except Exception as e:
            error_message = f"Error running Redshift Material Tool: {str(e)}"
            print(error_message)
            hou.ui.displayMessage(error_message, severity=hou.severityType.Error)


# When running the tool, execute it directly
RedshiftMaterialTool().run()
