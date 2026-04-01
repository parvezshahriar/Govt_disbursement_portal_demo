#!/usr/bin/env python
"""
Audit Context Manager
Provides a context manager to set employee_id for audit logging
"""

from database import Session
from sqlalchemy import text
from contextlib import contextmanager


@contextmanager
def audit_context(session, employee_id: str = None, user_id: int = None):
    """
    Context manager to set employee_id and user_id for audit logging
    
    Args:
        session: SQLAlchemy session
        employee_id: Employee ID to associate with changes
        user_id: User ID to associate with changes
    """
    try:
        # Set the session variables
        if employee_id:
            session.execute(text(f"SET app.current_employee_id = '{employee_id}'"))
        if user_id:
            session.execute(text(f"SET app.current_user_id = '{user_id}'"))
        session.commit()
        yield
    finally:
        # Reset the session variables
        try:
            if employee_id:
                session.execute(text("RESET app.current_employee_id"))
            if user_id:
                session.execute(text("RESET app.current_user_id"))
            session.commit()
        except:
            pass
        session.close()


def set_audit_employee(session, employee_id: str = None, user_id: int = None):
    """
    Directly set the employee_id and user_id for audit logging
    
    Args:
        session: SQLAlchemy session
        employee_id: Employee ID to associate with changes
        user_id: User ID to associate with changes
    """
    try:
        if employee_id:
            session.execute(text(f"SET app.current_employee_id = '{employee_id}'"))
        if user_id:
            session.execute(text(f"SET app.current_user_id = '{user_id}'"))
        session.commit()
    except Exception as e:
        print(f"[AUDIT] Error setting audit session variables: {str(e)}")


def reset_audit_employee(session):
    """
    Reset the audit session variables
    
    Args:
        session: SQLAlchemy session
    """
    try:
        session.execute(text("RESET app.current_employee_id"))
        session.execute(text("RESET app.current_user_id"))
        session.commit()
    except:
        pass
