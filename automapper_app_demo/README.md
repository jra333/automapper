# AUTOMAPPER DEMO VERSION

[Automapper](https://github.com/jra333/automapper/tree/main/automapper_app_demo) is a Streamlit-based web application designed to automate the processing, review, and archival of file submissions using AI-powered predictions. It integrates with Snowflake for data storage, staging, and user authentication, while leveraging a fine-tuned T5 model from Hugging Face Transformers for generating business-critical mappings.

**SOME CODE AND PROCESSES HAVE BEEN REDACTED/ALTERED FOR PRIVACY AND WILL NOT BE UPDATED.**

**Finetuned model not included in repo.**

---

## Features

- **File Upload & Processing**  
  Upload CSV or Excel files. The application cleans and processes the file data, applies AI predictions for mapping fields (e.g., Placement Group, Publisher, Tactic, Audience, Ad Type), and generates an updated dataset.

- **Interactive Data Review & Edit**  
  Use an intuitive data editor interface (powered by Streamlit) to review and apply changes to processed data. Users can search, filter, sort, and download the final output.

- **Snowflake Integration**  
  Set up and interact with Snowflake stages and tables for file submissions, comments, and status histories. SQL scripts initialize the required database schema and stages.

- **User Authentication**  
  A mock authentication module simulates user login and role-based access (Mapper, Partnership, Performance).

- **Archival & Version Control**  
  After processing, files are staged and archived. A versioning system is in place to track multiple versions of file submissions.

- **AI Prediction using T5 Model**  
  The core file processing relies on a T5 model to create mapping predictions. The model input is built from campaign details and placement names, and its output is parsed and merged into the submission data.

---

## Architecture & File Structure

- **app.py**  
  The main entry point for the application. It initializes the Streamlit session state and launches the user interface.

- **config.py**  
  Stores configuration settings such as Snowflake credentials, stage and table names, and application parameters (e.g., max file size).

- **SQL Scripts**
  - **init.sql**: Sets up Snowflake stages, tables (users, file submissions, file comments, file versions, status history), indexes, and constraints.

- **utils/**
  - **snowflake_utils.py**: Provides helper functions for Snowflake connections, staging files, updating submission statuses, and archival operations.
  - **interface_utils.py**: Contains UI components for processing, editing, and displaying data, including data validation and interactive editing using Streamlit.
  - **file_processor.py**: Implements file processing logic using a T5 model for conditional generation. It prepares model input, processes predictions, and merges AI-generated fields into the DataFrame.
  - **auth_utils.py**: Implements a mock authentication system for login, registration, and user data retrieval.

- **model_outputs/** & **model_archives/**  
  Directories containing model files and configuration files required to run the T5 model.

- **.gitattributes & .gitignore**  
  Standard files for managing large files (e.g., model tensors) with Git LFS and ignoring sensitive or temporary files.

- **requirements.txt**  
  Lists all required dependencies such as Streamlit, Pandas, Torch, Transformers, and Openpyxl.

---

## Usage

1. **Upload Files**  
   From the UI, upload a CSV or Excel file. The file is processed to remove extraneous text and fill missing placements from lookup files (if any).

2. **Process File with AI Predictions**  
   The T5 model processes the file input to predict fields such as Placement Group, Publisher, and others. View a preview of both the original and processed data.

3. **Interactive Editing**  
   Review and modify the processed data using the interactive data editor. Search, filter, and sort the data as needed.

4. **Apply and Download Changes**  
   Once confirmed, apply the changes. Download the updated data, and the file will be staged and archived accordingly.

5. **User Authentication**  
   (Mocked) Use role-based access to submit and review files. The user session is initialized automatically for demonstration.
