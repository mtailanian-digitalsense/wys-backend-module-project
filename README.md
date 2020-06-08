# API Endpoints for project module

Port: 8081

## Show single project by ID

**URL** : `/api/projects/{id}`

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

## Show single project by user ID

**URL** : `/api/projects/{user_id}`

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