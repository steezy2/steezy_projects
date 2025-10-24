# Go MongoDB Connection Example

A basic Go application demonstrating how to connect to a MongoDB database.

## Prerequisites

- [Go](https://golang.org/doc/install) (version 1.21 or newer)
- [MongoDB](https://www.mongodb.com/try/download/community) (running locally or on a cloud service like MongoDB Atlas)

## Getting Started

1.  **Clone the repository:**

    ```sh
    git clone <your-repo-url>
    cd <your-repo-directory>
    ```

2.  **Set up environment variables:**

    Copy the example `.env` file and update it with your MongoDB connection string.

    ```sh
    cp .env.example .env
    ```

3.  **Install dependencies:**

    ```sh
    go mod tidy
    ```

4.  **Run the application:**

    ```sh
    go run main.go
    ```

    If the connection is successful, you will see the message:
    `Successfully connected and pinged MongoDB!`