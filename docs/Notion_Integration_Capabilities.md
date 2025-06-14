# Notion Integration Capabilities

## Integration Capabilities Overview
All integrations have associated capabilities which enforce what an integration can do and see in a Notion workspace. These capabilities, when combined, determine which API endpoints an integration can call and what content and user-related information they can access. To set your integration's capabilities, see the Authorization guide or navigate to [Notion Integrations](https://www.notion.so/my-integrations).

![Capability Configuration Screen](screenshot.png)

> **Note:** If an integration is added to a page, it can access the page's children. When an integration receives access to a Notion page or database, it can read and write to both that resource and its children.

## Content Capabilities
Content capabilities affect how an integration can interact with database objects, page objects, and block objects via the API. Additionally, these capabilities affect what information is exposed to an integration in API responses. To verify which capabilities are needed for an endpoint's desired behavior, please use the API references.

- **Read Content**: This capability gives an integration access to read existing content in a Notion workspace. For example, an integration with only this capability can call Retrieve a database, but not Update database.
- **Update Content**: This capability gives an integration permission to update existing content in a Notion workspace. For example, an integration with only this capability can call the Update page endpoint, but cannot create new pages.
- **Insert Content**: This capability gives an integration permission to create new content in a Notion workspace. This capability does not give the integration access to read full objects. For example, an integration with only this capability can Create a page but cannot update existing pages.

It is possible for an integration to have any combination of these content capabilities.

## Comment Capabilities
Comment capabilities dictate how an integration can interact with the comments on a page or block.

- **Read Comments**: This capability gives the integration permission to read comments from a Notion page or block.
- **Insert Comments**: This capability gives the integration permission to insert comments in a page or in an existing discussion.

## User Capabilities
An integration can request different levels of user capabilities, which affect how user objects are returned from the Notion API:

- **No User Information**: Selecting this option prevents an integration from requesting any information about users. User objects will not include any information about the user, including name, profile image, or their email address.
- **User Information Without Email Addresses**: Selecting this option ensures that User objects will include all information about a user, including name and profile image, but omit the email address.
- **User Information With Email Addresses**: Selecting this option ensures that User objects will include all information about the user, including name, profile image, and their email address.

## Capability Behaviors and Best Practices
- An integration's capabilities will never supersede a user's. If a user loses edit access to the page where they have added an integration, that integration will now also only have read access, regardless of the capabilities the integration was created with.
- For public integrations, users will need to re-authenticate with an integration if the capabilities are changed since the user last authenticated with the integration.
- In general, request the minimum capabilities that your integration needs to function. The fewer capabilities you request, the more likely a workspace admin will be able to install your integration.

### Examples:
- If your integration is solely bringing data into Notion (creating new pages, or adding blocks), your integration only needs Insert content capabilities.
- If your integration is reading data to export it out of Notion, your integration will only need Read content capabilities.
- If your integration is simply updating a property on a page or an existing block, your integration will only need Update content capabilities.

## Update a Database

**PATCH** `https://api.notion.com/v1/databases/{database_id}`

Updates the database object — the title, description, or properties — of a specified database.

Returns the updated database object.

Database properties represent the columns (or schema) of a database. To update the properties of a database, use the properties body param with this endpoint. Learn more about database properties in the database properties and Update database properties docs.

To update a relation database property, share the related database with the integration. Learn more about relations in the database properties page.

For an overview of how to use the REST API with databases, refer to the Working with databases guide.

### How Database Property Type Changes Work
All properties in pages are stored as rich text. Notion will convert that rich text based on the types defined in a database's schema. When a type is changed using the API, the data will continue to be available, it is just presented differently.

For example, a multi select property value is represented as a comma-separated list of strings (e.g., "1, 2, 3") and a people property value is represented as a comma-separated list of IDs. These are compatible and the type can be converted.

**Note:** Not all type changes work. In some cases, data will no longer be returned, such as people type → file type.

### Interacting with Database Rows
This endpoint cannot be used to update database rows.

To update the properties of a database row — rather than a column — use the Update page properties endpoint. To add a new row to a database, use the Create a page endpoint.

### Recommended Database Schema Size Limit
Developers are encouraged to keep their database schema size to a maximum of 50KB. To stay within this schema size limit, the number of properties (or columns) added to a database should be managed.

Database schema updates that are too large will be blocked by the REST API to help developers keep their database queries performant.

### Errors
Each Public API endpoint can return several possible error codes. See the Error codes section of the Status codes documentation for more information.

🚧 **The following database properties cannot be updated via the API:**
- formula
- select
- status
- Synced content
- A multi_select database property's options values. An option can be removed, but not updated.

📘 **Database relations must be shared with your integration**

