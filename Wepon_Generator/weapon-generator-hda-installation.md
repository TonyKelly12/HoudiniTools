# Weapon Generator HDA - Installation Guide

This guide will walk you through setting up the Weapon Generator HDA, which connects to your 3D Weapon Assembly API to create assembled weapons in Houdini.

## Prerequisites

1. Houdini 19.5 or newer
2. Your 3D Weapon Assembly API server running (default: http://localhost:8000)
3. PySide2 (included with Houdini)

## Setup Instructions

### Step 1: Create the HDA

1. Open Houdini and navigate to the `/obj` context
2. From the menu, select **File > New Digital Asset...**
3. Choose **Subnet** for the operator type
4. Enter a name like `weapon_generator`
5. Click **Accept**

### Step 2: Configure Basic HDA Properties

1. In the Type Properties dialog:
   - Set **Label** to "Weapon Generator"
   - (Optional) Set an icon if you have one available
   - Set **Minimum Inputs** to 0 and **Maximum Inputs** to 0
   - Under **Description**, add "Generates assembled weapons from online parts library using the 3D Weapon Assembly API"

### Step 3: Add Parameters

1. In the **Parameters** tab of Type Properties:
   - Add a String parameter named `api_url` with label "API URL" and default value "http://localhost:8000"
   - Add a String parameter named `output_path` with label "Output Path" and default value "$HIP/geo/weapons"

### Step 4: Add Python Module

1. In Type Properties, go to the **Scripts** tab
2. Look for or add the **Python Module** section:
   - Paste the entire code from the "Weapon Generator HDA Python Code" artifact (this long Python code)
   - If you don't see a Python Module section, add one from the + button at the top of the tab

### Step 5: Add Interface Scripts

1. Still in the **Scripts** tab:
   - Find the **OnCreated** callback and enter:
     ```python
     import weapon_generator_ui
     weapon_generator_ui.onNodeCreated()
     ```
     
   - Find the **Interface** callback and enter:
     ```python
     import weapon_generator_ui
     return weapon_generator_ui.onCreateInterface()
     ```
     
   - Note: Houdini will automatically use the class name from the Python Module. If you prefer, you can directly use:
     ```python
     return hou.pwd().hdaModule().onCreateInterface()
     ```

### Step 6: Add Help Information

1. In Type Properties, go to the **Help** tab
2. Paste the content from the "Weapon Generator HDA Help" artifact
3. Click **Accept** to save all changes to the HDA

### Step 7: Test the HDA

1. Create an instance of your new Weapon Generator HDA in a Houdini scene
2. Make sure your 3D Weapon Assembly API server is running
3. The interface should load and connect to your API
4. Select a weapon type, browse through the parts, and generate a weapon
5. The resulting weapon will appear in your scene


## Troubleshooting

### API Connection Issues

- Ensure your API server is running and accessible from Houdini
- Check the API URL in the HDA parameter
- If you're running the API on a different machine, make sure networking allows the connection

### Missing Parts or Previews

- Confirm your API server has parts data for the weapon types you're trying to use
- The thumbnails in this implementation are generated dynamically - in a production version, you would fetch actual thumbnails from the API

### Import Errors

- Check file paths and ensure your API is correctly serving model files
- Verify that any downloaded model files are in a format Houdini can read (e.g., FBX, OBJ)
- Look at the console for Python errors that might provide more information

### Performance Issues

- This HDA uses threading to avoid freezing the UI during API calls
- If you experience crashes, simplify the threading model by making API calls synchronous
- Large model files may take time to download and process

## Customization

To customize the Weapon Generator:

1. Edit the Python Module to change the behavior of the tool
2. Modify the API client class to work with your specific API endpoints
3. Enhance the UI by adding more controls or feedback mechanisms
4. Improve the weapon assembly logic to support more complex positioning or materials

Remember to save your changes to the HDA after making any modifications.
