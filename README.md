# Deckoviz AI API

AI services for the Deckoviz platform, enabling advanced features like image style transfer.

## Features

- Image Style Transfer

## API Endpoints

The Deckoviz AI API currently provides the following endpoint for style transfer:

### Style Transfer

*   **`POST /style-transfer/`**

    Applies a style to an input image.

    **Request:**

    *   `image`: An image file (multipart/form-data).
    *   `req` (`StyleTransferRequest`): A JSON object (sent as part of the form data or as a query parameter, depending on FastAPI's `Depends` behavior for model binding with `UploadFile`) containing the following fields:
        *   `height` (integer, optional): Desired height of the output image.
        *   `width` (integer, optional): Desired width of the output image.
        *   Other style-specific parameters (to be inferred or documented further if `StyleTransferRequest` schema is available).

    **Workflow:**

    1.  The uploaded image is encoded to base64.
    2.  An `ImageStyleTransferAgent` processes the request and the image to generate a positive prompt and potentially negative prompts (referred to as `processing_notes`).
    3.  The request is then sent to the Runware service (`civitai:101055@128078` model) for image generation.

    **Response:**

    *   On success: The generated styled image (likely as a base64 string or a direct image response).
    *   On failure: A JSON object with an "error" key detailing the issue.

    **Example Usage (conceptual):**

    A client would send a POST request with an image file and the `StyleTransferRequest` data.

    ```
    POST /style-transfer/
    Content-Type: multipart/form-data

    (image file data)
    (StyleTransferRequest data as form fields or query parameters)
    ```

## Getting Started

To get started with the Deckoviz AI API:

1.  **Prerequisites:**
    *   Docker installed and running.
2.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```
3.  **Environment Variables:**
    *   Copy the `.env.example` file to `.env` and update the variables as needed.
    ```bash
    cp .env.example .env
    ```
4.  **Build and run the Docker container:**
    ```bash
    docker-compose up --build
    ```
5.  The API will be accessible at `http://localhost:8000` (or the port configured in your environment).

## Technology Stack

- Python
- FastAPI
- Docker

## Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a Pull Request.

Please ensure your code adheres to the project's coding standards and includes tests where applicable.
