#!/usr/bin/env python
"""
Audit Log Query Utilities
Provides functions to view and analyze audit logs
"""

from database import Session
from dbmodel import AuditLog, User, UserInfo
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


class AuditLogManager:
    """Manager class for audit log operations"""
    
    @staticmethod
    def get_recent_changes(table_name: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        Get recent changes across all or a specific table
        
        Args:
            table_name: Optional table name to filter by
            limit: Number of records to return
            
        Returns:
            List of audit log entries
        """
        session = Session()
        try:
            query = session.query(AuditLog).order_by(desc(AuditLog.timestamp))
            
            if table_name:
                query = query.filter(AuditLog.table_name == table_name)
            
            logs = query.limit(limit).all()
            
            result = []
            for log in logs:
                # Get username and last_name if user_id exists (who performed the action)
                username = None
                last_name = None
                if log.user_id:
                    user = session.query(User).filter(User.id == log.user_id).first()
                    username = user.username if user else None
                    if user:
                        user_info = session.query(UserInfo).filter(UserInfo.user_id == log.user_id).first()
                        last_name = user_info.last_name if user_info else None
                
                # Fallback to employee_id if user was deleted
                display_username = username or log.employee_id or f"User #{log.user_id}" or '-'
                
                # Extract deleted user info for DELETE operations on user table
                deleted_user_info = None
                if log.table_name == 'user' and log.operation == 'DELETE' and log.old_values:
                    try:
                        old_vals = log.old_values if isinstance(log.old_values, dict) else json.loads(log.old_values)
                        deleted_user_info = {
                            'deleted_user_id': old_vals.get('id', log.record_id),
                            'deleted_username': old_vals.get('username', 'Unknown'),
                            'deleted_email': old_vals.get('email', 'N/A')
                        }
                    except:
                        deleted_user_info = None
                
                result.append({
                    'id': log.id,
                    'table': log.table_name,
                    'operation': log.operation,
                    'record_id': log.record_id,
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                    'old_values': log.old_values,
                    'new_values': log.new_values,
                    'changed_columns': log.changed_columns,
                    'user_id': log.user_id or log.employee_id or '-',  # Numeric user ID or employee_id
                    'username': display_username,  # Username, employee_id, or user ID as fallback
                    'last_name': last_name or log.employee_id or '-',  # Last name, employee_id, or dash
                    'deleted_user_info': deleted_user_info  # Info about deleted user (if applicable)
                })
            return result
        finally:
            session.close()
    
    @staticmethod
    def get_changes_for_record(table_name: str, record_id: str) -> List[Dict]:
        """
        Get all changes for a specific record
        
        Args:
            table_name: Name of the table
            record_id: Primary key of the record
            
        Returns:
            List of changes for that record, ordered by time
        """
        session = Session()
        try:
            logs = session.query(AuditLog).filter(
                and_(
                    AuditLog.table_name == table_name,
                    AuditLog.record_id == record_id
                )
            ).order_by(AuditLog.timestamp).all()
            
            result = []
            for log in logs:
                username = None
                if log.user_id:
                    user = session.query(User).filter(User.id == log.user_id).first()
                    username = user.username if user else None
                
                result.append({
                    'operation': log.operation,
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                    'old_values': log.old_values,
                    'new_values': log.new_values,
                    'changed_columns': log.changed_columns,
                    'user_id': log.user_id or log.employee_id or '-',
                    'username': username or '-'
                })
            return result
        finally:
            session.close()
    
    @staticmethod
    def get_changes_by_employee(employee_id: str, limit: int = 50) -> List[Dict]:
        """
        Get all changes made by a specific employee
        
        Args:
            employee_id: ID of the employee
            limit: Number of records to return
            
        Returns:
            List of changes made by the employee
        """
        session = Session()
        try:
            logs = session.query(AuditLog).filter(
                AuditLog.employee_id == employee_id
            ).order_by(desc(AuditLog.timestamp)).limit(limit).all()
            
            result = []
            for log in logs:
                username = None
                if log.user_id:
                    user = session.query(User).filter(User.id == log.user_id).first()
                    username = user.username if user else None
                
                result.append({
                    'table': log.table_name,
                    'operation': log.operation,
                    'record_id': log.record_id,
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                    'changed_columns': log.changed_columns,
                    'user_id': log.user_id or log.employee_id or '-',
                    'username': username or '-'
                })
            return result
        finally:
            session.close()
    
    @staticmethod
    def get_changes_in_period(start_date: datetime, end_date: datetime, 
                              table_name: Optional[str] = None) -> List[Dict]:
        """
        Get all changes within a date range
        
        Args:
            start_date: Start of the period
            end_date: End of the period
            table_name: Optional table filter
            
        Returns:
            List of changes in the period
        """
        session = Session()
        try:
            query = session.query(AuditLog).filter(
                and_(
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date
                )
            )
            
            if table_name:
                query = query.filter(AuditLog.table_name == table_name)
            
            logs = query.order_by(AuditLog.timestamp).all()
            
            result = []
            for log in logs:
                username = None
                if log.user_id:
                    user = session.query(User).filter(User.id == log.user_id).first()
                    username = user.username if user else None
                
                result.append({
                    'table': log.table_name,
                    'operation': log.operation,
                    'record_id': log.record_id,
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                    'changed_columns': log.changed_columns,
                    'user_id': log.user_id or log.employee_id or '-',
                    'username': username or '-'
                })
            return result
        finally:
            session.close()
    
    @staticmethod
    def get_operation_summary(days: int = 7) -> Dict:
        """
        Get summary of operations in the last N days
        
        Args:
            days: Number of days to look back
            
        Returns:
            Summary of operations by table and type
        """
        session = Session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            logs = session.query(AuditLog).filter(
                AuditLog.timestamp >= cutoff_date
            ).all()
            
            summary = {}
            for log in logs:
                table = log.table_name
                operation = log.operation
                
                if table not in summary:
                    summary[table] = {'INSERT': 0, 'UPDATE': 0, 'DELETE': 0}
                
                summary[table][operation] += 1
            
            return summary
        finally:
            session.close()
    
    @staticmethod
    def print_recent_changes(table_name: Optional[str] = None, limit: int = 10):
        """Print recent changes in a readable format"""
        logs = AuditLogManager.get_recent_changes(table_name, limit)
        
        print("\n" + "="*80)
        print("RECENT AUDIT LOG ENTRIES")
        print("="*80)
        
        for log in logs:
            print(f"\n[{log['timestamp']}] {log['operation']} on {log['table']}")
            print(f"  Record ID: {log['record_id']}")
            if log['changed_columns']:
                print(f"  Changed Columns: {', '.join(log['changed_columns'])}")
        
        print("\n" + "="*80 + "\n")
    
    @staticmethod
    def print_record_history(table_name: str, record_id: str):
        """Print complete change history for a specific record"""
        logs = AuditLogManager.get_changes_for_record(table_name, record_id)
        
        print("\n" + "="*80)
        print(f"CHANGE HISTORY: {table_name} (ID: {record_id})")
        print("="*80)
        
        for log in logs:
            print(f"\n[{log['timestamp']}] {log['operation']}")
            if log['operation'] == 'INSERT':
                print("  New Record Created:")
                if log['new_values']:
                    for key, value in json.loads(log['new_values']).items():
                        print(f"    {key}: {value}")
            elif log['operation'] == 'UPDATE':
                print("  Changes:")
                if log['changed_columns']:
                    for col in json.loads(log['changed_columns']):
                        old = log['old_values'][col] if log['old_values'] else 'N/A'
                        new = log['new_values'][col] if log['new_values'] else 'N/A'
                        print(f"    {col}: {old} → {new}")
            elif log['operation'] == 'DELETE':
                print("  Record Deleted")
                if log['old_values']:
                    for key, value in json.loads(log['old_values']).items():
                        print(f"    {key}: {value}")
        
        print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    # Example usage
    print("Audit Log Manager initialized")
    print("Use AuditLogManager class to query audit logs")
