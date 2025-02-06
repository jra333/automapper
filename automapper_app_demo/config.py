import os
#from dotenv import load_dotenv
import streamlit as st

#load_dotenv()

class Config:
    # Mock configuration
    SNOWFLAKE_USER = "mock_user"
    SNOWFLAKE_PASSWORD = "mock_password"
    SNOWFLAKE_ACCOUNT = "mock_account"
    SNOWFLAKE_DATABASE = "mock_database"
    SNOWFLAKE_SCHEMA = "mock_schema"
    SNOWFLAKE_WAREHOUSE = "mock_warehouse"
    
    # Stage names
    UPLOAD_STAGE = 'AUTOMAPPER_UPLOAD_STAGE'
    PROCESSED_STAGE = 'AUTOMAPPER_PROCESSED_STAGE'
    ARCHIVE_STAGE = 'AUTOMAPPER_ARCHIVE_STAGE'
    
    # Table names
    TABLE_FILE_SUBMISSIONS = 'AUTOMAPPER_FILE_SUBMISSIONS'
    TABLE_SUBMISSION_COMMENTS = 'AUTOMAPPER_SUBMISSION_COMMENTS'
    TABLE_STATUS_HISTORY = 'AUTOMAPPER_STATUS_HISTORY'
    TABLE_USERS = 'AUTOMAPPER_USERS'
    TABLE_FILE_VERSIONS = 'AUTOMAPPER_FILE_VERSIONS'
    
    # App configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    @staticmethod
    def get_full_account():
        return "mock_account"
