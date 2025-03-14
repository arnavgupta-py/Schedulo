"""
Chatbot logic for Schedulo.
Handles natural language processing and database interaction.
"""

import os
import re
import logging
import threading
import sqlite3
from typing import Dict, List, Any, Union, Optional
import json

# Conditional import for LangChain (to allow the app to start even if not installed)
try:
    from langchain_groq import ChatGroq
    from langchain.schema import SystemMessage, HumanMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    
from database import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
GROQ_MODEL = "llama3-70b-8192"

# Thread local storage for database connections
thread_local = threading.local()

def get_db_path_from_uri(uri):
    """
    Extract actual file path from SQLite URI.
    
    Args:
        uri: SQLite URI
        
    Returns:
        str: File path for the SQLite database
    """
    if uri.startswith('sqlite:///'):
        # Remove sqlite:/// prefix
        relative_path = uri[10:]
        
        # For absolute paths (four slashes)
        if uri.startswith('sqlite:////'):
            return relative_path
            
        # For relative paths (three slashes)
        # Make it absolute based on the application root directory
        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.abspath(os.path.join(app_root, relative_path))
    
    return None  # Not a SQLite URI

class ScheduloDB:
    """Thread-safe database operations for Schedulo."""
    
    def __init__(self, db_uri: str = None):
        """
        Initialize the database connection.
        
        Args:
            db_uri: Database URI (defaults to environment variable)
        """
        # Get database URI from app config or environment
        self.db_uri = db_uri or os.getenv('DATABASE_URL')
        if not self.db_uri:
            raise ValueError("Database URI is not set!")

        # Extract the file path from the SQLAlchemy URI
        self.db_path = get_db_path_from_uri(self.db_uri)
        if not self.db_path:
            raise ValueError(f"Invalid SQLite URI: {self.db_uri}")
            
        logger.info(f"Actual database file path: {self.db_path}")
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize schema
        try:
            self._get_connection()
            self.tables = self._get_tables()
            self.schema = self._get_schema()
            self._close_connection()
            logger.info(f"Successfully loaded schema with {len(self.tables)} tables")
        except Exception as e:
            logger.error(f"Error initializing database schema: {e}")
            self.tables = []
            self.schema = {}
    
    def _get_connection(self):
        """
        Get a thread-local SQLite connection.
        
        Returns:
            tuple: (connection, cursor)
        """
        if not hasattr(thread_local, 'conn'):
            try:
                thread_local.conn = sqlite3.connect(self.db_path)
                thread_local.conn.row_factory = sqlite3.Row
                thread_local.cursor = thread_local.conn.cursor()
                logger.debug(f"Created new database connection to {self.db_path}")
            except Exception as e:
                logger.error(f"Error creating database connection: {e}")
                raise
        return thread_local.conn, thread_local.cursor
    
    def _close_connection(self):
        """Close the thread-local connection."""
        if hasattr(thread_local, 'conn'):
            try:
                thread_local.conn.close()
                delattr(thread_local, 'conn')
                delattr(thread_local, 'cursor')
                logger.debug("Closed database connection")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
    
    def _get_tables(self) -> List[str]:
        """
        Get all tables in the database.
        
        Returns:
            list: Table names
        """
        conn, cursor = self._get_connection()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            return [row['name'] for row in cursor.fetchall()]
        finally:
            self._close_connection()
    
    def _get_schema(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get the database schema.
        
        Returns:
            dict: Schema information for all tables
        """
        schema = {}
        conn, cursor = self._get_connection()
        
        try:
            for table in self.tables:
                try:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = []
                    for col in cursor.fetchall():
                        columns.append({
                            'name': col['name'],
                            'type': col['type'],
                            'pk': bool(col['pk']),
                            'notnull': bool(col['notnull']),
                            'default': col['dflt_value']
                        })
                    schema[table] = columns
                except Exception as e:
                    logger.error(f"Error getting schema for table {table}: {e}")
        finally:
            self._close_connection()
        
        return schema
    
    def get_schema_str(self) -> str:
        """
        Get the schema as a formatted string.
        
        Returns:
            str: Formatted schema string
        """
        lines = []
        for table, columns in self.schema.items():
            lines.append(f"Table: {table}")
            for col in columns:
                pk_str = "PRIMARY KEY" if col['pk'] else ""
                null_str = "NOT NULL" if col['notnull'] else ""
                default_str = f"DEFAULT {col['default']}" if col['default'] else ""
                lines.append(f"  - {col['name']} ({col['type']}) {pk_str} {null_str} {default_str}".strip())
            lines.append("")
        
        return "\n".join(lines)
    
    def execute_query(self, query: str, params: tuple = ()) -> Union[List[Dict], int]:
        """
        Execute a SQL query (thread-safe).
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Union[List[Dict], int]: Query results or number of affected rows
            
        Raises:
            Exception: If query execution fails
        """
        try:
            conn, cursor = self._get_connection()
            cursor.execute(query, params)
            
            if query.strip().lower().startswith("select"):
                result = [dict(row) for row in cursor.fetchall()]
                return result
            else:
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error executing query: {e}\nQuery: {query}\nParams: {params}")
            raise
        finally:
            self._close_connection()
    
    def execute_script(self, script: str) -> str:
        """
        Execute a SQL script containing multiple statements (thread-safe).
        
        Args:
            script: SQL script to execute
            
        Returns:
            str: Success message
            
        Raises:
            Exception: If script execution fails
        """
        try:
            conn, cursor = self._get_connection()
            cursor.executescript(script)
            conn.commit()
            return f"Script executed successfully ({script.count(';')} statements)"
        except Exception as e:
            logger.error(f"Error executing script: {e}\nScript: {script}")
            raise
        finally:
            self._close_connection()
    
    def query_with_results(self, query: str, params: tuple = ()) -> str:
        """
        Execute a query and format the results as a markdown string.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            str: Markdown-formatted results
        """
        try:
            results = self.execute_query(query, params)
            
            if isinstance(results, int):
                return f"Query executed successfully. {results} rows affected."
            
            if not results:
                return "Query executed successfully, but no rows were returned."
            
            # Format results as a markdown table
            if results:
                headers = list(results[0].keys())
                markdown_table = ["| " + " | ".join(headers) + " |"]
                markdown_table.append("| " + " | ".join(["---"] * len(headers)) + " |")
                
                for row in results:
                    formatted_row = [str(row.get(header, '')) for header in headers]
                    markdown_table.append("| " + " | ".join(formatted_row) + " |")
                
                return "\n".join(markdown_table)
            else:
                return "No results found."
        except Exception as e:
            return f"Error: {str(e)}"

class ScheduloAgent:
    """AI-powered agent for Schedulo."""
    
    def __init__(self, db_uri: str = None, groq_api_key: str = None):
        """
        Initialize the Schedulo Agent.
        
        Args:
            db_uri: Database URI
            groq_api_key: Groq API key
            
        Raises:
            ValueError: If GROQ API key is not provided
        """
        try:
            self.db = ScheduloDB(db_uri)
            self.setup_llm(groq_api_key)
            self.conversation_history = {}  # Indexed by user_id
        except Exception as e:
            logger.error(f"Error initializing ScheduloAgent: {e}")
            raise
    
    def setup_llm(self, groq_api_key: str = None):
        """
        Set up the LLM for the agent.
        
        Args:
            groq_api_key: Groq API key (defaults to environment variable)
            
        Raises:
            ValueError: If GROQ API key is not found
        """
        if not LANGCHAIN_AVAILABLE:
            logger.error("LangChain is not installed. NLP capabilities will be limited.")
            self.llm = None
            return
            
        # Get GROQ API key from environment
        api_key = groq_api_key or os.environ.get("GROQ_API_KEY")
        
        if not api_key:
            logger.error("GROQ API key not found")
            raise ValueError("GROQ API key is required")
        
        # Initialize LLM
        try:
            self.llm = ChatGroq(
                groq_api_key=api_key,
                model_name=GROQ_MODEL,
                temperature=0,
                max_tokens=2048
            )
            logger.info("ChatGroq initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ChatGroq: {e}")
            raise
    
    def get_system_message(self):
        """
        Get the system message with current schema information.
        
        Returns:
            str: System message for the LLM
        """
        return f"""You are a SQL expert assistant for Schedulo, a university timetable generation system. 
                    You help users query and update the database using natural language.

                    DATABASE SCHEMA:
                    {self.db.get_schema_str()}

                    YOUR CAPABILITIES:
                    1. Convert natural language queries into SQL
                    2. Execute SQL queries
                    3. Insert, update, and delete data
                    4. Explain complex database operations

                    YOUR RULES:
                    1. ALWAYS generate complete, executable SQL 
                    2. NEVER just describe or explain SQL without also generating it
                    3. Ensure SQL is valid for SQLite (date functions, syntax, etc.)
                    4. For INSERT/UPDATE operations, provide the SQL first followed by execution
                    5. Check for existing records before performing INSERT operations
                    6. ALWAYS provide a concise, clear response
                    7. ALWAYS use the correct table and column names from the schema

                    COMMON TABLES AND COLUMNS:
                    - Table: subjects (NOT Subjects)
                    - official_code, unofficial_code, name, required_hours_per_week (NOT Duration or Credits)
                    
                    - Table: teachers 
                    - id, name, workload

                    - Table: academic_years
                    - symbol, is_current
                    
                    - Table: divisions
                    - id, year_id, name
                    
                    - Table: batches
                    - id, division_id, name

                    - Table: venues
                    - id, name, type, capacity
                    
                    - Table: events
                    - id, subject_id, teacher_id, venue_id, division_id, batch_id, day_of_week, start_time, end_time, is_recurring

                    YOUR WORKFLOW:
                    1. Analyze the user's request
                    2. Generate SQL directly without excessive reasoning
                    3. If appropriate, execute the SQL
                    4. Return the results in a clear format
                    5. For complex operations, break down into steps

                    IMPORTANT: You have direct database access. You MUST generate SQL to accomplish the user's request AND execute it yourself.
                    """
    
    def get_or_create_conversation(self, user_id):
        """
        Get or create conversation history for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            list: Conversation history
        """
        if not LANGCHAIN_AVAILABLE:
            return []
            
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        return self.conversation_history[user_id]
    
    def process_query(self, query: str, user_id: int) -> str:
        """
        Process a natural language query for a specific user.
        
        Args:
            query: User query
            user_id: User ID
            
        Returns:
            str: Response to the query
        """
        if not LANGCHAIN_AVAILABLE or self.llm is None:
            return "Sorry, the chatbot service is currently unavailable. Please check if LangChain and Groq API key are properly configured."
            
        # Get the conversation history for this user
        conversation = self.get_or_create_conversation(user_id)
        
        # Add user message to conversation history
        conversation.append(HumanMessage(content=query))
        
        # Create messages for LLM with schema context
        messages = [
            SystemMessage(content=self.get_system_message()),
            *conversation
        ]
        
        try:
            # Get AI response
            response = self.llm.invoke(messages)
            
            # Check response for SQL queries
            content = response.content
            conversation.append(AIMessage(content=content))
            
            # Extract SQL queries from the response
            sql_queries = self._extract_sql_queries(content)
            
            # Execute SQL queries if found
            if sql_queries:
                results = []
                for sql in sql_queries:
                    # Skip empty queries
                    if not sql.strip():
                        continue
                    
                    try:
                        if ";" in sql.strip() and not sql.strip().lower().startswith("select"):
                            # Multiple statements
                            result = self.db.execute_script(sql)
                            results.append(result)
                        else:
                            # Single query
                            result = self.db.query_with_results(sql)
                            results.append(result)
                    except Exception as e:
                        results.append(f"Error executing SQL: {str(e)}")
                
                # Create a new response that includes both the original AI response and the SQL execution results
                result_text = "\n\n".join(results)
                new_response = f"{content}\n\n[SQL EXECUTION RESULTS]\n{result_text}"
                
                # Update the last AI message in conversation history with the execution results
                conversation[-1] = AIMessage(content=new_response)
                
                return new_response
            
            # If no SQL queries found, just return the response
            return content
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _extract_sql_queries(self, text: str) -> List[str]:
        """
        Extract SQL queries from text.
        
        Args:
            text: Text to extract SQL queries from
            
        Returns:
            list: Extracted SQL queries
        """
        # Extract SQL queries enclosed in triple backticks
        sql_pattern = r"```sql\s*(.*?)\s*```"
        queries = re.findall(sql_pattern, text, re.DOTALL)
        
        # If no queries found with sql tag, try without tag
        if not queries:
            sql_pattern = r"```\s*(.*?)\s*```"
            queries = re.findall(sql_pattern, text, re.DOTALL)
        
        # Clean up queries
        queries = [q.strip() for q in queries]
        
        # If still no queries, look for SQL keywords
        if not queries:
            lines = text.split('\n')
            current_query = []
            all_queries = []
            
            sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP']
            in_query = False
            
            for line in lines:
                stripped = line.strip()
                
                # Check if line starts with SQL keyword
                if any(stripped.upper().startswith(keyword) for keyword in sql_keywords):
                    if in_query:
                        # End previous query
                        all_queries.append('\n'.join(current_query))
                        current_query = []
                    
                    in_query = True
                    current_query.append(stripped)
                elif in_query and (stripped.endswith(';') or not stripped):
                    # End of query
                    current_query.append(stripped)
                    all_queries.append('\n'.join(current_query))
                    current_query = []
                    in_query = False
                elif in_query:
                    # Continue current query
                    current_query.append(stripped)
            
            # Add last query if any
            if current_query:
                all_queries.append('\n'.join(current_query))
            
            queries = all_queries
        
        return queries
    
    def reset_conversation(self, user_id: int):
        """
        Reset the conversation history for a user.
        
        Args:
            user_id: User ID
        """
        if user_id in self.conversation_history:
            self.conversation_history[user_id] = []