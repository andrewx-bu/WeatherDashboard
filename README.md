# CS411 Final Group Project 
## Weather Dashboard Application
### Overview
* The Weather Dashboard is a web-based application designed to provide users with easy access to weather information.
* This application allows users to set favorite locations and quickly view current and forecasted weather and air pollution data for these locations.
* By offering userspecific customization, the Weather Dashboard aims to deliver a personalized weather tracking experience, making it easier for users to get the most relevant weather information based on their interests and needs.
* Database: MySQL

### Contributors
* Andrew Xin
* Jeremy Lau
* Sarah Lam
* Tong Zhang

## APi Call Route
### Route1: /get-coords
* **Request Type:** GET
* **Purpose:** Fetches the coordinates (latitude, longitude) of a city.
* **Request Body:**
  * city (str): The name of the city.
  * country_code (str, optional): The country code. Defaults to None.
* **Response Format:** JSON
  * Success Response Example:
    * Code: 200
    * Content: ``` { "message": "Found coordinates: {data[0]['lat']}, {data[0]['lon']}"} ```
* **Example Request:**
  ```
    {
      "city": "San Francisco",
      "country_code: "United States"
    }
  ```
* **Example Response:**
  ```
    {
      "message": "Found coordinates: {data[0]['lat']}, {data[0]['lon']}",
      "status": "200"
    }
  ```


## Favorite Management

### Route1: /add-favorite
* **Request Type:** POST
* **Purpose:** Add a favorite location for a user.
* **Request Body:**
  * user_id (int): The ID of the user.
  * location (str): The location to be added as a favorite.

* **Response Format:** JSON
  * Success Response Example:
    * Code: 200
    * Content: ``` { "message": "User {user_id} added new favorite location: {location}"} ```
* **Example Request:**
  ```
    {
      "user_id": 1
      "location": "San Francisco"
    }
  ```
* **Example Response:**
  ```
    {
      "message": "User 1 added new favorite location: San Francisco",
      "status": "200"
    }
  ```

### Route2: /update-favorite
* **Request Type:** PUT
* **Purpose:** Update a user's favorite location.
* **Request Body:**
  * user_id (int): The ID of the user.
  * old_location (str): The location to be replaced.
  * new_location (str): The new location to replace the old one.
* **Response Format:** JSON
  * Success Response Example:
    * Code: 200
    * Content: ``` { "message": "User {user_id} updated favorite location '{old_location}' to '{new_location}'"} ```
* **Example Request:**
  ```
    {
      "user_id": 1
      "old_location": "San Francisco"
      "new_location": "San Jose"
    }
  ```
* **Example Response:**
  ```
    {
      "message": "User 1 updated favorite location San Francisco to San Jose",
      "status": "200"
    }
  ```


### Route3: /remove-favorite
* **Request Type:** DELETE
* **Purpose:** Remove a favorite location for a user.
* **Request Body:**
  * user_id (int): The ID of the user.
  * location (str): The location to be added as a favorite.
* **Response Format:** JSON
  * Success Response Example:
    * Code: 200
    * Content: ``` { "message": "User {user_id} removed new favorite location: {location}"} ```
* **Example Request:**
  ```
    {
      "user_id": 1
      "location": "San Francisco"
    }
  ```

* **Example Response:**
  ```
    {
      "message": "User 1 added new favorite location: San Francisco",
      "status": "200"
    }
  ```


### Route4: 
* **Request Type:** 
* **Purpose:**
* **Request Body:**
  *
  *
* **Response Format:**
  *   
    * Code:
    * Content: { "message": ""}
* **Example Request:**
  ```
    {
      "user_id": 1
      "location": "San Francisco"
    }
  ```
* **Example Response:**
  ```
    {
      "message": "User 1 added new favorite location: San Francisco",
      "status": "200"
    }
  ```

### Route5: 
* **Request Type:** 
* **Purpose:**
* **Request Body:**
  *
  *
* **Response Format:**
  *   
    * Code:
    * Content: { "message": ""}
* **Example Request:**
  ```
    {
      "user_id": 1
      "location": "San Francisco"
    }
  ```
* **Example Response:**
  ```
    {
      "message": "User 1 added new favorite location: San Francisco",
      "status": "200"
    }
  ```