To update a database relation property, the related database must also be shared with your integration.

### Path Params
- **database_id**: `string` (required) - Identifier for a Notion database

### Body Params
- **title**: `array` - An array of rich text objects that represents the title of the database that is displayed in the Notion UI. If omitted, then the database title remains unchanged.
- **description**: `array` - An array of rich text objects that represents the description of the database that is displayed in the Notion UI. If omitted, then the database description remains unchanged.
- **properties**: `json` - The properties of a database to be changed in the request, in the form of a JSON object. If updating an existing property, then the keys are the names or IDs of the properties as they appear in Notion, and the values are property schema objects. If adding a new property, then the key is the name of the new database property and the value is a property schema object.

### Headers
- **Notion-Version**: `string` (required) - The API version to use for this request. The latest version is 2022-06-28.

### Responses
- **200**: Success
- **400**: Bad Request
- **404**: Not Found
- **429**: Too Many Requests

*Updated 3 months ago*

## Update Page Properties

**PATCH** `https://api.notion.com/v1/pages/{page_id}`

Updates the properties of a page in a database. The properties body param of this endpoint can only be used to update the properties of a page that is a child of a database. The page's properties schema must match the parent database's properties.

This endpoint can be used to update any page icon or cover, and can be used to delete or restore any page.

To add page content instead of page properties, use the append block children endpoint. The `page_id` can be passed as the `block_id` when adding block children to the page.

Returns the updated page object.

📘 **Requirements**

Your integration must have update content capabilities on the target page in order to call this endpoint. To update your integration's capabilities, navigate to the My integrations dashboard, select your integration, go to the Capabilities tab, and update your settings as needed.

Attempting a query without update content capabilities returns an HTTP response with a 403 status code.

🚧 **Limitations**

- Updating rollup property values is not supported.
- A page's parent cannot be changed.

### Errors
Each Public API endpoint can return several possible error codes. See the Error codes section of the Status codes documentation for more information.

### Path Params
- **page_id**: `string` (required) - The identifier for the Notion page to be updated.

### Body Params
- **properties**: `json` - The property values to update for the page. The keys are the names or IDs of the property and the values are property values. If a page property ID is not included, then it is not changed.
- **in_trash**: `boolean` - Defaults to false. Set to true to delete a block. Set to false to restore a block.
- **icon**: `json` - A page icon for the page. Supported types are external file object or emoji object.
- **cover**: `json` - A cover image for the page. Only external file objects are supported.

### Headers
- **Notion-Version**: `string` (required) - The API version to use for this request. The latest version is 2022-06-28.

### Responses
- **200**: Success
- **400**: Bad Request
- **404**: Not Found
- **429**: Too Many Requests 

## Create a Page

**POST** `https://api.notion.com/v1/pages`

Creates a new page that is a child of an existing page or database.

If the new page is a child of an existing page, `title` is the only valid property in the properties body param.

If the new page is a child of an existing database, the keys of the properties object body param must match the parent database's properties.

This endpoint can be used to create a new page with or without content using the children option. To add content to a page after creating it, use the Append block children endpoint.

Returns a new page object.

🚧 **Limitations**

Some page properties are not supported via the API.

A request body that includes rollup, created_by, created_time, last_edited_by, or last_edited_time values in the properties object returns an error. These Notion-generated values cannot be created or updated via the API. If the parent contains any of these properties, then the new page's corresponding values are automatically created.

📘 **Requirements**

Your integration must have Insert Content capabilities on the target parent page or database in order to call this endpoint. To update your integration's capabilities, navigate to the My integrations dashboard, select your integration, go to the Capabilities tab, and update your settings as needed.

Attempting a query without update content capabilities returns an HTTP response with a 403 status code.

### Errors
Each Public API endpoint can return several possible error codes. See the Error codes section of the Status codes documentation for more information.

### Body Params
- **parent**: `json` (required) - The parent page or database where the new page is inserted, represented as a JSON object with a `page_id` or `database_id` key, and the corresponding ID.
- **properties**: `json` (required) - The values of the page's properties. If the parent is a database, then the schema must match the parent database's properties. If the parent is a page, then the only valid object key is `title`.
- **children**: `array of strings` - The content to be rendered on the new page, represented as an array of block objects.
- **icon**: `json` - The icon of the new page. Either an emoji object or an external file object.
- **cover**: `json` - The cover image of the new page, represented as a file object.

### Headers
- **Notion-Version**: `string` (required) - The API version to use for this request. The latest version is 2022-06-28.

### Responses
- **200**: Success
- **400**: Bad Request
- **404**: Not Found
- **429**: Too Many Requests 

## Comment Object

