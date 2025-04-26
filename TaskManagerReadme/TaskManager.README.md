# ClickUp Task Manager for Houdini

A powerful Houdini plugin that integrates ClickUp task management directly into your Houdini workflow. Create, update, and manage ClickUp tasks without leaving your 3D environment.

## Features

- **OAuth 2.0 Authentication**: Secure connection to your ClickUp account
- **Workspace Navigation**: Browse workspaces, spaces, and lists
- **Task Management**: Create, update, and view tasks directly in Houdini
- **Assignee Support**: Assign tasks to team members
- **Priority Management**: Set task priorities (Urgent, High, Normal, Low)
- **Status Tracking**: Update task statuses based on your list's custom statuses
- **Houdini Integration**: Convert tasks into Houdini nodes for visual project management
- **Credential Storage**: Save and load your ClickUp credentials

## Installation

1. **Download the Script**
   - Save `clickup_task_manager_oauth.py` to your Houdini scripts directory:
     - Windows: `C:/Users/[username]/Documents/houdini[version]/scripts/python/`
     - Mac: `~/Library/Preferences/houdini/[version]/scripts/python/`
     - Linux: `~/houdini[version]/scripts/python/`

2. **Create a Shelf Tool**
   - Right-click on any shelf in Houdini
   - Select "New Tool..."
   - Name: "ClickUp Task Manager"
   - Script tab:
     ```python
     import clickup_task_manager_oauth
     clickup_task_manager_oauth.launch_task_manager()
     ```
   - Click "Accept"

3. **Set Up ClickUp OAuth App**
   - Go to your [ClickUp App Settings](https://app.clickup.com/settings/apps)
   - Create a new app or select an existing one
   - Set the redirect URI to: `http://localhost:8888`
   - Note down your Client ID and Client Secret

## Usage

### First-Time Setup

1. **Launch the Tool**
   - Click the "ClickUp Task Manager" button on your shelf
   
2. **Authenticate**
   - Enter your ClickUp Client ID and Client Secret
   - Click "Authenticate with ClickUp"
   - Your browser will open for OAuth authentication
   - Grant permissions and you'll be redirected back to Houdini
   - Click "Save Credentials" to save your login for future sessions

### Working with Tasks

1. **Navigate to Your List**
   - Select your Workspace from the dropdown
   - Select your Space
   - Select your List

2. **View Tasks**
   - Tasks are displayed in the table with their name, status, priority, due date, and assignees
   - Click "Refresh" to update the task list

3. **Create New Tasks**
   - Click "Create Task"
   - Fill in the task details:
     - Task Name (required)
     - Description
     - Priority
     - Assignee
   - Click "Create" to add the task to ClickUp

4. **Update Existing Tasks**
   - Select a task in the table
   - Click "Update Selected"
   - Modify the task details:
     - Status (uses your list's custom statuses)
     - Description
     - Assignee
   - Click "Update" to save changes

5. **Convert to Houdini Node**
   - Double-click any task in the table
   - A null node will be created in `/obj` context
   - The node contains task information as parameters
   - Node color indicates task status:
     - Red: Open
     - Yellow: In Progress
     - Blue: Review
     - Green: Completed

## Technical Details

### Authentication
- Uses OAuth 2.0 with authorization code flow
- Runs a local server on port 8888 to receive the callback
- Access tokens are valid for 1 hour (refresh not implemented)

### API Integration
- Uses ClickUp API v2
- Supports custom statuses per list
- Handles UDIM workspace structures
- Robust error handling with user feedback

### Data Storage
- Credentials saved in `$HOUDINI_USER_PREF_DIR/config/clickup_credentials.json`
- Only Client ID and Secret are stored (not access tokens)

## Troubleshooting

### Common Issues

1. **Authentication Fails**
   - Ensure your Client ID and Secret are correct
   - Check that your redirect URI is set to `http://localhost:8888`
   - Try clearing your browser cache and authenticating again

2. **Tasks Not Loading**
   - Verify you have the correct permissions in ClickUp
   - Check that you've selected a workspace, space, and list
   - Click "Refresh" to reload the task list

3. **Status Update Errors**
   - Different lists have different status options
   - The tool automatically loads available statuses for your selected list
   - Ensure you're selecting a valid status from the dropdown

4. **Assignee Issues**
   - Only users with access to the selected list can be assigned
   - The tool checks both list members and workspace members
   - Ensure the user has been invited to the workspace/list

### Error Messages

- **"Status does not exist"**: The status value is not valid for the selected list
- **"Failed to create task: 400"**: Usually indicates missing required fields or invalid data
- **"Failed to load workspace members"**: Check your permissions in ClickUp

## Limitations

- Token refresh not implemented (re-authenticate after 1 hour)
- Audit log functionality removed (not supported by current API)
- Cannot create new statuses (uses existing list statuses)
- Limited to single assignee per task

## Support

For issues or feature requests, please contact your pipeline TD or submit a ticket to the tools team.

## Version History

- **v1.0**: Initial release with basic task management
- **v1.1**: Added OAuth authentication and assignee support
- **v1.2**: Fixed status handling and improved error messages

## License

Internal tool - not for distribution outside the studio.