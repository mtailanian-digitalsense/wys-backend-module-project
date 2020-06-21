# API Endpoints for project module

Port: 8081

## Show single project by ID

**URL** : `/api/projects/{id}`

**URL Parameters** : `{id}=[integer]` where `{id}` is the ID of the Project on the server.

**Method** : `GET`

**Auth required** : YES

### Success Response

**Code** : `200 OK`

**Content example**

For a project with ID 123 in the local database where that project has saved a name and has an associated m2, a user and a location.

```json
{
    "id": 123,
    "name": "Project name",
    "m2_gen_id": 1234,
    "user_id": 321,
    "location_id": 12345
}
```

### Error Responses

**Condition** :  If Account does not exist with `id` of provided parameter.

**Code** : `404 NOT FOUND`

**Content** : `{}`

## Show all projects by single user ID

**URL** : `/api/projects/user/{user_id}/projects`

**URL Parameters** : `{user_id}=[integer]` where `{user_id}` is the ID of the User on the server.

**Method** : `GET`

**Auth required** : YES

### Success Response

**Code** : `200 OK`

**Content example**

```json
{
    "data": 
    [
        {
            "name": "Project1",
            "user_id": 1,
            "m2_gen_id":1,
            "location_id":1
        },
        {
            "name": "Project2",
            "user_id": 1,
            "m2_gen_id":2,
            "location_id":2
        },
        ...
    ]
}
```

### Error Responses

**Condition** :  If User does not exist with `id` of provided parameter.

**Code** : `404 NOT FOUND`

**Content** : `{}`

### Or

**Condition** : If an error occurs with the database.

**Code** : `500 Internal Server Error`

**Content** : `{exception_message}`

## Create a new project

**URL** : `/api/projects`

**Method** : `POST`

**Auth required** : YES

**Data constraints**

Provide the `name` and owner user `ID of Project` to be created. The `location ID` and the `generated M2 ID` will be 
created when the User finishes the Project creation process, so they may not be in the request data.

```json
{
    "name": "[unicode 120 chars max]",
    "m2_gen_id": "[integer]",
    "location_id" : "[integer]"
}
```

### Success Response

**Code** : `201 CREATED`

**Content example**

```json
{
    "name": "Project",
    "user_id": 1,
    "m2_gen_id":1,
    "location_id":1
}
```

### Error Responses

**Condition** : If Project already exists for User.

**Code** : `303 SEE OTHER`

**Headers** : `Location: /api/projects/{project_id}`

**Content** : `{}`

### Or

**Condition** : If an error occurs with the database.

**Code** : `500 Internal Server Error`

**Content** : `{exception_message}`

## Update an existing project

Update the Account of the Authenticated User if and only if they are Owner.

**URL** : `/api/projects/{project_id}`

**URL Parameters** : `{id}=[integer]` where `{id}` is the ID of the Project on the server.

**Method** : `PUT`

**Auth required** : YES

**Data constraints**

The projects are not transferable, so the user id is not modifiable. Data example:

```json
{
    "name": "[unicode 64 chars max]",
    "m2_gen_id": "[integer]",
    "location_id" : "[integer]"
}
```

### Success Responses

**Condition** : Update can be performed either fully or partially by the Owner
of the Account.

**Code** : `200 OK`

**Content example** : For the example above, when the 'name' is updated and posted to `/api/projects/123/`...

```json
{
    "id": 123,
    "name": "New project name",
    "user_id": 1,
    "m2_gen_id":1,
    "location_id":1
}
```

### Error Response

**Condition** : Project does not exist at URL

**Code** : `404 NOT FOUND`

**Content** : `{}`

### Or

**Condition** : Authorized User is not owner of Project at URL.

**Code** : `403 FORBIDDEN`

**Content** : `{}`

## Delete an existing Project

Delete the Project of the Authenticated User if they are Owner.

**URL** : `/api/projects/{project_id}`

**URL Parameters** : `{id}=[integer]` where `{id}` is the ID of the Project on the server.

**Method** : `DELETE`

**Auth required** : YES

**Data** : `{}`

### Success Response

**Condition** : If the Project exists.

**Code** : `200 OK`

**Content** : `{"result": 'Project deleted'}`

### Error Responses

**Condition** : If there was no Project available to delete.

**Code** : `404 NOT FOUND`

**Content** : `{}`

### Or

**Condition** : Authorized User is not owner of Project at URL.

**Code** : `403 FORBIDDEN`

**Content** : `{}`