The Comment object represents a comment on a Notion page or block. Comments can be viewed or created by an integration that has access to the page/block and the correct capabilities. Please see the Capabilities guide for more information on setting up your integration's capabilities.

When retrieving comments, one or more Comment objects will be returned in the form of an array, sorted in ascending chronological order. When adding a comment to a page or discussion, the Comment object just added will always be returned.

### JSON Representation
```json
{
    "object": "comment",
    "id": "7a793800-3e55-4d5e-8009-2261de026179",
    "parent": {
        "type": "page_id",
        "page_id": "5c6a2821-6bb1-4a7e-b6e1-c50111515c3d"
    },
    "discussion_id": "f4be6752-a539-4da2-a8a9-c3953e13bc0b",
    "created_time": "2022-07-15T21:17:00.000Z",
    "last_edited_time": "2022-07-15T21:17:00.000Z",
    "created_by": {
        "object": "user",
        "id": "e450a39e-9051-4d36-bc4e-8581611fc592"
    },
    "rich_text": [
        {
            "type": "text",
            "text": {
                "content": "Hello world",
                "link": null
            },
            "annotations": {
                "bold": false,
                "italic": false,
                "strikethrough": false,
                "underline": false,
                "code": false,
                "color": "default"
            },
            "plain_text": "Hello world",
            "href": null
        }
    ]
}
```

### Reminder
📘 **Reminder: Turn on integration comment capabilities**

Integrations must have read comments or insert comments capabilities in order to interact with the Comment object through the API. For more information on integration capabilities, see the capabilities guide.

### Properties
| Property         | Type                  | Description                                                                 | Example Value |
|------------------|-----------------------|-----------------------------------------------------------------------------|---------------|
| object           | string                | Always "comment"                                                           | "comment"    |
| id               | string (UUIDv4)       | Unique identifier of the comment.                                           | "ce18f8c6-ef2a-427f-b416-43531fc7c117" |
| parent           | object                | Information about the comment's parent. See Parent object.                  | { "type": "block_id", "block_id": "5d4ca33c-d6b7-4675-93d9-84b70af45d1c" } |
| discussion_id    | string (UUIDv4)       | Unique identifier of the discussion thread that the comment is associated with. | "ce18f8c6-ef2a-427f-b416-43531fc7c117" |
| created_time     | string (ISO 8601)     | Date and time when this comment was created. Formatted as an ISO 8601 date time string. | "2022-07-15T21:46:00.000Z" |
| last_edited_time | string (ISO 8601)     | Date and time when this comment was updated. Formatted as an ISO 8601 date time string. | "2022-07-15T21:46:00.000Z" |
| created_by       | Partial User          | User who created the comment.                                               | { "object": "user", "id": "e450a39e-9051-4d36-bc4e-8581611fc592" } |
| rich_text        | Rich text object      | Content of the comment, which supports rich text formatting, links, and mentions. |               | 

## Retrieve Comments

**GET** `https://api.notion.com/v1/comments`

Retrieves a list of un-resolved Comment objects from a page or block.

See Pagination for details about how to use a cursor to iterate through the list.

### Errors
Each Public API endpoint can return several possible error codes. See the Error codes section of the Status codes documentation for more information.

📘 **Reminder: Turn on integration comment capabilities**

Integration capabilities for reading and inserting comments are off by default.

This endpoint requires an integration to have read comment capabilities. Attempting to call this endpoint without read comment capabilities will return an HTTP response with a 403 status code.

For more information on integration capabilities, see the capabilities guide. To update your integration settings, visit the integration dashboard.

### Query Params
- **block_id**: `string` (required) - Identifier for a Notion block or page
- **start_cursor**: `string` - If supplied, this endpoint will return a page of results starting after the cursor provided. If not supplied, this endpoint will return the first page of results.
- **page_size**: `int32` - The number of items from the full list desired in the response. Maximum: 100

### Headers
- **Notion-Version**: `string` (required) - The API version to use for this request. The latest version is 2022-06-28.

### Responses
- **200**: Success
- **403**: Forbidden

## Create Comment

**POST** `https://api.notion.com/v1/comments`

Creates a comment in a page or existing discussion thread.

Returns a comment object for the created comment.

There are two locations where a new comment can be added with the public API:

- A page.
- An existing discussion thread.

The request body will differ slightly depending on which type of comment is being added with this endpoint.

To add a new comment to a page, a parent object with a `page_id` must be provided in the body params.

To add a new comment to an existing discussion thread, a `discussion_id` string must be provided in the body params. (Inline comments to start a new discussion thread cannot be created via the public API.)

Either the `parent.page_id` or `discussion_id` parameter must be provided — not both.

To see additional examples of creating a page or discussion comment and to learn more about comments in Notion, see the Working with comments guide.

