# MyRitu 🌸

MyRitu is a Streamlit application designed to help women track their menstrual cycles, understand hormonal changes, log symptoms, and gain insights into their reproductive health. It also features conceptual integrations with Hugging Face AI models for image analysis and personalized chat.

## ✨ Features

*   **Secure User Authentication:** Sign up, log in, and log out functionality to protect your personal data.
*   **Personalized Profile:** Store and update your average cycle length, period length, medical history, and more.
*   **Cycle Tracking Dashboard:** At-a-glance view of your current cycle phase, predicted next period, and fertile window.
*   **Interactive Calendar:** Visually track past and predicted periods, ovulation, fertile windows. Log new period dates and symptoms.
*   **Hormone Hub:** Educational section detailing key hormones (Estrogen, Progesterone, FSH, LH) and their roles during different cycle phases.
*   **Cycle Insights:** Visualizations of cycle length variations and symptom trends over time (e.g., mood, pain levels).
*   **Vision Model Integration (Conceptual):** Example of how to upload an image and send it to a Hugging Face vision model (e.g., for image captioning of a meal or skin concern).
*   **CycleChat (Conceptual):** An AI chat assistant that can answer general questions about menstrual health, "personalized" by providing your anonymized cycle summary as context to a Hugging Face Small Language Model (SLM).
*   **Data Persistence:** Your data is saved locally in an SQLite database.
*   **Themed Interface:** A user-friendly interface with a pink/feminine theme.

## 🛠️ Setup & Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://your-github-repo-url/femcycle-harmony.git
    cd femcycle-harmony
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **(Optional) Hugging Face API Token:**
    To use the Vision Model and CycleChat features, you'll need a Hugging Face API token.
    *   Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
    *   Create a new token (read access is usually sufficient for inference).
    *   You will be prompted to enter this token within the app when accessing these features.
    *   **Important:** Keep your API token secure and do not commit it to your repository. The app asks for it at runtime.

## 🚀 Running the Application

1.  Ensure your virtual environment is activated.
2.  Navigate to the project's root directory (`femcycle-harmony/`).
3.  Run the Streamlit application:
    ```bash
    streamlit run main.py
    ```
4.  The application will open in your default web browser.

## 🤖 Hugging Face API Integration Instructions

This application demonstrates how to connect to Hugging Face Inference Endpoints for AI-powered features.

**General Steps for Hugging Face Inference API:**

1.  **Obtain an API Token:** As mentioned in the setup, get your token from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
2.  **Choose a Model:** Browse [huggingface.co/models](https://huggingface.co/models) to find suitable models.
    *   For **Vision tasks** (e.g., image captioning, object detection), filter by task. Example: `Salesforce/blip-image-captioning-base`.
    *   For **Text Generation/Chat (SLM)**, filter by task (e.g., Text Generation, Conversational). Example: `mistralai/Mistral-7B-Instruct-v0.1` or `microsoft/DialoGPT-medium`.
3.  **Construct the API URL:** The URL is typically `https://api-inference.huggingface.co/models/YOUR_MODEL_ID`.
    *   Replace `YOUR_MODEL_ID` with the ID of the chosen model (e.g., `mistralai/Mistral-7B-Instruct-v0.1`).
4.  **Make the Request:**
    *   Use an HTTP POST request.
    *   Include an `Authorization` header: `Bearer YOUR_HF_API_TOKEN`.
    *   The request body (`data` or `json` parameter) depends on the model.
        *   **Vision Models:** Often expect raw image bytes in the `data` parameter.
        *   **Text Models:** Expect a JSON payload with an `inputs` field, and optionally a `parameters` field for things like `max_new_tokens`, `temperature`, etc. The structure of `inputs` can vary (e.g., a string, a dictionary for conversational history).
5.  **Process the Response:** The API usually returns a JSON response. The structure of this response also varies by model.

**In this App:**

*   **Vision Model (`tabs/tab_insights.py`):**
    *   The app uses a predefined model ID (e.g., `Salesforce/blip-image-captioning-base`). You can change this.
    *   It takes an uploaded image, sends its bytes to the API.
    *   Displays the `generated_text` from the response.
*   **Chat Model (SLM) (`tabs/tab_chat.py`):**
    *   Uses a predefined model ID (e.g., `mistralai/Mistral-7B-Instruct-v0.1`).
    *   Constructs a prompt including a summary of your profile and cycle history.
    *   Sends this prompt as `inputs` to the API.
    *   Displays the `generated_text` from the response.
    *   **Note:** This is *in-context learning*, not fine-tuning. The model is not retrained on your data; your data is simply provided as part of the prompt for context.

## ⚠️ Disclaimer

This application is for informational and educational purposes only. It is not intended to be a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.