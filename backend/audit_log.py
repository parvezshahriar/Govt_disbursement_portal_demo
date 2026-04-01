#!/usr/bin/env python
"""
Audit Log System with Database Triggers
Tracks all changes to critical tables (user, product_1, batch_upload)
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, func, event, text
from sqlalchemy.dialects.postgresql import JSON
from database import Base, engine
from datetime import datetime
import json


class AuditLog(Base):
    """
    Audit log table to store all changes to critical tables
    """
    __tablename__ = 'audit_log'
    
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String, index=True)  # Name of the table that was modified
    operation = Column(String, index=True)  # INSERT, UPDATE, DELETE
    record_id = Column(String, index=True)  # Primary key of the modified record
    old_values = Column(JSON, nullable=True)  # Previous values (NULL for INSERT)
    new_values = Column(JSON, nullable=True)  # New values (NULL for DELETE)
    changed_columns = Column(JSON, nullable=True)  # List of columns that changed
    employee_id = Column(String, nullable=True, index=True)  # Employee who made the change
    user_id = Column(Integer, nullable=True, index=True)  # User who made the change
    timestamp = Column(DateTime, default=func.now(), index=True)  # When the change occurred
    description = Column(Text, nullable=True)  # Additional context


def create_audit_triggers():
    """
    Create triggers for automatic audit logging on critical tables
    Uses PostgreSQL session variables to track employee_id
    """
    
    try:
        with engine.begin() as connection:
            # Create the audit function with session variable support
            audit_function_sql = text("""
            CREATE OR REPLACE FUNCTION audit_trigger_function()
            RETURNS TRIGGER AS $$
            DECLARE
                old_values JSON;
                new_values JSON;
                changed_cols TEXT[];
                col_name TEXT;
                emp_id TEXT;
                usr_id INTEGER;
                record_id_value TEXT;
            BEGIN
                -- Get employee_id and user_id from session variables (set by application)
                -- If not set, will be NULL
                BEGIN
                    emp_id := current_setting('app.current_employee_id', true);
                EXCEPTION WHEN OTHERS THEN
                    emp_id := NULL;
                END;
                
                BEGIN
                    usr_id := CAST(current_setting('app.current_user_id', true) AS INTEGER);
                EXCEPTION WHEN OTHERS THEN
                    usr_id := NULL;
                END;
                
                -- Determine record_id based on table
                IF TG_TABLE_NAME = 'product_1' THEN
                    -- For product_1 table, use EFTREFNUMBER as record_id
                    IF TG_OP = 'DELETE' THEN
                        -- Use OLD for DELETE
                        BEGIN
                            record_id_value := CAST(OLD."EFTREFNUMBER" AS TEXT);
                        EXCEPTION WHEN OTHERS THEN
                            record_id_value := CAST(OLD.eftrefnumber AS TEXT);
                        END;
                    ELSE
                        BEGIN
                            record_id_value := CAST(NEW."EFTREFNUMBER" AS TEXT);
                        EXCEPTION WHEN OTHERS THEN
                            record_id_value := CAST(NEW.eftrefnumber AS TEXT);
                        END;
                    END IF;
                ELSIF TG_TABLE_NAME = 'client_info' THEN
                    -- For client_info table, use BENEFICIARY_ID as record_id
                    IF TG_OP = 'DELETE' THEN
                        BEGIN
                            record_id_value := CAST(OLD."BENEFICIARY_ID" AS TEXT);
                        EXCEPTION WHEN OTHERS THEN
                            record_id_value := CAST(OLD.beneficiary_id AS TEXT);
                        END;
                    ELSE
                        BEGIN
                            record_id_value := CAST(NEW."BENEFICIARY_ID" AS TEXT);
                        EXCEPTION WHEN OTHERS THEN
                            record_id_value := CAST(NEW.beneficiary_id AS TEXT);
                        END;
                    END IF;
                ELSIF TG_TABLE_NAME = 'batch_upload' THEN
                    -- For batch_upload table, use id as record_id
                    IF TG_OP = 'DELETE' THEN
                        record_id_value := CAST(OLD.id AS TEXT);
                    ELSE
                        record_id_value := CAST(NEW.id AS TEXT);
                    END IF;
                ELSIF TG_TABLE_NAME = 'user_info' THEN
                    -- For user_info table, use id as record_id
                    IF TG_OP = 'DELETE' THEN
                        record_id_value := CAST(OLD.id AS TEXT);
                    ELSE
                        record_id_value := CAST(NEW.id AS TEXT);
                    END IF;
                ELSE
                    -- Default: try to use id, fallback to first column
                    IF TG_OP = 'DELETE' THEN
                        record_id_value := CAST(OLD.id AS TEXT);
                    ELSE
                        record_id_value := CAST(NEW.id AS TEXT);
                    END IF;
                END IF;
                
                -- For INSERT operations
                IF TG_OP = 'INSERT' THEN
                    new_values := row_to_json(NEW);
                    INSERT INTO audit_log (
                        table_name, 
                        operation, 
                        record_id, 
                        new_values,
                        employee_id,
                        user_id,
                        timestamp
                    ) VALUES (
                        TG_TABLE_NAME,
                        TG_OP,
                        record_id_value,
                        new_values,
                        emp_id,
                        usr_id,
                        NOW()
                    );
                    RETURN NEW;
                
                -- For UPDATE operations
                ELSIF TG_OP = 'UPDATE' THEN
                    old_values := row_to_json(OLD);
                    new_values := row_to_json(NEW);
                    
                    -- Find which columns changed
                    changed_cols := ARRAY[]::TEXT[];
                    FOR col_name IN
                        SELECT key FROM json_object_keys(new_values) AS key
                    LOOP
                        IF old_values->>col_name IS DISTINCT FROM new_values->>col_name THEN
                            changed_cols := array_append(changed_cols, col_name);
                        END IF;
                    END LOOP;
                    
                    INSERT INTO audit_log (
                        table_name, 
                        operation, 
                        record_id, 
                        old_values, 
                        new_values, 
                        changed_columns,
                        employee_id,
                        user_id,
                        timestamp
                    ) VALUES (
                        TG_TABLE_NAME,
                        TG_OP,
                        record_id_value,
                        old_values,
                        new_values,
                        to_json(changed_cols),
                        emp_id,
                        usr_id,
                        NOW()
                    );
                    RETURN NEW;
                
                -- For DELETE operations
                ELSIF TG_OP = 'DELETE' THEN
                    old_values := row_to_json(OLD);
                    INSERT INTO audit_log (
                        table_name, 
                        operation, 
                        record_id, 
                        old_values,
                        employee_id,
                        user_id,
                        timestamp
                    ) VALUES (
                        TG_TABLE_NAME,
                        TG_OP,
                        record_id_value,
                        old_values,
                        emp_id,
                        usr_id,
                        NOW()
                    );
                    RETURN OLD;
                END IF;
                
                RETURN NULL;
            END;
            $$ LANGUAGE plpgsql;
            """)
            
            connection.execute(audit_function_sql)
            print("[AUDIT_LOG] ✓ Audit trigger function created successfully")
            
            # Create triggers for each table
            triggers = [
                text("""
                    DROP TRIGGER IF EXISTS user_audit_trigger ON "user";
                    CREATE TRIGGER user_audit_trigger
                    AFTER INSERT OR UPDATE OR DELETE ON "user"
                    FOR EACH ROW
                    EXECUTE FUNCTION audit_trigger_function();
                """),
                text("""
                    DROP TRIGGER IF EXISTS product_audit_trigger ON product_1;
                    CREATE TRIGGER product_audit_trigger
                    AFTER INSERT OR UPDATE OR DELETE ON product_1
                    FOR EACH ROW
                    EXECUTE FUNCTION audit_trigger_function();
                """),
                text("""
                    DROP TRIGGER IF EXISTS batch_upload_audit_trigger ON batch_upload;
                    CREATE TRIGGER batch_upload_audit_trigger
                    AFTER INSERT OR UPDATE OR DELETE ON batch_upload
                    FOR EACH ROW
                    EXECUTE FUNCTION audit_trigger_function();
                """),
                text("""
                    DROP TRIGGER IF EXISTS user_info_audit_trigger ON user_info;
                    CREATE TRIGGER user_info_audit_trigger
                    AFTER INSERT OR UPDATE OR DELETE ON user_info
                    FOR EACH ROW
                    EXECUTE FUNCTION audit_trigger_function();
                """),
                text("""
                    DROP TRIGGER IF EXISTS client_info_audit_trigger ON client_info;
                    CREATE TRIGGER client_info_audit_trigger
                    AFTER INSERT OR UPDATE OR DELETE ON client_info
                    FOR EACH ROW
                    EXECUTE FUNCTION audit_trigger_function();
                """),
            ]
            
            for trigger_sql in triggers:
                connection.execute(trigger_sql)
            
            print("[AUDIT_LOG] ✓ All audit triggers created successfully")
            return True
            
    except Exception as e:
        print(f"[AUDIT_LOG] ✗ Error creating audit triggers: {str(e)}")
        return False


def setup_audit_system():
    """
    Complete setup: create table and triggers
    """
    print("[AUDIT_LOG] Starting audit log system setup...")
    
    try:
        # Create audit log table
        Base.metadata.create_all(bind=engine)
        print("[AUDIT_LOG] ✓ Audit log table created")
        
        # Create triggers
        create_audit_triggers()
        print("[AUDIT_LOG] ✓ Audit system fully initialized")
        return True
        
    except Exception as e:
        print(f"[AUDIT_LOG] ✗ Setup failed: {str(e)}")
        return False


if __name__ == "__main__":
    setup_audit_system()
