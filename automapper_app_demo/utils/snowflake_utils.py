import snowflake.connector
from config import Config
import pandas as pd
from io import StringIO
import streamlit as st
import uuid
from datetime import datetime
from openpyxl import load_workbook
import io
import os
import tempfile

# Mock data storage
mock_db = {
    'files': {},
    'comments': [],
    'users': {
        'mapper': {'username': 'mapper', 'account_type': 'Mapper'},
        'partnership': {'username': 'partnership', 'account_type': 'Partnership'},
        'performance': {'username': 'performance', 'account_type': 'Performance'}
    },
    'submissions': {},
    'status_history': []
}

def get_snowflake_connection():
    """Mock connection function"""
    return None

def stage_file(df, filename, stage_name):
    """Mock staging a file"""
    file_id = f"{stage_name}/{filename}"
    mock_db['files'][file_id] = df
    return file_id

def read_from_stage(stage_path):
    """Mock reading from stage"""
    return mock_db['files'].get(stage_path, pd.DataFrame())

def get_reference_data():
    """Mock reference data"""
    return {
        'PLACEMENT_GROUP': ['Group A', 'Group B', 'Group C'],
        'PUBLISHER': ['Publisher 1', 'Publisher 2', 'Publisher 3'],
        'TACTIC': ['Tactic 1', 'Tactic 2', 'Tactic 3'],
        'AUDIENCE': ['Audience 1', 'Audience 2', 'Audience 3'],
        'AD_TYPE': ['Display', 'Video', 'Native']
    }

def get_campaign_names():
    """Mock campaign names"""
    return ['Campaign 1', 'Campaign 2', 'Campaign 3']

def get_file_data(submission_id):
    """Mock getting file data"""
    return mock_db['submissions'].get(submission_id, {}).get('data', None)

def update_file_status(submission_id, status, reviewer=None):
    """Update file submission status with better tracking"""
    conn = get_snowflake_connection()
    try:
        cur = conn.cursor()
        
        # Get current status first
        cur.execute(f"""
            SELECT STATUS, CURRENT_REVIEWER
            FROM {Config.TABLE_FILE_SUBMISSIONS}
            WHERE ID = %s
        """, (submission_id,))
        
        current_status = cur.fetchone()
        
        # Validate status transition
        valid_transitions = {
            'uploaded': 'mapper_complete',
            'mapper_complete': 'partnership_complete',
            'partnership_complete': 'performance_complete',
            'performance_complete': 'uploaded'  # Complete cycle
        }
        
        if current_status and current_status[0] not in valid_transitions:
            raise ValueError(f"Invalid status transition from {current_status[0]} to {status}")
            
        # Update status and reviewer
        if reviewer:
            cur.execute(f"""
                UPDATE {Config.TABLE_FILE_SUBMISSIONS}
                SET STATUS = %s, 
                    CURRENT_REVIEWER = %s,
                    UPDATED_AT = CURRENT_TIMESTAMP
                WHERE ID = %s
            """, (status, reviewer, submission_id))
        else:
            cur.execute(f"""
                UPDATE {Config.TABLE_FILE_SUBMISSIONS}
                SET STATUS = %s,
                    UPDATED_AT = CURRENT_TIMESTAMP
                WHERE ID = %s
            """, (status, submission_id))
            
        # Add status history record
        history_id = str(uuid.uuid4())
        cur.execute(f"""
            INSERT INTO {Config.TABLE_STATUS_HISTORY}
            (ID, SUBMISSION_ID, STATUS, CHANGED_BY, CHANGED_AT)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
        """, (history_id, submission_id, status, reviewer or 'SYSTEM'))
        
        conn.commit()
    finally:
        conn.close()

