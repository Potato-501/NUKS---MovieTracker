# Movie-kite API Documentation

This project exposes a small Flask API for managing movies in a SQL database and notes in MongoDB.

## Overview

- Base movie routes: `/movies`
- Base review routes: `/api/reviews`
- CORS is enabled for the whole app
- No authentication is implemented
- The OMDb search endpoint requires `API_KEY` in the environment

## Movie Data Model

The SQL `Movie` record contains:

- `id`: integer, primary key
- `title`: string, required, unique
- `status`: string, default `watchlist`
- `year`: string
- `poster_url`: string
- `rating`: integer, default `0`

## Endpoints

### GET `/`

Simple health-style homepage that confirms the app is running.

#### Response

Returns a small HTML page with a link to the movies section.

### GET `/movies/search?q=<query>`

Searches OMDb and returns the upstream response.

#### Query parameters

- `q` required search text

#### Responses

- `200 OK` with the OMDb JSON payload
- `400 Bad Request` if `q` is missing
- Upstream OMDb error status if the external request fails

#### Example

```http
GET /movies/search?q=Inception
```

#### Example response

```json
{
	"Search": [
		{
			"Title": "Inception",
			"Year": "2010",
			"imdbID": "tt1375666",
			"Type": "movie",
			"Poster": "https://..."
		}
	],
	"totalResults": "1",
	"Response": "True"
}
```

### POST `/movies/add`

Adds a movie to the SQL database.

#### Request body

```json
{
	"title": "Inception",
	"year": "2010",
	"status": "watchlist"
}
```

#### Field notes

- `title` is required
- `status` is required
- `year` is optional but expected by the frontend

#### Responses

- `201 Created` when the movie is saved
- `400 Bad Request` if `title` is missing
- `400 Bad Request` if the title already exists in the database
- `500 Internal Server Error` for unexpected failures

#### Example response

```json
{
	"message": "Added movie Inception to watchlist"
}
```

### GET `/movies/`

Returns all movies stored in the SQL database.

#### Response

```json
[
	{
		"id": 1,
		"title": "Inception",
		"status": "watchlist",
		"year": "2010",
		"poster_url": null,
		"rating": 0
	}
]
```

### PUT `/movies/<movie_id>/status`

Updates a movie status.

#### Request body

```json
{
	"status": "library"
}
```

#### Responses

- `200 OK` when the status is updated
- `404 Not Found` if the movie does not exist

#### Example response

```json
{
	"message": "Status updated!"
}
```

### PATCH `/movies/<movie_id>/rating`

Updates a movie rating.

#### Request body

```json
{
	"rating": 4
}
```

#### Responses

- `200 OK` when the rating is updated
- `404 Not Found` if the movie does not exist

#### Example response

```json
{
	"message": "Rating updated"
}
```

### DELETE `/movies/<movie_id>`

Deletes a movie from the SQL database.

#### Responses

- `200 OK` when the movie is deleted
- `404 Not Found` if the movie does not exist

#### Example response

```json
{
	"message": "Movie deleted!"
}
```

## Review Notes API

Notes are stored in MongoDB under the `movie_notes` collection. Each note is associated with a SQL movie ID.

### GET `/api/reviews/<movie_id>`

Fetches the note for a specific movie.

#### Responses

- `200 OK` with a note object if one exists
- `200 OK` with an empty note if no note exists yet

#### Example response with a note

```json
{
	"note": "Great soundtrack and pacing.",
	"last_updated": "2026-05-09T12:34:56.789Z"
}
```

#### Example response without a note

```json
{
	"note": ""
}
```

### POST `/api/reviews/<movie_id>`

Creates or updates a note for a movie.

#### Request body

```json
{
	"note": "Great soundtrack and pacing."
}
```

#### Responses

- `201 Created` when the note is stored

#### Example response

```json
{
	"message": "Note synced to MongoDB"
}
```

### DELETE `/api/reviews/<movie_id>`

Deletes the note for a movie without removing the SQL movie record.

#### Responses

- `200 OK` when the note is removed

#### Example response

```json
{
	"message": "Note deleted"
}
```

## Frontend Usage Summary

The frontend currently calls:

- `GET /movies/search?q=...` for OMDb search
- `POST /movies/add` to save a movie
- `GET /movies/` to list all movies
- `PUT /movies/<id>/status` to move a movie into the library
- `PATCH /movies/<id>/rating` to rate a movie
- `GET /api/reviews/<id>` to load notes
- `POST /api/reviews/<id>` to save notes

## Environment Notes

- SQLite database: `movies.db`
- MongoDB URI: `mongodb://localhost:27017/movieDB`
- OMDb API key must be available as `API_KEY`
