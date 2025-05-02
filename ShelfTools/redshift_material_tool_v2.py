import hou
import os
import re
from PySide2 import QtCore, QtWidgets


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
            "translucency": ["translucency", "translucent", "sss"],
            "alpha": ["alpha", "opacity", "transparency"],
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
        print(f"Using project path: {self.project_path}")

        # Walk through the texture directory
        for root, dirs, files in os.walk(self.tex_path):
            # Debug info
            print(f"Checking directory: {root}")
            print(f"Contains {len(files)} files")

            # Skip empty directories
            if not files:
                continue

            # Check if there are any texture files
            texture_files = [
                f
                for f in files
                if any(f.lower().endswith(ext) for ext in self.texture_extensions)
            ]
            if not texture_files:
                print(f"No texture files found in {root}")
                continue

            print(f"Found {len(texture_files)} potential texture files")

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

            # Extract mesh name from path
            rel_path = os.path.relpath(root, self.tex_path)

            # Get mesh name - either first subdirectory or directory name if we're at root
            if rel_path == ".":
                # We're directly in the texture directory, use directory name
                mesh_name = os.path.basename(root)
            else:
                # We're in a subdirectory, use first component of path
                parts = rel_path.split(os.sep)
                mesh_name = (
                    parts[0] if parts and parts[0] != "." else os.path.basename(root)
                )

            # Process UDIM groups first
            for file_or_group in file_groups:
                # Only process UDIM groups here
                if not isinstance(file_or_group, dict):
                    continue

                # Handle UDIM texture group
                udim_group = file_or_group
                base_file = udim_group["base_file"]
                udim_files = udim_group["files"]

                # Process the base file name (without the UDIM part)
                file_ext = os.path.splitext(base_file)[1].lower()
                if file_ext not in self.texture_extensions:
                    continue

                # Extract material name and texture type
                material_name = self._extract_material_name(base_file)
                texture_type = self._identify_texture_type(base_file)

                if not (material_name and texture_type):
                    continue

                # Create keys for organization
                if mesh_name not in material_sets:
                    material_sets[mesh_name] = {}

                if material_name not in material_sets[mesh_name]:
                    material_sets[mesh_name][material_name] = {}

                # Store the UDIM pattern and first file as a reference
                first_file = os.path.join(root, udim_files[0])
                material_sets[mesh_name][material_name][texture_type] = {
                    "is_udim": True,
                    "pattern": base_file,  # This is the pattern with <UDIM> in it
                    "sample_file": first_file,
                    "path": root,
                }

                print(
                    f"Added UDIM texture {texture_type} to material {material_name} (mesh: {mesh_name})"
                )

            # Now process regular files
            for file_or_group in file_groups:
                # Only process regular files here
                if isinstance(file_or_group, dict):
                    continue

                # Handle regular (non-UDIM) texture
                file = file_or_group
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext not in self.texture_extensions:
                    continue

                # Skip if this is part of a UDIM sequence (we've already processed it)
                if self._is_udim_file(file):
                    continue

                # Extract material name and texture type
                material_name = self._extract_material_name(file)
                texture_type = self._identify_texture_type(file)

                if not (material_name and texture_type):
                    continue

                # Create keys for organization
                if mesh_name not in material_sets:
                    material_sets[mesh_name] = {}

                if material_name not in material_sets[mesh_name]:
                    material_sets[mesh_name][material_name] = {}

                # Store the texture path
                file_path = os.path.join(root, file)
                material_sets[mesh_name][material_name][texture_type] = {
                    "is_udim": False,
                    "file_path": file_path,
                }

                print(
                    f"Added regular texture {texture_type} to material {material_name} (mesh: {mesh_name})"
                )

        # Debug dump of material sets structure
        for mesh_name, materials in material_sets.items():
            print(f"Mesh '{mesh_name}': {len(materials)} materials")
            for material_name, textures in materials.items():
                print(f"  Material '{material_name}': {len(textures)} textures")
                for tex_type, tex_info in textures.items():
                    if isinstance(tex_info, dict) and tex_info.get("is_udim", False):
                        print(f"    - {tex_type}: UDIM pattern '{tex_info['pattern']}'")
                    else:
                        print(f"    - {tex_type}: Regular texture")

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
        """Extract base material name without texture types and UDIM tags"""
        # Remove extension
        base = os.path.splitext(filename)[0]

        # Store original base for debugging
        original_base = base
        print(f"Extracting material name from: {base}")

        # Remove UDIM placeholders first
        if "<UDIM>" in base:
            base = base.replace("<UDIM>", "")
            print(f"  - Removed Redshift UDIM tag: {base}")

        if "%(UDIM)d" in base:
            base = base.replace("%(UDIM)d", "")
            print(f"  - Removed Houdini UDIM tag: {base}")

        # Remove standard UDIM tile numbers (like _1001_, .1001.)
        udim_standard = re.sub(r"([\._])[0-9]{4}([\._])", r"\1\2", base)
        if udim_standard != base:
            base = udim_standard
            print(f"  - Removed standard UDIM format: {base}")

        # Remove UDIM tile numbers at the end (like _1001)
        udim_end = re.sub(r"([\._])[0-9]{4}$", "", base)
        if udim_end != base:
            base = udim_end
            print(f"  - Removed UDIM tile at end: {base}")

        # Remove Mari-style coordinates (like _u1_v1_)
        mari_style = re.sub(r"(_u\d+_v\d+)", "", base)
        if mari_style != base:
            base = mari_style
            print(f"  - Removed Mari-style coordinates: {base}")

        # Now carefully remove texture type keywords from the name
        for tex_type, keywords in self.texture_types.items():
            for keyword in keywords:
                # Check for texture type at the end (_basecolor, _diffuse, etc.)
                pattern = r"(.*?)(?:[_\.])(" + re.escape(keyword) + r")$"
                match = re.match(pattern, base, re.IGNORECASE)
                if match:
                    base = match.group(1)
                    print(f"  - Removed texture type '{keyword}' from end: {base}")
                    continue

                # Check for texture type in the middle (_basecolor_, _diffuse_, etc.)
                pattern = r"(.*?)(?:[_\.])(" + re.escape(keyword) + r")(?:[_\.])(.*)"
                match = re.match(pattern, base, re.IGNORECASE)
                if match:
                    base = match.group(1) + match.group(3)
                    print(f"  - Removed texture type '{keyword}' from middle: {base}")
                    continue

        # Special cases that might not be in the texture_types dictionary
        extra_keywords = [
            "Color",
            "DisplaceHeightField",
            "EmissionColor",
            "Metalness",
            "Normal",
            "Roughness",
            "alpha",
            "translucency",
            "AO",
            "height",
        ]

        for keyword in extra_keywords:
            # Check for these keywords at the end (_Color, _Normal, etc.)
            pattern = r"(.*?)(?:[_\.])(" + re.escape(keyword) + r")$"
            match = re.match(pattern, base, re.IGNORECASE)
            if match:
                base = match.group(1)
                print(f"  - Removed special keyword '{keyword}' from end: {base}")
                continue

            # Check for these keywords in the middle (_Color_, _Normal_, etc.)
            pattern = r"(.*?)(?:[_\.])(" + re.escape(keyword) + r")(?:[_\.])(.*)"
            match = re.match(pattern, base, re.IGNORECASE)
            if match:
                base = match.group(1) + match.group(3)
                print(f"  - Removed special keyword '{keyword}' from middle: {base}")
                continue

        # Remove trailing dots and underscores
        base = re.sub(r"[_\.]+$", "", base)

        # Check if we actually modified the name
        if base != original_base:
            print(f"  Final material name: {base}")
        else:
            print(f"  No modifications needed, material name: {base}")

        return base

    def _identify_texture_type(self, filename):
        """Identify texture type from filename with improved UDIM handling"""
        # Remove extension
        filename_no_ext = os.path.splitext(filename)[0]
        
        print(f"Identifying texture type for: {filename_no_ext}")

        # Remove UDIM numbering (for Substance Painter format: name.1001)
        substance_match = re.match(r"(.*?)\.([0-9]{4})$", filename_no_ext)
        if substance_match:
            filename_no_ext = substance_match.group(1)
            print(f"  - Removed UDIM tile number: {filename_no_ext}")

        # Remove UDIM parts from the name
        if "%(UDIM)d" in filename_no_ext:
            filename_no_ext = filename_no_ext.replace("_%(UDIM)d_", "_").replace(
                ".%(UDIM)d.", "."
            )
            print(f"  - Removed Houdini UDIM tag: {filename_no_ext}")
        elif "<UDIM>" in filename_no_ext:
            filename_no_ext = filename_no_ext.replace("_<UDIM>_", "_").replace(
                ".<UDIM>.", "."
            )
            print(f"  - Removed Redshift UDIM tag: {filename_no_ext}")

        # Handle standard UDIM numbering and Mari-style coordinates
        # Replace standard UDIM tile numbers
        udim_standard = re.sub(r"([\._])[0-9]{4}([\._])", r"\1\2", filename_no_ext)
        if udim_standard != filename_no_ext:
            filename_no_ext = udim_standard
            print(f"  - Removed standard UDIM format: {filename_no_ext}")

        # Replace Mari-style coordinates
        mari_pattern = re.sub(r"(_u\d+_v\d+_)", "_", filename_no_ext)
        if mari_pattern != filename_no_ext:
            filename_no_ext = mari_pattern
            print(f"  - Removed Mari-style coordinates: {filename_no_ext}")

        # Handle UDIM in the middle of the name
        middle_udim = re.sub(r"_[0-9]{4}_", "_", filename_no_ext)
        if middle_udim != filename_no_ext:
            filename_no_ext = middle_udim
            print(f"  - Removed UDIM from middle of name: {filename_no_ext}")

        # Check for texture type indicators using the cleaner name
        clean_name = filename_no_ext.lower()

        # Special handling for certain types by exact string match
        if "alpha" in clean_name:
            print("  Identified as: alpha texture")
            return "alpha"

        if "translucency" in clean_name or "translucent" in clean_name:
            print("  Identified as: translucency texture")
            return "translucency"

        # For Substance Painter naming convention: base_Color, base_Normal, etc.
        for tex_type, keywords in self.texture_types.items():
            for keyword in keywords:
                # Check for keyword after an underscore or at the end
                if f"_{keyword}" in clean_name or clean_name.endswith(keyword):
                    print(f"  Identified as: {tex_type} texture")
                    return tex_type

        # If we can't identify a specific type, assume it's basecolor
        print("  No specific type identified, defaulting to: basecolor")
        return "basecolor"

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

        # NEW: Sanitize the material name to be a valid Houdini node name
        # Remove periods, replace spaces with underscores, and other invalid characters
        clean_material_name = clean_material_name.replace(".", "_").replace(" ", "_")
        # Replace any other potentially problematic characters
        clean_material_name = re.sub(r"[^a-zA-Z0-9_]", "_", clean_material_name)
        # Ensure it doesn't start with a number
        if clean_material_name and clean_material_name[0].isdigit():
            clean_material_name = "_" + clean_material_name

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
                print("Created StandardMaterial node")

            if redshift_material_node is None:
                redshift_material_node = rs_mat.createNode(
                    "redshift_material", "redshift_material"
                )
                print("Created redshift_material node")

            # Connect StandardMaterial to redshift_material if not already connected
            try:
                # Check if already connected
                if redshift_material_node.input(0) is None:
                    # Connect StandardMaterial to redshift_material
                    redshift_material_node.setInput(0, material_node, 0)
                    print("Connected StandardMaterial to redshift_material")
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
                            print("Connected basecolor texture")
                        elif tex_type == "roughness":
                            material_node.setNamedInput("refl_roughness", tex_node, 0)
                            print("Connected roughness texture")
                        elif tex_type == "metallic":
                            material_node.setNamedInput("metalness", tex_node, 0)
                            print("Connected metallic texture")
                        elif tex_type == "emission":
                            material_node.setNamedInput("emission_color", tex_node, 0)
                            print("Connected emission texture")
                        elif tex_type == "ao":
                            material_node.setNamedInput("overall_color", tex_node, 0)
                            print("Connected ambient occlusion texture")
                        elif tex_type == "translucency":
                            material_node.setNamedInput("transl_color", tex_node, 0)
                            material_node.setNamedInput("transl_weight", tex_node, 0)
                            print("Connected translucency texture")
                        elif tex_type == "alpha":
                            material_node.setNamedInput("opacity_color", tex_node, 0)
                            print("Connected alpha texture")
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

                        # Set to normal map mode - use try/except for each parameter
                        # to handle different Redshift versions
                        try:
                            if bump_node.parm("inputType") is not None:
                                bump_node.parm("inputType").set(1)  # 1 = Normal Map
                        except Exception:
                            pass

                        try:
                            if bump_node.parm("input_type") is not None:
                                bump_node.parm("input_type").set(1)
                        except Exception:
                            pass

                        # Set Input Map Type to Tangent-Space Normal
                        try:
                            if bump_node.parm("inputMapType") is not None:
                                bump_node.parm("inputMapType").set(
                                    1
                                )  # 1 = Tangent-Space Normal
                        except Exception:
                            pass

                        try:
                            if bump_node.parm("input_map_type") is not None:
                                bump_node.parm("input_map_type").set(1)
                        except Exception:
                            pass

                        try:
                            if bump_node.parm("normal_map_type") is not None:
                                bump_node.parm("normal_map_type").set(1)
                        except Exception:
                            pass

                        print("Set normal map to Tangent-Space Normal")

                        # Connect normal texture to bump node
                        bump_node.setInput(0, normal_tex, 0)
                        print("Connected normal map to bump node")

                    # Process bump map
                    if "bump" in textures:
                        bump_tex = self._create_texture_node(
                            rs_mat, "bump", textures["bump"]
                        )

                        if "normal" in textures:
                            # If we already have a normal map, connect bump to input 1
                            bump_node.setInput(1, bump_tex, 0)
                            print("Connected bump map to bump node input 1")
                        else:
                            # Otherwise, set to bump map mode and connect to input 0
                            try:
                                bump_node.parm("inputType").set(0)  # 0 = Bump Map
                            except Exception:
                                try:
                                    bump_node.parm("input_type").set(0)
                                except Exception:
                                    pass  # Just continue if can't set parameter

                            bump_node.setInput(0, bump_tex, 0)
                            print("Connected bump map to bump node input 0")

                    # Connect bump node to material_node
                    material_node.setNamedInput("bump_input", bump_node, 0)
                    print("Connected bump node to material")
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
                    print("Connected displacement texture to displacement node")

                    # Connect displacement node to redshift_material
                    redshift_material_node.setInput(1, disp_node, 0)
                    print("Connected displacement node to redshift_material")
                except Exception as e:
                    print(f"Warning: Failed to process displacement map: {str(e)}")

            # Make sure redshift_material is the output - NEW: Try different output node types
            try:
                # Find the output node
                output_node = None

                # First check if an output node already exists
                for child in rs_mat.children():
                    if child.type().name() in ["subnet_output", "output", "vopout"]:
                        output_node = child
                        print(f"Found existing output node: {child.name()}")
                        break

                # If no output node exists, try to create one, trying different types
                if output_node is None:
                    # Try different output node types in order
                    for node_type in ["subnet_output", "output", "vopout"]:
                        try:
                            output_node = rs_mat.createNode(node_type, "output")
                            print(f"Created output node of type {node_type}")
                            break  # Break if successful
                        except Exception as e:
                            print(f"Failed to create {node_type}: {str(e)}")
                            continue  # Try next type

                # Connect redshift_material to output if we found/created an output node
                if output_node is not None:
                    output_node.setInput(0, redshift_material_node, 0)
                    print("Connected redshift_material to output node")
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
                except Exception:
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
                except Exception:
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


class RedshiftMaterialToolDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(RedshiftMaterialToolDialog, self).__init__(parent)
        self.setWindowTitle("Redshift Material Tool v2")
        self.resize(700, 500)

        # Default paths
        self.project_path = hou.text.expandString("$HIP")
        self.tex_path = os.path.join(self.project_path, "tex")

        # Create the material tool instance first
        self.material_tool = RedshiftMaterialTool()

        # Create the UI
        self.create_ui()

        # Set the default texture path in the UI
        if os.path.exists(self.tex_path):
            self.tex_path_field.setText(self.tex_path)
        else:
            # If the default texture path doesn't exist, just use the project path
            self.tex_path_field.setText(self.project_path)

        self.material_sets = {}
        self.checkbox_widgets = {}

    def create_ui(self):
        """Create the user interface"""
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # Texture directory selection
        tex_layout = QtWidgets.QHBoxLayout()
        tex_label = QtWidgets.QLabel("Texture Directory:")
        self.tex_path_field = QtWidgets.QLineEdit()
        self.tex_path_field.setText(self.tex_path)
        browse_button = QtWidgets.QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_texture_directory)

        tex_layout.addWidget(tex_label)
        tex_layout.addWidget(self.tex_path_field, 1)
        tex_layout.addWidget(browse_button)

        layout.addLayout(tex_layout)

        # Add some spacing
        layout.addSpacing(10)

        # Options group box
        options_group = QtWidgets.QGroupBox("Options")
        options_layout = QtWidgets.QVBoxLayout()
        options_group.setLayout(options_layout)

        # Option to overwrite existing materials
        self.overwrite_checkbox = QtWidgets.QCheckBox("Overwrite existing materials")
        options_layout.addWidget(self.overwrite_checkbox)

        # Option to create a folder for each material
        self.create_folders_checkbox = QtWidgets.QCheckBox(
            "Create separate folder for each material"
        )
        options_layout.addWidget(self.create_folders_checkbox)

        layout.addWidget(options_group)

        # Material list section
        list_label = QtWidgets.QLabel("Materials to be created:")
        layout.addWidget(list_label)

        self.material_list = QtWidgets.QListWidget()
        layout.addWidget(self.material_list)

        # Scan button
        scan_button = QtWidgets.QPushButton("Scan for Textures")
        scan_button.clicked.connect(self.scan_textures)
        layout.addWidget(scan_button)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        create_button = QtWidgets.QPushButton("Create Materials")
        create_button.clicked.connect(self.create_materials)
        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(create_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        # Add a group box for scan results with checkboxes
        self.scan_results_group = QtWidgets.QGroupBox("Scan Results")
        self.scan_results_layout = QtWidgets.QVBoxLayout()
        self.scan_results_group.setLayout(self.scan_results_layout)

        # Initially hide the scan results section
        self.scan_results_group.setVisible(False)

        # Add a scroll area for the checkboxes (in case there are many)
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QtWidgets.QWidget()
        self.checkbox_layout = QtWidgets.QVBoxLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        self.scan_results_layout.addWidget(scroll_area)

        # Add buttons for controlling the checkboxes
        checkbox_buttons_layout = QtWidgets.QHBoxLayout()
        select_all_button = QtWidgets.QPushButton("Select All")
        select_all_button.clicked.connect(self.select_all_checkboxes)
        deselect_all_button = QtWidgets.QPushButton("Deselect All")
        deselect_all_button.clicked.connect(self.deselect_all_checkboxes)

        checkbox_buttons_layout.addWidget(select_all_button)
        checkbox_buttons_layout.addWidget(deselect_all_button)
        self.scan_results_layout.addLayout(checkbox_buttons_layout)

        # Add the scan results group to the main layout
        layout.addWidget(self.scan_results_group)

    def browse_texture_directory(self):
        """Open a directory browser to select the texture directory"""
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Texture Directory", self.tex_path
        )

        if directory:
            self.tex_path = directory
            self.tex_path_field.setText(directory)

    def scan_textures(self):
        """Scan for textures and update the material list"""
        # Clear the material list
        self.material_list.clear()

        # Clear any existing checkboxes from previous scans
        if hasattr(self, "checkbox_layout"):
            self.clear_checkboxes()

        # Get and expand the texture path from the field
        input_path = self.tex_path_field.text()
        expanded_path = hou.text.expandString(input_path)

        # Update both paths in the material tool
        if os.path.exists(expanded_path):
            self.material_tool.tex_path = expanded_path

            # Adjust the project path based on the texture path
            # If the path ends with /tex, set project to parent dir
            if os.path.basename(expanded_path) == "tex":
                self.material_tool.project_path = os.path.dirname(expanded_path)
            else:
                # Otherwise, just use the directory as the project
                self.material_tool.project_path = expanded_path

            print(f"Scanning texture path: {expanded_path}")
            print(f"Using project path: {self.material_tool.project_path}")

            # Scan for textures
            material_sets = self.material_tool.scan_textures()

            if not material_sets:
                QtWidgets.QMessageBox.warning(
                    self,
                    "No Textures Found",
                    f"No texture sets found in:\n{expanded_path}\n\n"
                    f"Make sure your textures follow the expected naming conventions and folder structure.",
                )

                # Hide the scan results section if it exists
                if hasattr(self, "scan_results_group"):
                    self.scan_results_group.setVisible(False)

                return

            # Show the scan results group with checkboxes if it exists
            if hasattr(self, "scan_results_group"):
                self.scan_results_group.setVisible(True)

                # Add a checkbox for each mesh/material combination
                for mesh_name, materials in material_sets.items():
                    # Add a label for the mesh
                    mesh_label = QtWidgets.QLabel(f"<b>{mesh_name}</b>")
                    self.checkbox_layout.addWidget(mesh_label)

                    # Add checkboxes for each material
                    for material_name, textures in materials.items():
                        # Create a description of the material
                        texture_types = ", ".join(textures.keys())
                        checkbox_text = f"{material_name} ({len(textures)} textures: {texture_types})"

                        # Create the checkbox
                        checkbox = QtWidgets.QCheckBox(checkbox_text)
                        checkbox.setChecked(True)  # Default to checked

                        # Store the checkbox with a unique key
                        key = f"{mesh_name}:{material_name}"
                        self.checkbox_widgets[key] = checkbox

                        # Add the checkbox to the layout
                        self.checkbox_layout.addWidget(checkbox)

                    # Add a spacer after each mesh
                    spacer = QtWidgets.QSpacerItem(
                        20,
                        10,
                        QtWidgets.QSizePolicy.Minimum,
                        QtWidgets.QSizePolicy.Fixed,
                    )
                    self.checkbox_layout.addSpacerItem(spacer)

                # Store the material sets for later use
                self.material_sets = material_sets

                # Show a summary
                QtWidgets.QMessageBox.information(
                    self,
                    "Scan Complete",
                    f"Found {len(self.checkbox_widgets)} materials in {len(self.material_sets)} mesh folders.",
                )
            else:
                # Original behavior - populate the list widget
                for mesh_name, materials in material_sets.items():
                    for material_name, textures in materials.items():
                        # Create a descriptive display string
                        texture_types = ", ".join(textures.keys())
                        item_text = f"{mesh_name} / {material_name} ({len(textures)} textures: {texture_types})"

                        # Create a list item with the complete material data
                        item = QtWidgets.QListWidgetItem(item_text)
                        item.setData(
                            QtCore.Qt.UserRole,
                            {
                                "mesh_name": mesh_name,
                                "material_name": material_name,
                                "textures": textures,  # Contains ALL textures for this material
                            },
                        )
                        self.material_list.addItem(item)

                print(f"Found {self.material_list.count()} consolidated materials")
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Directory",
                f"The specified directory does not exist:\n{expanded_path}",
            )

    def extract_base_material_name(self, material_name):
        """Extract a clean base material name without texture type indicators"""
        # Remove UDIM tags
        clean_name = material_name.replace("<UDIM>", "")
        clean_name = clean_name.replace("%(UDIM)d", "")

        # Handle BarBase_Bar_combo_Color.UDIM format
        for suffix in [
            "Color",
            "DisplaceHeightField",
            "EmissionColor",
            "Metalness",
            "Normal",
            "Roughness",
            "alpha",
            "translucency",
            "AO",
            "height",
            "basecolor",
            "diffuse",
            "albedo",
            "roughness",
            "rough",
            "metallic",
            "metal",
            "normal",
            "bump",
            "displacement",
            "emission",
            "ao",
        ]:

            # Check for suffix at end with dot or underscore
            if re.search(rf"[_\.]({re.escape(suffix)})$", clean_name, re.IGNORECASE):
                clean_name = re.sub(
                    rf"[_\.]({re.escape(suffix)})$", "", clean_name, flags=re.IGNORECASE
                )
                break

            # Check for suffix in middle with separators
            if re.search(
                rf"[_\.]({re.escape(suffix)})[_\.]", clean_name, re.IGNORECASE
            ):
                clean_name = re.sub(
                    rf"[_\.]({re.escape(suffix)})[_\.]",
                    "",
                    clean_name,
                    flags=re.IGNORECASE,
                )
                break

        # Remove trailing separators
        clean_name = re.sub(r"[_\.]+$", "", clean_name)

        return clean_name

    def create_materials(self):
        """Create the materials based on the selected items in the list or checkboxes"""
        # Determine if we're using checkboxes or the list widget
        using_checkboxes = hasattr(self, "checkbox_widgets") and self.checkbox_widgets

        # Check if we have materials
        if using_checkboxes and not hasattr(self, "material_sets"):
            QtWidgets.QMessageBox.warning(
                self,
                "No Materials",
                "No materials found. Please scan for textures first.",
            )
            return
        elif not using_checkboxes and self.material_list.count() == 0:
            QtWidgets.QMessageBox.warning(
                self,
                "No Materials",
                "No materials found. Please scan for textures first.",
            )
            return

        # Get the material context
        try:
            mat_context = self.material_tool.create_material_context()
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to create material context: {str(e)}"
            )
            return

        # Process materials based on UI type (checkboxes or list)
        if using_checkboxes:
            # Create a list of materials to create based on checked boxes
            materials_to_create = []
            for key, checkbox in self.checkbox_widgets.items():
                if checkbox.isChecked():
                    mesh_name, material_name = key.split(":", 1)
                    materials_to_create.append(
                        {
                            "mesh_name": mesh_name,
                            "material_name": material_name,
                            "textures": self.material_sets[mesh_name][material_name],
                        }
                    )

            if not materials_to_create:
                QtWidgets.QMessageBox.warning(
                    self,
                    "No Selection",
                    "No materials selected. Please select at least one material.",
                )
                return
        else:
            # Process selected materials from the list or all if none selected
            selected_items = self.material_list.selectedItems()
            if not selected_items:
                # No selection, process all
                material_items = [
                    self.material_list.item(i)
                    for i in range(self.material_list.count())
                ]
            else:
                material_items = selected_items

            # Convert to the same format as the checkbox version
            materials_to_create = [
                item.data(QtCore.Qt.UserRole) for item in material_items
            ]

        # Create materials
        created_count = 0
        skipped_count = 0

        progress = QtWidgets.QProgressDialog(
            "Creating materials...", "Cancel", 0, len(materials_to_create), self
        )
        progress.setWindowModality(QtCore.Qt.WindowModal)

        for i, material_data in enumerate(materials_to_create):
            progress.setValue(i)
            if progress.wasCanceled():
                break

            mesh_name = material_data["mesh_name"]
            material_name = material_data["material_name"]
            textures = material_data["textures"]

            # Check if material already exists
            existing_mat = self.material_tool.check_material_exists(
                mat_context, material_name
            )

            if existing_mat and not self.overwrite_checkbox.isChecked():
                progress.setLabelText(f"Skipping existing material: {material_name}")
                skipped_count += 1
                continue

            # Delete existing material if we're overwriting
            if existing_mat and self.overwrite_checkbox.isChecked():
                existing_mat.destroy()

            try:
                # Create new material
                if self.create_folders_checkbox.isChecked():
                    # Create a subnet for this material
                    material_folder = mat_context.createNode(
                        "subnet", f"FOLDER_{material_name}"
                    )
                    new_mat = self.material_tool.create_redshift_material(
                        material_folder, material_name, textures
                    )
                else:
                    new_mat = self.material_tool.create_redshift_material(
                        mat_context, material_name, textures
                    )

                if new_mat:
                    progress.setLabelText(f"Created material: {material_name}")
                    created_count += 1
            except Exception as e:
                progress.setLabelText(f"Error creating {material_name}: {str(e)}")

        progress.setValue(len(materials_to_create))

        # Layout nodes in material context
        try:
            mat_context.layoutChildren()
        except Exception as e:
            print(f"Warning: Could not layout children: {str(e)}")

        # Show summary
        QtWidgets.QMessageBox.information(
            self,
            "Material Creation Complete",
            f"Created {created_count} new materials\nSkipped {skipped_count} existing materials",
        )

        # Close the dialog if successful
        if created_count > 0:
            self.accept()

    def select_all_checkboxes(self):
        """Select all checkboxes"""
        for checkbox in self.checkbox_widgets.values():
            checkbox.setChecked(True)

    def deselect_all_checkboxes(self):
        """Deselect all checkboxes"""
        for checkbox in self.checkbox_widgets.values():
            checkbox.setChecked(False)

    def clear_checkboxes(self):
        """Clear all checkboxes from the layout"""
        # Remove all existing checkboxes
        for i in reversed(range(self.checkbox_layout.count())):
            widget = self.checkbox_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        self.checkbox_widgets = {}


# Function to launch the dialog
def create_redshift_material_tool_v2():
    """Launch the Redshift Material Tool v2 dialog"""
    dialog = RedshiftMaterialToolDialog(hou.ui.mainQtWindow())
    dialog.exec_()


# For testing the tool in Houdini
if __name__ == "__main__":
    create_redshift_material_tool_v2()