def submit_for_review(df, submission_id, account_type):
    """Submit file for review to next account type"""
    conn = get_snowflake_connection()
    try:
        cur = conn.cursor()
        
        # Use fully qualified names
        table_file_versions = f"{Config.SNOWFLAKE_DATABASE}.{Config.SNOWFLAKE_SCHEMA}.{Config.TABLE_FILE_VERSIONS}"
        
        # Get current status and original submitter
        cur.execute(f"""
            SELECT STATUS, SUBMITTED_BY 
            FROM {Config.TABLE_FILE_SUBMISSIONS} 
            WHERE ID = %s
        """, (submission_id,))
        result = cur.fetchone()
        current_status, original_submitter = result

        # Define workflow transitions
        status_map = {
            "Mapper": {
                "uploaded": "pending_partnership",
                "performance_complete": "pending_partnership"
            },
            "Partnership": {
                "pending_partnership": "pending_performance"
            },
            "Performance": {
                "pending_performance": "complete"
            }
        }
        
        new_status = status_map.get(account_type, {}).get(current_status)
        if not new_status:
            raise ValueError(f"Invalid status transition for {account_type} from {current_status}")
        
        # Get next reviewer based on status
        cur.execute(f"""
            SELECT USERNAME 
            FROM {Config.TABLE_USERS} 
            WHERE ACCOUNT_TYPE = %s 
            LIMIT 1
        """, (
            "Partnership" if new_status == "pending_partnership" else
            "Performance" if new_status == "pending_performance" else
            "Mapper" if new_status == "complete" else None,
        ))
        
        next_reviewer_result = cur.fetchone()
        next_reviewer = next_reviewer_result[0] if next_reviewer_result else None

        # For completed files, set reviewer back to original mapper
        if new_status == "complete":
            next_reviewer = original_submitter
        
        # Update submission status, submitted_by, and current_reviewer
        cur.execute(f"""
            UPDATE {Config.TABLE_FILE_SUBMISSIONS}
            SET STATUS = %s,
                CURRENT_REVIEWER = %s,
                SUBMITTED_BY = %s
            WHERE ID = %s
        """, (new_status, next_reviewer, st.session_state.username, submission_id))
        
        # Add status history record
        history_id = str(uuid.uuid4())
        cur.execute(f"""
            INSERT INTO {Config.TABLE_STATUS_HISTORY}
            (ID, SUBMISSION_ID, STATUS, CHANGED_BY, CHANGED_AT)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
        """, (history_id, submission_id, new_status, st.session_state.username))
        
        # Stage updated file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"version_{timestamp}.csv"
        stage_path = stage_file(df, filename, Config.PROCESSED_STAGE)
        
        # Create version record
        version_id = str(uuid.uuid4())
        cur.execute(f"""
            INSERT INTO {table_file_versions}
            (ID, SUBMISSION_ID, VERSION_NUMBER, STAGE_PATH, CREATED_BY, CREATED_AT)
            SELECT %s, %s, COALESCE(MAX(VERSION_NUMBER), 0) + 1, %s, %s, CURRENT_TIMESTAMP
            FROM {table_file_versions}
            WHERE SUBMISSION_ID = %s
        """, (version_id, submission_id, stage_path, st.session_state.username, submission_id))
        
        conn.commit()
        print(f"File submitted for {new_status} by {st.session_state.username} to reviewer {next_reviewer}")
        
    except Exception as e:
        conn.rollback()
        print(f"Error submitting for review: {str(e)}")
        raise
    finally:
        conn.close()

def archive_file(submission_id):
    """Archive the final processed file"""
    conn = get_snowflake_connection()
    try:
        # Get the current file data
        file_data = get_file_data(submission_id)
        if file_data is None:
            return False
            
        # Create archive filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_filename = f"archived_{submission_id}_{timestamp}.csv"
        
        # Upload to archive stage
        stage_path = stage_file(file_data, archive_filename, Config.ARCHIVE_STAGE)
        
        # Update submission record with archive path
        cur = conn.cursor()
        cur.execute(f"""
            UPDATE {Config.TABLE_FILE_SUBMISSIONS}
            SET ARCHIVE_PATH = %s,
                ARCHIVED_AT = CURRENT_TIMESTAMP
            WHERE ID = %s
        """, (stage_path, submission_id))
        
        conn.commit()
        return True
    finally:
        conn.close()

def convert_excel_to_csv(excel_file):
    """Convert Excel file to CSV DataFrame"""
    try:
        return pd.read_excel(excel_file)
    except Exception as e:
        st.error(f"Error reading Excel file: {str(e)}")
        return None

def convert_df_to_excel(df):
    """Convert DataFrame to Excel bytes"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def download_processed_file(submission_id):
    """Download processed file and archive it"""
    file_data = get_file_data(submission_id)
    if file_data is not None:
        # Archive the file
        archive_success = archive_file(submission_id)
        
        # Convert to Excel
        excel_data = convert_df_to_excel(file_data)
        
        if archive_success:
            st.success("File has been archived successfully!")
            
        st.download_button(
            label="Download Excel",
            data=excel_data,
            file_name=f"processed_{submission_id}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def get_comment_count(submission_id):
    """Get the total number of comments for a submission"""
    conn = get_snowflake_connection()
    try:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT COUNT(*)
            FROM {Config.TABLE_SUBMISSION_COMMENTS}
            WHERE SUBMISSION_ID = %s
        """, (submission_id,))
        return cur.fetchone()[0]
    finally:
        conn.close()

def download_completed_file(submission_id):
    """Download a completed file and mark it as archived"""
    file_data = get_file_data(submission_id)
    if file_data is not None:
        # Convert to Excel
        excel_data = convert_df_to_excel(file_data)
        
        # Get filename and mark as archived
        conn = get_snowflake_connection()
        try:
            cur = conn.cursor()
            
            # Get filename
            cur.execute(f"""
                SELECT FILENAME 
                FROM {Config.TABLE_FILE_SUBMISSIONS}
                WHERE ID = %s
            """, (submission_id,))
            result = cur.fetchone()
            filename = result[0] if result else f"completed_{submission_id}.xlsx"
            
            # Add 'completed' prefix if not already present
            if not filename.startswith('completed_'):
                filename = f"completed_{filename}"
            
            # Ensure xlsx extension
            if not filename.endswith('.xlsx'):
                filename = filename.rsplit('.', 1)[0] + '.xlsx'
            
            # Mark as archived
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_path = f"@{Config.ARCHIVE_STAGE}/archived_{filename}_{timestamp}"
            
            cur.execute(f"""
                UPDATE {Config.TABLE_FILE_SUBMISSIONS}
                SET ARCHIVED = TRUE,
                    ARCHIVED_AT = CURRENT_TIMESTAMP,
                    ARCHIVE_PATH = %s
                WHERE ID = %s
            """, (archive_path, submission_id))
            
            conn.commit()
            return excel_data, filename
        finally:
            conn.close()
    return None, None