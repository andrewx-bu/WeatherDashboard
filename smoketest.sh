#!/bin/bash

BASE_URL="http://127.0.0.1:5001"
BASE_URL_API="$BASE_URL/api"

ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done

# Fetch user ID by username
get_user_id() {
  local username=$1
  echo "Fetching user ID for username: $username"
  response=$(curl -s -X GET "$BASE_URL/get-all-users")
  user_id=$(echo "$response" | jq -r --arg USERNAME "$username" '.users[] | select(.username == $USERNAME) | .id')

  if [ -z "$user_id" ] || [ "$user_id" == "null" ]; then
    echo "Failed to fetch user ID for username: $username"
    echo "$response"
    exit 1
  fi
  echo "User ID for $username is $user_id."
}

###############################################
#
# Health Checks
#
###############################################

check_health() {
  echo "Checking health status..."
  response=$(curl -s -X GET "$BASE_URL_API/health")
  if echo "$response" | grep -q '"status":"healthy"'; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    echo "$response"
    exit 1
  fi
}

check_db() {
  echo "Checking database connection..."
  response=$(curl -s -X GET "$BASE_URL_API/db-check")
  if echo "$response" | grep -q '"database_status":"healthy"'; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    echo "$response"
    exit 1
  fi
}

###############################################
#
# User Account Management
#
###############################################

create_user() {
  local username=$1
  local password=$2

  echo "Creating user: $username"
  response=$(curl -s -X POST "$BASE_URL/create-account" -H "Content-Type: application/json" \
    -d "{\"username\": \"$username\", \"password\": \"$password\"}")
  
  if echo "$response" | grep -q "success"; then
    echo "User created successfully."
  else
    echo "Failed to create user."
    echo "$response"
    exit 1
  fi
}

login_user() {
  local username=$1
  local password=$2

  echo "Logging in user: $username"
  response=$(curl -s -X GET "$BASE_URL/login" -H "Content-Type: application/json" \
    -d "{\"username\": \"$username\", \"password\": \"$password\"}")

  if echo "$response" | grep -q "success"; then
    echo "Login successful."
  else
    echo "Failed to log in."
    echo "$response"
    exit 1
  fi
}

update_password() {
  local username=$1
  local old_password=$2
  local new_password=$3

  echo "Updating password for user: $username"
  response=$(curl -s -X PUT "$BASE_URL/update-password" -H "Content-Type: application/json" \
    -d "{\"username\": \"$username\", \"old_password\": \"$old_password\", \"new_password\": \"$new_password\"}")

  if echo "$response" | grep -q "success"; then
    echo "Password updated successfully."
  else
    echo "Failed to update password."
    echo "$response"
    exit 1
  fi
}

get_all_users() {
  echo "Retrieving all users..."
  response=$(curl -s -X GET "$BASE_URL/get-all-users")

  if echo "$response" | grep -q '"users"'; then
    echo "Users retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Users JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve users."
    echo "$response"
    exit 1
  fi
}

delete_user() {
  local username=$1
  local password=$2

  echo "Deleting user: $username"
  response=$(curl -s -X DELETE "$BASE_URL/delete-account" -H "Content-Type: application/json" \
    -d "{\"username\": \"$username\", \"password\": \"$password\"}")
  
  if echo "$response" | grep -q "success"; then
    echo "User deleted successfully."
  else
    echo "Failed to delete user."
    echo "$response"
    exit 1
  fi
}

###############################################
#
# Favorites Management
#
###############################################

add_favorite() {
  local user_id=$1
  local location=$2

  echo "Adding favorite location: $location for user: $user_id"
  response=$(curl -s -X POST "$BASE_URL_API/add-favorite" -H "Content-Type: application/json" \
    -d "{\"user_id\": \"$user_id\", \"location\": \"$location\"}")

  if echo "$response" | grep -q "success"; then
    echo "Favorite location added successfully."
  else
    echo "Failed to add favorite location."
    echo "$response"
    exit 1
  fi
}

remove_favorite() {
  local user_id="$1"
  local location="$2"
  echo "Removing favorite location '$location' for user '$user_id'..."
  response=$(curl -s -X DELETE "$BASE_URL_API/remove-favorite" -H "Content-Type: application/json" \
    -d "{\"user_id\": \"$user_id\", \"location\": \"$location\"}")

  if echo "$response" | grep -q "success"; then
    echo "Favorite location removed successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to remove favorite location."
    echo "$response"
    exit 1
  fi
}

update_favorite() {
  local user_id="$1"
  local old_location="$2"
  local new_location="$3"
  echo "Updating favorite location from '$old_location' to '$new_location' for user '$user_id'..."
  response=$(curl -s -X PUT "$BASE_URL_API/update-favorite" -H "Content-Type: application/json" \
    -d "{\"user_id\": \"$user_id\", \"old_location\": \"$old_location\", \"new_location\": \"$new_location\"}")

  if echo "$response" | grep -q "success"; then
    echo "Favorite location updated successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to update favorite location."
    echo "$response"
    exit 1
  fi
}

