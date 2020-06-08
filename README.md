# API Endpoints for project module

Port: 8081

## Show single project by ID

**URL** : `/api/projects/{id}`

**URL Parameters** : `{id}=[integer]` where `{id}` is the ID of the Project on the server.

**Method** : `GET`

**Auth required** : -

**Permissions required** : -

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

**URL** : `/api/user/{user_id}/projects`

**URL Parameters** : `{user_id}=[integer]` where `{user_id}` is the ID of the User on the server.

**Method** : `GET`

**Auth required** : -

**Permissions required** : -

### Success Response

**Code** : `200 OK`

**Content example**

```json
{

}
```

### Error Responses

**Condition** :  If User does not exist with `id` of provided parameter.

**Code** : `404 NOT FOUND`

**Content** : `{}`

## Create a new project

**URL** : `/api/projects`

**Method** : `POST`

**Auth required** : -

**Permissions required** : -

### Success Response

**Code** : `201 CREATED`

**Content example**

```json
{
    "name": "Project",
    "user_id": "1",
    "m2_gen_id":1,
    "location_id":1,
}
```

### Error Responses

**Condition** : If Project already exists for User.

**Code** : `303 SEE OTHER`

**Headers** : `Location: /api/projects/{project_id}`

**Content** : `{}`