### Errors
Each Public API endpoint can return several possible error codes. See the Error codes section of the Status codes documentation for more information.

📘 **Reminder: Turn on integration comment capabilities**

Integration capabilities for reading and inserting comments are off by default.

This endpoint requires an integration to have insert comment capabilities. Attempting to call this endpoint without insert comment capabilities will return an HTTP response with a 403 status code.

For more information on integration capabilities, see the capabilities guide. To update your integration settings, visit the integration dashboard.

### Body Params
- **parent**: `json` - A page parent. Either this or a `discussion_id` is required (not both)
- **discussion_id**: `string` - A UUID identifier for a discussion thread. Either this or a parent object is required (not both)
- **rich_text**: `json` (required) - A rich text object

### Headers
- **Notion-Version**: `string` (required) - The API version to use for this request. The latest version is 2022-06-28.

### Responses
- **200**: Success
- **403**: Forbidden 

## User Object

The User object represents a user in a Notion workspace. Users include full workspace members, guests, and integrations. You can find more information about members and guests in this guide.

📘 **Provisioning users and groups using SCIM**

The SCIM API is available for workspaces in Notion's Enterprise Plan. Learn more about using SCIM with Notion.

📘 **Setting up single sign-on (SSO) with Notion**

Single sign-on (SSO) can be configured for workspaces in Notion's Enterprise Plan. Learn more about SSO with Notion.

### Where User Objects Appear in the API
User objects appear in nearly all objects returned by the API, including:

- Block object under `created_by` and `last_edited_by`.
- Page object under `created_by` and `last_edited_by` and in people property items.
- Database object under `created_by` and `last_edited_by`.
- Rich text object, as user mentions.
- Property object when the property is a people property.

User objects will always contain `object` and `id` keys, as described below. The remaining properties may appear if the user is being rendered in a rich text or page property context, and the bot has the correct capabilities to access those properties. For more about capabilities, see the Capabilities guide and the Authorization guide.

### All Users
These fields are shared by all users, including people and bots. Fields marked with * are always present.

| Property   | Updatable   | Type                | Description                              | Example Value |
|------------|-------------|---------------------|------------------------------------------|---------------|
| object*    | Display-only| "user"             | Always "user"                           | "user"       |
| id*        | Display-only| string (UUID)       | Unique identifier for this user.         | "e79a0b74-3aba-4149-9f74-0bb5791a6ee6" |
| type       | Display-only| string (optional, enum) | Type of the user. Possible values are "person" and "bot". | "person"     |
| name       | Display-only| string (optional)   | User's name, as displayed in Notion.     | "Avocado Lovelace" |
| avatar_url | Display-only| string (optional)   | Chosen avatar image.                     | "https://secure.notion-static.com/e6a352a8-8381-44d0-a1dc-9ed80e62b53d.jpg" |

### People
User objects that represent people have the `type` property set to "person". These objects also have the following properties:

| Property       | Updatable   | Type   | Description                                      | Example Value |
|----------------|-------------|--------|--------------------------------------------------|---------------|
| person         | Display-only| object | Properties only present for non-bot users.       |               |
| person.email   | Display-only| string | Email address of person. This is only present if an integration has user capabilities that allow access to email addresses. | "avo@example.org" |

### Bots
A user object's `type` property is "bot" when the user object represents a bot. A bot user object has the following properties:

| Property       | Updatable   | Type   | Description                                      | Example Value |
|----------------|-------------|--------|--------------------------------------------------|---------------|
| bot            | Display-only| object | If you're using GET /v1/users/me or GET /v1/users/{{your_bot_id}}, then this field returns data about the bot, including owner, owner.type, and workspace_name. These properties are detailed below. | { "object": "user", "id": "9188c6a5-7381-452f-b3dc-d4865aa89bdf", "name": "Test Integration", "avatar_url": null, "type": "bot", "bot": { "owner": { "type": "workspace", "workspace": true }, "workspace_name": "Ada Lovelace's Notion" } } |
| owner          | Display-only| object | Information about who owns this bot.             | { "type": "workspace", "workspace": true } |
| owner.type     | Display-only| string enum | The type of owner, either "workspace" or "user". | "workspace" |
| workspace_name | Display-only| string enum | If the owner.type is "workspace", then workspace.name identifies the name of the workspace that owns the bot. If the owner.type is "user", then workspace.name is null. | "Ada Lovelace's Notion" |
| workspace_limits | Display-only| object | Information about the limits and restrictions that apply to the bot's workspace. | {"max_file_upload_size_in_bytes": 5242880} |
| workspace_limits.max_file_upload_size_in_bytes | Display-only| integer | The maximum allowable size of a file upload, in bytes. | 5242880 | 