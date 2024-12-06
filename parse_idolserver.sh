#!/bin/bash

# Variables
TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsIng1YyI6WyJNSUlFRmpDQ0F2NmdBd0lCQWdJVVZOajJRbU1JWnUzeGl0NUJ1RTlvRWdoVU5KUXdEUVlKS29aSWh2Y05BUUVMQlFBd2dZWXhDekFKQmdOVkJBWVRBbFZUTVJNd0VRWURWUVFJRXdwRFlXeHBabTl5Ym1saE1SSXdFQVlEVlFRSEV3bFFZV3h2SUVGc2RHOHhGVEFUQmdOVkJBb1RERVJ2WTJ0bGNpd2dTVzVqTGpFVU1CSUdBMVVFQ3hNTFJXNW5hVzVsWlhKcGJtY3hJVEFmQmdOVkJBTVRHRVJ2WTJ0bGNpd2dTVzVqTGlCRmJtY2dVbTl2ZENCRFFUQWVGdzB5TkRBeE1UWXdOak0yTURCYUZ3MHlOVEF4TVRVd05qTTJNREJhTUlHRk1Rc3dDUVlEVlFRR0V3SlZVekVUTUJFR0ExVUVDQk1LUTJGc2FXWnZjbTVwWVRFU01CQUdBMVVFQnhNSlVHRnNieUJCYkhSdk1SVXdFd1lEVlFRS0V3eEViMk5yWlhJc0lFbHVZeTR4RkRBU0JnTlZCQXNUQzBWdVoybHVaV1Z5YVc1bk1TQXdIZ1lEVlFRREV4ZEViMk5yWlhJc0lFbHVZeTRnUlc1bklFcFhWQ0JEUVRDQ0FTSXdEUVlKS29aSWh2Y05BUUVCQlFBRGdnRVBBRENDQVFvQ2dnRUJBTWI4eHR6ZDQ1UWdYekV0bWMxUEJsdWNGUnlzSUF4UUJCN3lSNjdJemdMd05IS24rbUdKTzV5alh6amtLZm5zWm1JRURnZFlraEpBbGNYYTdQa1BFaCtqcTRGNWNaaWtkTmFUQmM3alNkTFJzTVlVa3dwWTl4WUVqYitCYnVGUWVxa0R2RXNqbFJJTzRQK0FsRlhNMDhMYlpIZ3hFWUdkbFk3WFlhT1BLMmE1aUd2eVFRb09GVmZjZDd2ekhaREVBMHZqVmU1M0xLdjVMYmh6TzcxZHRxS0RwNEhnVWR5N1pENDFNN3I1bTd5eE1LeFNpQmJHZTFvem5Wamh1ck5GNHdGSml5bVU4YkhTV2tVTXVLQ3JTbEd4d1NCZFVZNDRyaEh2UW5zYmgzUFF2TUZTWTQ4REdoNFhUUldjSzFWUVlSTnA2ZWFXUVg1RUpJSXVJbjJQOVBzQ0F3RUFBYU43TUhrd0RnWURWUjBQQVFIL0JBUURBZ0dtTUJNR0ExVWRKUVFNTUFvR0NDc0dBUVVGQndNQk1CSUdBMVVkRXdFQi93UUlNQVlCQWY4Q0FRQXdIUVlEVlIwT0JCWUVGSnVRYXZTZHVScm5kRXhLTTAwV2Z2czh5T0RaTUI4R0ExVWRJd1FZTUJhQUZGSGVwRE9ZQ0Y5Qnc5dXNsY0RVUW5CalU3MS9NQTBHQ1NxR1NJYjNEUUVCQ3dVQUE0SUJBUUNDWW0xUVorUUZ1RVhkSWpiNkg4bXNyVFBRSlNnR0JpWDFXSC9QRnpqZlJGeHc3dTdDazBRb0FXZVNqV3JWQWtlVlZQN3J2REpwZ0ZoeUljdzNzMXRPVjN0OGp3cXJTUmc2R285dUd2OG9IWUlLTm9YaDErUFVDTG44b0JwYUJsOUxzSWtsL2FHMG9lY0hrcDVLYmtBNjN6eTFxSUVXNFAzWVJLSk9hSGoxYWFiOXJLc3lRSHF6SUl4TnlDRVVINTMwU1B4RUNMbE53YWVKTDVmNXIxUW5wSi9GM3Q5Vk8xZ0Y2RFpiNitPczdTV29ocGhWZlRCOERkL1VjSk1VOGp2YlF3MWRVREkwelNEdXo2aHNJbGdITk0yak04M0lOS1VqNjNaRDMwRG15ejQvczFFdGgyQmlKK2RHdnFpQkRzaWhaR0tyQnJzUzhWVkRBd3hDeDVRMyJdfQ.eyJhdWQiOiJodHRwczovL2h1Yi5kb2NrZXIuY29tIiwiZXhwIjoxNzE5NzU2Mzg2LCJodHRwczovL2h1Yi5kb2NrZXIuY29tIjp7ImVtYWlsIjoibWljcm9mb2N1cy5pZG9sLmRvY2tlckBtaWNyb2ZvY3VzLmNvbSIsInJvbGVzIjpbXSwic2Vzc2lvbl9pZCI6ImVjNTBlOGQzLWI1M2ItNDIxOC05MmU2LTk4OWU4MTU1ODEwNiIsInNvdXJjZSI6ImRvY2tlcl9wYXR8YWY0MDI3ZmMtNTQ5Ni00NWU0LTk4MzctZGU4MTUyZmZjMjU5IiwidXNlcm5hbWUiOiJtaWNyb2ZvY3VzaWRvbHJlYWRvbmx5IiwidXVpZCI6ImNhNGVmNzMwLWQzMmItNDc1My05YzczLTFmOWUwZjRmOWY2YyJ9LCJpYXQiOjE3MTcxNjQzODYsImlzcyI6Imh0dHBzOi8vYXBpLmRvY2tlci5jb20vIiwianRpIjoiZWM1MGU4ZDMtYjUzYi00MjE4LTkyZTYtOTg5ZTgxNTU4MTA2Iiwic2NvcGUiOiJyZXBvOnJlYWQiLCJzb3VyY2UiOnsiaWQiOiJhZjQwMjdmYy01NDk2LTQ1ZTQtOTgzNy1kZTgxNTJmZmMyNTkiLCJ0eXBlIjoicGF0In0sInN1YiI6ImNhNGVmNzMwZDMyYjQ3NTM5YzczMWY5ZTBmNGY5ZjZjIn0.ffWT2HvD9NFnZ_B5gss4hQMxPq4pI6G8XPuR0-29ly0Y148D2NZRoFzl9NYoesliYdb3fe4dFYnSMKt4liB1kFskh0F0CBTJ8N8-l7nel-AuWqxPEnf00bX5LjbhhsBr9z2HwvE4ko9nbRCO4E9mJbQjebAytt-HZavNcHfX0Xw-J5G_jWKsp3g-kkMfaA2NPN88pPlW7nZ_rrraUVU-MqOVIsBNfioK5n-nI0R4VTXfPecRvlNLRECKgqqKekNVFcdy0spHBoWA8KEyAi3CYN43zuDCUSiWiJT1-UwgS_hvTUx2djd9g2KgKSkpmmbWxL6i6JXaVXq3HqnvBClQ9A"
REPO="microfocusidolserver"  # or organization name

# Initialize an empty array to store repository and tag information
repo_tags=()

# Fetch all repositories for the given user/organization
url="https://hub.docker.com/v2/repositories/$REPO/"

while [ "$url" != "null" ]; do
  response=$(curl -s -H "Authorization: Bearer $TOKEN" "$url")
  repos=$(echo "$response" | jq -r '.results[].name')
  
  # For each repository, fetch all tags
  for repo in $repos; do
    tag_url="https://hub.docker.com/v2/repositories/$REPO/$repo/tags/"
    while [ "$tag_url" != "null" ]; do
      tag_response=$(curl -s -H "Authorization: Bearer $TOKEN" "$tag_url")
      tags=$(echo "$tag_response" | jq -r '.results[] | @base64')
      
      for tag in $tags; do
        decoded_tag=$(echo "$tag" | base64 --decode)
        repo_tags+=("$decoded_tag")
      done
      
      tag_url=$(echo "$tag_response" | jq -r '.next')
    done
  done
  
  url=$(echo "$response" | jq -r '.next')
done

# Save data to a JSON file for further processing with Python
echo "[" > repo_tags.json
printf "%s\n" "${repo_tags[@]}" | sed '$!s/$/,/' >> repo_tags.json
echo "]" >> repo_tags.json