clear_favorites() {
  local user_id="$1"
  echo "Clearing all favorites for user '$user_id'..."
  response=$(curl -s -X DELETE "$BASE_URL_API/clear-favorites" -H "Content-Type: application/json" \
    -d "{\"user_id\": \"$user_id\"}")

  if echo "$response" | grep -q "success"; then
    echo "All favorites cleared successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to clear all favorites."
    echo "$response"
    exit 1
  fi
}

get_favorites() {
  local user_id=$1

  echo "Fetching favorite locations for user: $user_id"
  response=$(curl -s -G "$BASE_URL_API/get-favorites" --data-urlencode "user_id=$user_id")

  if echo "$response" | grep -q "favorites"; then
    echo "Favorites retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Favorites JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve favorites."
    echo "$response"
    exit 1
  fi
}

###############################################
#
# API Route Tests
#
###############################################

test_coords() {
  local city=$1
  echo "Testing coordinates retrieval for city: $city"
  
  response=$(curl -s -G "$BASE_URL_API/coords" --data-urlencode "city=$city")
  
  if echo "$response" | grep -q '"coordinates"'; then
    echo "Successfully fetched coordinates for city: $city"
  else
    echo "Failed to fetch coordinates for city: $city"
    echo "$response"
    exit 1
  fi
}

test_forecast() {
  local city=$1
  echo "Testing weather forecast for city: $city"
  
  response=$(curl -s -G "$BASE_URL_API/forecast" --data-urlencode "city=$city")
  
  if echo "$response" | grep -q '"weather"'; then
    echo "Successfully fetched weather forecast for city: $city"
  else
    echo "Failed to fetch weather forecast for city: $city"
    echo "$response"
    exit 1
  fi
}

test_air_pollution_forecast() {
  local city=$1
  echo "Testing air pollution forecast for city: $city"
  
  response=$(curl -s -G "$BASE_URL_API/air-pollution-forecast" --data-urlencode "city=$city")
  
  if echo "$response" | grep -q '"aqi"'; then
    echo "Successfully fetched air pollution forecast for city: $city"
  else
    echo "Failed to fetch air pollution forecast for city: $city"
    # echo "$response"
    exit 1
  fi
}

test_current_weather() {
  local city=$1
  echo "Testing current weather for city: $city"
  
  response=$(curl -s -G "$BASE_URL_API/weather" --data-urlencode "city=$city")
  
  if echo "$response" | grep -q '"weather"'; then
    echo "Successfully fetched current weather for city: $city"
  else
    echo "Failed to fetch current weather for city: $city"
    echo "$response"
    exit 1
  fi
}

test_air_pollution() {
  local city=$1
  echo "Testing air pollution data for city: $city"
  
  response=$(curl -s -G "$BASE_URL_API/air-pollution" --data-urlencode "city=$city")
  
  if echo "$response" | grep -q '"aqi"'; then
    echo "Successfully fetched air pollution data for city: $city"
  else
    echo "Failed to fetch air pollution data for city: $city"
    # echo "$response"
    exit 1
  fi
}

###############################################
#
# Main Execution
#
###############################################

echo "Starting smoke tests..."

# Health Checks
check_health
check_db

# User Account Management
USERNAME="testuser0"
PASSWORD="testpassword123"
NEW_PASSWORD="newpassword123"

create_user "$USERNAME" "$PASSWORD"
login_user "$USERNAME" "$PASSWORD"
update_password "$USERNAME" "$PASSWORD" "$NEW_PASSWORD"
get_all_users

get_user_id "$USERNAME"

# Favorites Management
LOCATION1="New York"
LOCATION2="San Francisco"
LOCATION3="Boston"

add_favorite "$user_id" "$LOCATION1"
add_favorite "$user_id" "$LOCATION2"
get_favorites "$user_id"
update_favorite "$user_id" "$LOCATION1" "$LOCATION3"
get_favorites "$user_id"
remove_favorite "$user_id" "$LOCATION2"
get_favorites "$user_id"
clear_favorites "$user_id"

# Cleanup
delete_user "$USERNAME" "$NEW_PASSWORD"

# API Routes Tests
CITY1="New York"
CITY2="Los Angeles"

test_coords "$CITY1"
test_forecast "$CITY1"
test_air_pollution_forecast "$CITY1"
test_current_weather "$CITY1"
test_air_pollution "$CITY1"

test_coords "$CITY2"
test_forecast "$CITY2"
test_air_pollution_forecast "$CITY2"
test_current_weather "$CITY2"
test_air_pollution "$CITY2"

echo "All smoke tests completed successfully!"