# Redshift Material Tool with UDIM Support

The updated Redshift Material Tool now includes support for UDIM textures. This guide explains how to install the updated version and how UDIM textures are handled.

## Installation

1. **Replace Your Existing Script**:
   - Copy the updated Python script from the "Redshift Material Tool with UDIM Support" artifact
   - Save it to the same location as your previous script, overwriting the existing file:
     - Windows: `C:/Users/[username]/Documents/houdini[version]/scripts/python/redshift_material_tool.py`
     - Mac: `~/Library/Preferences/houdini/[version]/scripts/python/redshift_material_tool.py`
     - Linux: `~/houdini[version]/scripts/python/redshift_material_tool.py`

2. **No Other Changes Needed**:
   - Your existing shelf tool will automatically use the updated script
   - No additional configuration is required

## UDIM Support Features

The updated tool supports several UDIM naming conventions:

1. **Standard UDIM Format**: Files named like `texture_1001_diffuse.exr`, `texture_1002_diffuse.exr`

2. **Mari-style UDIMs**: Files named like `texture_u1_v1_diffuse.exr`, `texture_u2_v1_diffuse.exr`

3. **Various Separators**: Supports both dot and underscore separators (e.g., `texture.1001.diffuse.exr` or `texture_1001_diffuse.exr`)

## How UDIM Textures Are Organized

For the tool to correctly identify UDIM textures, organize them following these guidelines:

1. **Standard Directory Structure**:
   - Place all textures in the `tex` folder of your Houdini project
   - Create subfolders named after your meshes
   - Keep all UDIM tiles for the same texture together in the same folder

2. **UDIM Naming Convention**:
   - Name your UDIM textures using a consistent pattern
   - Include the UDIM tile number (e.g., 1001, 1002) or Mari-style coordinates (u1_v1, u2_v1)
   - Add texture type suffix as usual (e.g., `_basecolor`, `_normal`, etc.)

Example folder structure:
```
MyProject/
  ├── tex/
  │   ├── character/
  │   │   ├── skin_1001_basecolor.exr
  │   │   ├── skin_1002_basecolor.exr
  │   │   ├── skin_1001_normal.exr
  │   │   ├── skin_1002_normal.exr
  │   │   ├── leather_u1_v1_basecolor.exr
  │   │   ├── leather_u2_v1_basecolor.exr
  │   │   └── leather_u1_v1_roughness.exr
  │   └── environment/
  │       ├── ground_1001_basecolor.exr
  │       ├── ground_1002_basecolor.exr
  │       └── ground_1001_roughness.exr
```

## How It Works

When the tool discovers UDIM textures:

1. It recognizes files that are part of a UDIM sequence
2. Groups them together and determines the base pattern
3. Creates a Redshift texture node with the `<UDIM>` tag in the file path
4. Enables the UDIM flag on the texture node

The tool automatically sets the appropriate color space for each texture type:
- sRGB for basecolor and emission textures
- Raw for all other texture types (normal, roughness, metallic, etc.)

## Troubleshooting

If you encounter issues with UDIM textures:

1. **Check Naming Consistency**: Ensure all tiles of the same texture follow the same naming pattern
2. **Verify UDIM Tags**: Make sure the UDIM tile numbers are correctly formatted (4 digits, e.g., 1001)
3. **Check Console**: Look for error messages in the Houdini console
4. **Examine File Paths**: Verify the texture paths in the generated Redshift nodes

If a UDIM texture isn't recognized, try running the tool with these troubleshooting steps:
1. Add print statements in your scripts/python/redshift_material_tool.py file
2. Add `print(files)` at line 37 (beginning of the scan_textures method)
3. Run the tool and check the output in the console